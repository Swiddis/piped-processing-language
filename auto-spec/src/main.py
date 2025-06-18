# Enable type checking
from beartype.claw import beartype_package

from data_generation.data import OPENSEARCH_DATA_TYPES
from data_generation.index import generate_index

beartype_package("src")

import asyncio
import json
import sys
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


async def do_test(client: AsyncOpenSearch):
    async with context(client) as ctx:
        query = f"source = {ctx.index.name} | stats count();"
        result = await ctx.run_query(query)

        expect_result_types(result, ["int"])
        expect_result_data(result, [[len(ctx.index.documents)]])


async def do_test_capturing_result(client: AsyncOpenSearch):
    try:
        await do_test(client)
        return True
    except AssertionError as err:
        with open("err.log", "a") as fp:
            fp.write(repr(err) + "\n")
        return False


async def main_run_tests():
    os_adaptor = opensearch()
    try:
        futures = [
            asyncio.create_task(do_test_capturing_result(os_adaptor))
            for _ in range(100)
        ]
        total = 0
        for future in tqdm.tqdm(asyncio.as_completed(futures), total=len(futures)):
            total += int(await future)
        print("Count queries:", total, "/", len(futures))
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

    as_toml_table = lambda o: json.dumps(o, separators=(', ', ' = '))
    with open(f'src/query_cases/cases/{function['name']}_{sig_idx}.toml', 'w') as fp:
        fp.write("[data]\n")
        fp.write(f"mapping = {as_toml_table(case['data']['mapping'])}\n")
        fp.write(f"documents = [\n")
        for doc in case['data']['documents']:
            fp.write('\t' + as_toml_table(doc) + ',\n')
        fp.write(f']\n\n[query]\nlanguage = "ppl"\nquery = {json.dumps(case['query']['query'])}\n')


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
