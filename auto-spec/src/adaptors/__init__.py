import typing
from abc import ABC, abstractmethod

from data_generation.index import OpenSearchIndex


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
    async def run_query(self, query: str) -> dict[str, typing.Any]:
        # TODO define a format that works for both spark and SQL plugin
        # We probably can't just rely on JDBC everywhere
        pass

    @abstractmethod
    async def close(self):
        """
        Final teardown operations for the Adaptor before program shutdown.
        """
        pass
