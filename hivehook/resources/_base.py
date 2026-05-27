from __future__ import annotations

from typing import Any, AsyncIterator, Callable, Iterator

from hivehook.types import PageInfo


def paginate(list_fn: Callable[..., Any], page_size: int = 100, **filters: Any) -> Iterator[Any]:
    after = filters.pop("after", None)
    first = filters.pop("first", None) or filters.pop("limit", None) or page_size
    filters.pop("offset", None)
    while True:
        result = list_fn(after=after, first=first, **filters)
        for node in result.nodes:
            yield node
        if not result.page_info.has_next_page or not result.page_info.end_cursor:
            return
        after = result.page_info.end_cursor


async def paginate_async(list_fn: Callable[..., Any], page_size: int = 100, **filters: Any) -> AsyncIterator[Any]:
    after = filters.pop("after", None)
    first = filters.pop("first", None) or filters.pop("limit", None) or page_size
    filters.pop("offset", None)
    while True:
        result = await list_fn(after=after, first=first, **filters)
        for node in result.nodes:
            yield node
        if not result.page_info.has_next_page or not result.page_info.end_cursor:
            return
        after = result.page_info.end_cursor


def parse_page_info(data: dict[str, Any]) -> PageInfo:
    pi = data.get("pageInfo", {})
    return PageInfo(
        total=pi.get("total", 0),
        limit=pi.get("limit", 0),
        offset=pi.get("offset", 0),
        end_cursor=pi.get("endCursor"),
        has_next_page=pi.get("hasNextPage", False),
    )


def build_list_vars(
    limit: int | None = None,
    offset: int | None = None,
    after: str | None = None,
    first: int | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    v: dict[str, Any] = {}
    if limit is not None:
        v["limit"] = limit
    if offset is not None:
        v["offset"] = offset
    if after is not None:
        v["after"] = after
    if first is not None:
        v["first"] = first
    for k, val in kwargs.items():
        if val is not None:
            v[k] = val
    return v
