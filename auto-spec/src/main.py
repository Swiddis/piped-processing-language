import asyncio
import random
import uuid
from opensearchpy import AsyncOpenSearch
from faker import Faker
import json
import typing
import tqdm

fake = Faker()

def opensearch():
    return AsyncOpenSearch(
        [{ "host": "localhost", "port": 9200 }]
    )

def index_name():
    return "autospec_" + str(uuid.uuid4()).replace("-", "_")[19:]

async def assign_index_contents(client: AsyncOpenSearch, index_name: str):
    global fake
    # TODO make this a separate module
    record = lambda: { "int_key": random.randint(-2**31, 2**31-1), "str_key": fake.text() }
    result = await client.indices.create(index_name, {
        "settings": {
            "index": {
                "number_of_shards": 1,
                "number_of_replicas": 0,
            }
        },
        "mappings": {
            "properties": {
                "str_key": {
                    "type": "text",
                },
                "int_key": {
                    "type": "integer",
                },
            }
        }
    })
    assert not result.get("errors", None), f"failed to create index: {result}"
    
    return [
        record()
        for _ in range(random.randint(1, 100))
    ]

async def populate_index(client: AsyncOpenSearch, index: str, index_data: list[dict]):
    header = json.dumps({"index": { "_index": index } })
    bulk_req = '\n'.join(header + "\n" + json.dumps(row) for row in index_data)
    response = await client.bulk(bulk_req, params={ 'refresh': 'wait_for' })
    assert not response['errors'], f"failed to insert to index: {response}"

async def run_query(client: AsyncOpenSearch, query: str):
    response = await client.http.post("/_plugins/_ppl", body={ "query": query })
    return response

def expect_result_types(result: dict, expect_types: list[str]):
    types = list(map(lambda s: s.get("type", None), result.get("schema", [])))
    assert types == expect_types, f"incorrect types: {types}, expected {expect_types}"

def expect_result_data(result: dict, data: list[list[typing.Any]]):
    assert result.get("datarows", []) == data, f"incorrect data: {result}, expected {data}"

async def do_test(client: AsyncOpenSearch):
    iname = index_name()
    idata = await assign_index_contents(client, iname)
    await populate_index(client, iname, idata)

    query = f"source = {iname} | stats count();"
    result = await run_query(client, query)

    expect_result_types(result, ['int'])
    expect_result_data(result, [[len(idata)]])
    await client.indices.delete(iname)

async def do_test_capturing_result(client: AsyncOpenSearch):
    try:
        await do_test(client)
        return True
    except AssertionError as err:
        with open('err.log', 'a') as fp:
            fp.write(repr(err) + "\n")
        return False

async def main():
    client = opensearch()
    try:
        futures = [asyncio.create_task(do_test_capturing_result(client)) for _ in range(100)]
        total = 0
        for future in tqdm.tqdm(futures):
            total += int(await future)
        print("Count queries:", total, "/", len(futures))
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
