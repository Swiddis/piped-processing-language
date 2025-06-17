from opensearchpy import AsyncOpenSearch
from dataclasses import dataclass
import random
import uuid

from data_generation.data import OPENSEARCH_DATA_TYPES, gen_column_name


@dataclass(init=True)
class OpenSearchColumn:
    name: str
    dtype: str

    def mapping_obj(self):
        return {"type": self.dtype}


@dataclass(init=True)
class OpenSearchIndex:
    name: str
    columns: list[OpenSearchColumn]
    documents: list[dict]

    def mapping(self):
        properties = {c.name: c.mapping_obj() for c in self.columns}
        return {
            "settings": {
                "index": {
                    "number_of_shards": 1,
                    "number_of_replicas": 0,
                }
            },
            "mappings": {"properties": properties},
        }


def index_name():
    return "autospec_" + str(uuid.uuid4()).replace("-", "_")[19:]


def generate_index() -> OpenSearchIndex:
    name = index_name()
    column_count, data_count = random.randint(1, 10), random.randint(1, 200)
    columns = [
        OpenSearchColumn(gen_column_name(), random.choice(list(OPENSEARCH_DATA_TYPES)))
        for _ in range(column_count)
    ]
    documents = [
        {column.name: OPENSEARCH_DATA_TYPES[column.dtype]() for column in columns}
        for _ in range(data_count)
    ]
    return OpenSearchIndex(name, columns, documents)
