from contextlib import asynccontextmanager

from adaptors import QueryableAdaptor
from data_generation.index import OpenSearchIndex, generate_index


class QueryContext():
    def __init__(self, adaptor: QueryableAdaptor, index: OpenSearchIndex):
        self.adaptor = adaptor
        self.index = index

    
    async def run_query(self, query: str):
        return await self.adaptor.run_query(query)


@asynccontextmanager
async def context(adaptor: QueryableAdaptor):
    index = generate_index()
    await adaptor.create_index(index)
    try:
        yield QueryContext(adaptor, index)
    finally:
        await adaptor.cleanup_index(index)
