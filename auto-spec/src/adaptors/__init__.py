from abc import ABC, abstractmethod

from model import OpenSearchIndex, QueryResponse


class QueryableAdaptor(ABC):
    """
    Used to support testing queries on multiple runtimes
    """

    @abstractmethod
    async def create_index(self, index: OpenSearchIndex):
        pass

    @abstractmethod
    async def cleanup_index(self, index: OpenSearchIndex):
        pass

    @abstractmethod
    async def run_query(self, query: str) -> QueryResponse:
        pass

    @abstractmethod
    async def close(self):
        """
        Final teardown operations for the Adaptor before program shutdown.
        """
        pass
