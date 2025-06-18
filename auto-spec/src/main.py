# Enable type checking
from beartype.claw import beartype_package

beartype_package("src")

import asyncio
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


async def main():
    os_adaptor = opensearch()
    try:
        futures = [
            asyncio.create_task(do_test_capturing_result(os_adaptor))
            for _ in range(1000)
        ]
        total = 0
        for future in tqdm.tqdm(asyncio.as_completed(futures), total=len(futures)):
            total += int(await future)
        print("Count queries:", total, "/", len(futures))
    finally:
        await os_adaptor.close()


if __name__ == "__main__":
    asyncio.run(main())
