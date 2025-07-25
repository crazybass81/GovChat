# SPDX-License-Identifier: Apache-2.0
#
# The OpenSearch Contributors require contributions made to
# this file be licensed under the Apache-2.0 license or a
# compatible open source license.
#
# Modifications Copyright OpenSearch Contributors. See
# GitHub history for details.

import os
import time
from typing import Any
from unittest import SkipTest

from opensearchpy import AsyncOpenSearch
from opensearchpy.exceptions import ConnectionError

OPENSEARCH_URL = os.environ.get("OPENSEARCH_URL", "https://admin:admin@localhost:9200")


async def get_test_client(nowait: bool = False, **kwargs: Any) -> Any:
    # construct kwargs from the environment
    kw = {"timeout": 30}

    from opensearchpy import AsyncConnection

    async_connection = AsyncConnection()
    if hasattr(async_connection, "AIOHttpConnection"):
        kw["connection_class"] = async_connection.AIOHttpConnection

    kw.update(kwargs)
    client = AsyncOpenSearch(OPENSEARCH_URL, **kw)  # type: ignore

    # wait for yellow status
    for _ in range(1 if nowait else 100):
        try:
            await client.cluster.health(wait_for_status="yellow")
            return client
        except ConnectionError:
            time.sleep(0.1)
    else:
        # timeout
        raise SkipTest("OpenSearch failed to start.")
