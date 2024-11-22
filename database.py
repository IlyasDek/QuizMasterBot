import os
import ydb
import asyncio
from concurrent.futures import ThreadPoolExecutor

YDB_ENDPOINT = os.getenv("YDB_ENDPOINT")
YDB_DATABASE = os.getenv("YDB_DATABASE")

executor = ThreadPoolExecutor()

def get_ydb_pool(ydb_endpoint, ydb_database, timeout=30):
    ydb_driver_config = ydb.DriverConfig(
        ydb_endpoint,
        ydb_database,
        credentials=ydb.credentials_from_env_variables(),
        root_certificates=ydb.load_ydb_root_certificate(),
    )

    ydb_driver = ydb.Driver(ydb_driver_config)
    ydb_driver.wait(fail_fast=True, timeout=timeout)
    return ydb.SessionPool(ydb_driver)

def _format_kwargs(kwargs):
    return {"${}".format(key): value for key, value in kwargs.items()}

def _sync_execute_update_query(pool, query, kwargs):
    def callee(session):
        prepared_query = session.prepare(query)
        session.transaction(ydb.SerializableReadWrite()).execute(
            prepared_query, _format_kwargs(kwargs), commit_tx=True
        )
    pool.retry_operation_sync(callee)

def _sync_execute_select_query(pool, query, kwargs):
    def callee(session):
        prepared_query = session.prepare(query)
        result_sets = session.transaction(ydb.SerializableReadWrite()).execute(
            prepared_query, _format_kwargs(kwargs), commit_tx=True
        )
        return result_sets[0].rows if result_sets else []
    return pool.retry_operation_sync(callee)

async def execute_update_query(pool, query, **kwargs):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(
        executor, _sync_execute_update_query, pool, query, kwargs
    )

async def execute_select_query(pool, query, **kwargs):
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(
        executor, _sync_execute_select_query, pool, query, kwargs
    )

pool = get_ydb_pool(YDB_ENDPOINT, YDB_DATABASE)
