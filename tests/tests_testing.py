import asyncio

import pytest

from tests.conftest import QueueMockContext


@pytest.mark.asyncio
def test_queue_mock_context_sync():
    queue = asyncio.Queue()

    with QueueMockContext(queue) as m:
        queue.put_nowait(1)
        queue.put_nowait(2)
        queue.get_nowait()

    assert m.put_items == [1, 2]
    assert m.got_items == [1]


@pytest.mark.asyncio
async def test_queue_mock_context_async():
    queue = asyncio.Queue()

    with QueueMockContext(queue) as m:
        await queue.put(1)
        await queue.put(2)
        await queue.get()

    assert m.put_items == [1, 2]
    assert m.got_items == [1]