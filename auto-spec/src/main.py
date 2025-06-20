# Enable type checking
from beartype.claw import beartype_package

from data_generation.data import OPENSEARCH_DATA_TYPES
from data_generation.index import generate_index
from query_cases import TestCase

beartype_package("src")

import asyncio
import json
import os
import sys
import tomllib
import typing

import tqdm
from opensearchpy import AsyncOpenSearch

from adaptors.context import context
from adaptors.opensearch import OpenSearchAdaptor


def opensearch() -> OpenSearchAdaptor:
    # TODO get this from a config instead of hardcoding it
    client = AsyncOpenSearch([{"host": "localhost", "port": 9200}])
    return OpenSearchAdaptor(client)


def expect_result_types(result: dict, expect_types: list[str]):
    types = list(map(lambda s: s.get("type", None), result.get("schema", [])))
    assert types == expect_types, f"incorrect types: {types}, expected {expect_types}"


def expect_result_data(result: dict, data: list[list[typing.Any]]):
    assert (
        result.get("datarows", []) == data
    ), f"incorrect data: {result}, expected {data}"


async def do_test(client: AsyncOpenSearch, test_case: TestCase):
    async with context(client, test_case.index()) as ctx:
        query = test_case.query.replace("$INDEX", ctx.index.name)
        result = await ctx.run_query(query)

        with open('output.json', 'a') as fp:
            fp.write(json.dumps(result) + "\n")


async def do_test_capturing_result(client: AsyncOpenSearch, test_case: TestCase):
    try:
        await do_test(client, test_case)
        return True
    except Exception as err:
        with open("err.log", "a") as fp:
            fp.write(repr(err) + "\n")
        return False


def load_tests():
    for dirpath, _, filenames in os.walk('src/query_cases/cases'):
        for filename in filenames:
            if not filename.endswith('.json'):
                continue
            with open(os.path.join(dirpath, filename), 'r') as fp:
                yield TestCase.from_case_dict(json.load(fp))


async def main_run_tests():
    os_adaptor = opensearch()
    try:
        futures = [
            asyncio.create_task(do_test_capturing_result(os_adaptor, test_case))
            for test_case in load_tests()
        ]
        total = 0
        for future in tqdm.tqdm(asyncio.as_completed(futures), total=len(futures)):
            total += int(await future)
        print("Successful Queries:", total, "/", len(futures))
    finally:
        await os_adaptor.close()


# TODO modularize
def build_case_from(function, signature, sig_idx):
    if not all(s in OPENSEARCH_DATA_TYPES for s in signature):
        return
    index = generate_index(column_types=signature)
    case = {
        "data": {
            "mapping": {col.name: col.dtype for col in index.columns},
            "documents": index.documents,
        },
        "query": {
            "language": "ppl",
            "query": f"source = $INDEX | eval result = {function['str']}({', '.join(col.name for col in index.columns)}) | fields result",
        },
    }

    with open(f'src/query_cases/cases/{function['name']}_{sig_idx}.json', 'w') as fp:
        json.dump(case, fp, indent=4)


def main_generate_tests():
    with open("data/function_signatures.json", "r") as fp:
        functions = json.load(fp)
    for function in functions:
        for i, signature in enumerate(function["signatures"]):
            build_case_from(function, signature, i)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: main.py [test|generate]")
        sys.exit(1)
    if sys.argv[1] == "test":
        asyncio.run(main_run_tests())
    if sys.argv[1] == "generate":
        main_generate_tests()
