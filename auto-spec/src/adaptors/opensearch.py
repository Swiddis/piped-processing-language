from contextlib import asynccontextmanager
import json
from opensearchpy import AsyncOpenSearch
from multiprocessing import Lock

from adaptors import QueryableAdaptor
from data_generation.index import OpenSearchIndex
import asyncio


class RequestPool:
    """
    OpenSearch doesn't do well with thousands of requests being made at once. When that happens,
    it's prone to time out. For our purposes, we're going to keep a pool to limit concurrent
    requests.
    """

    def __init__(self, capacity: int = 32):
        self.sem = asyncio.Semaphore(capacity)

    @asynccontextmanager
    async def acquire(self):
        await self.sem.acquire()
        try:
            yield
        finally:
            await self.sem.release()


class OpenSearchAdaptor(QueryableAdaptor):
    def __init__(self, client: AsyncOpenSearch):
        self.client = client
        self.pool = RequestPool()

    async def _init_index_mapping(self, index: OpenSearchIndex):
        async with self.pool.acquire():
            result = await self.client.indices.create(
                index.name,
                index.mapping(),
                params={"timeout": 120},
            )
        assert not result.get("errors", None), f"failed to create index: {result}"

    async def _populate_index(self, index: OpenSearchIndex):
        header = json.dumps({"index": {"_index": index.name}})
        bulk_req = "\n".join(header + "\n" + json.dumps(doc) for doc in index.documents)
        async with self.pool.acquire():
            response = await self.client.bulk(
                bulk_req, params={"refresh": "wait_for", "timeout": 120}
            )
        assert not response["errors"], f"failed to insert to index: {response}"

    async def create_index(self, index: OpenSearchIndex):
        await self._init_index_mapping(index)
        await self._populate_index(index)

    async def cleanup_index(self, index: OpenSearchIndex):
        async with self.pool.acquire():
            await self.client.indices.delete(index.name, params={"timeout": 120})

    async def run_query(self, query: str):
        async with self.pool.acquire():
            return await self.client.http.post(
                "/_plugins/_ppl", body={"query": query}, params={"timeout": 120}
            )

    async def close(self):
        await self.client.close()
