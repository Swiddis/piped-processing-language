from dataclasses import dataclass

from data_generation.index import OpenSearchColumn, OpenSearchIndex, index_name


@dataclass(init=True)
class TestCase:
    name: str
    mapping: dict[str, str]
    documents: list[dict]
    language: str
    query: str

    def to_case_dict(self):
        return {
            "data": {
                "mapping": self.mapping,
                "documents": self.documents,
            },
            "query": {
                "language": self.language,
                "query": self.query,
            }
        }

    def from_case_dict(case_name: str, case_dict: dict):
        return TestCase(
            case_name,
            case_dict["data"]["mapping"],
            case_dict["data"]["documents"],
            case_dict["query"]["language"],
            case_dict["query"]["query"],
        )

    def index(self):
        return OpenSearchIndex(
            index_name(),
            [OpenSearchColumn(k, v) for k, v in self.mapping.items()],
            self.documents,
        )
