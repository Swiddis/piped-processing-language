from dataclasses import dataclass

from data_generation.index import OpenSearchColumn, OpenSearchIndex, index_name


@dataclass(init=True)
class TestCase:
    mapping: dict[str, str]
    documents: list[dict]
    language: str
    query: str

    def from_case_dict(case_dict: dict):
        return TestCase(
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
