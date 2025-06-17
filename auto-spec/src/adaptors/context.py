import asyncio
from contextlib import asynccontextmanager
from collections import defaultdict

from adaptors import QueryableAdaptor
from data_generation.index import OpenSearchIndex, generate_index


# Enables a per-adaptor limit on the number of contexts that can exist at once. This helps avoid
# runaway resource usage by trying to run thousand of tests at once.
_context_pool = defaultdict(lambda: asyncio.Semaphore(128))


class QueryContext:
    def __init__(self, adaptor: QueryableAdaptor, index: OpenSearchIndex):
        self.adaptor = adaptor
        self.index = index

    async def run_query(self, query: str):
        return await self.adaptor.run_query(query)


@asynccontextmanager
async def context(adaptor: QueryableAdaptor):
    async with _context_pool[id(adaptor)]:
        index = generate_index()
        await adaptor.create_index(index)
        try:
            yield QueryContext(adaptor, index)
        finally:
            await adaptor.cleanup_index(index)
