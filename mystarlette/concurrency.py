import sys
import typing
import functools

import anyio

if sys.version_info >= (3, 10):  # pragma: no cover
    from typing import ParamSpec
else:  # pragma: no cover
    from typing_extensions import ParamSpec

T = typing.TypeVar("T")
P = ParamSpec("P")


async def run_in_threadpool(func: typing.Callable[P, T], *args: P.args, **kwargs: P.kwargs) -> T:
    # TODO question | what's this function's feature
    if kwargs:
        func = functools.partial(func, **kwargs)
    # TODO need-learn | anyio
    return await anyio.to_thread.run_sync(func, *args)