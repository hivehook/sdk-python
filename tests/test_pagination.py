from __future__ import annotations

import asyncio

from hivehook import paginate, paginate_async
from hivehook.types import ListResult, PageInfo


def test_paginate_walks_every_page():
    pages = {
        None: ListResult(nodes=["a", "b"], page_info=PageInfo(end_cursor="c1", has_next_page=True)),
        "c1": ListResult(nodes=["c"], page_info=PageInfo(end_cursor=None, has_next_page=False)),
    }
    seen_after = []

    def fake_list(after=None, first=None, **kw):
        seen_after.append(after)
        return pages[after]

    assert list(paginate(fake_list)) == ["a", "b", "c"]
    assert seen_after == [None, "c1"]


def test_paginate_single_page():
    page = ListResult(nodes=["only"], page_info=PageInfo(has_next_page=False))

    def fake_list(after=None, first=None, **kw):
        return page

    assert list(paginate(fake_list)) == ["only"]


def test_paginate_async_walks_every_page():
    pages = {
        None: ListResult(nodes=["a"], page_info=PageInfo(end_cursor="c1", has_next_page=True)),
        "c1": ListResult(nodes=["b"], page_info=PageInfo(end_cursor=None, has_next_page=False)),
    }

    async def fake_list(after=None, first=None, **kw):
        return pages[after]

    async def collect():
        return [x async for x in paginate_async(fake_list)]

    assert asyncio.run(collect()) == ["a", "b"]
