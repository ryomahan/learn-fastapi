import typing
import asyncio
import functools


def is_async_callable(obj: typing.Any) -> bool:
    # 如果传入的对象是一个偏函数，则先将最终的函数体取出
    while isinstance(obj, functools.partial):
        obj = obj.func

    # 如果传入的对象是有一个 decorated coroutine function
    # 或者传入的对象可调用并且对象的 __call__ 方法是一个 decorated coroutine function
    return \
        asyncio.iscoroutinefunction(obj) or \
        (callable(obj) and asyncio.iscoroutinefunction(obj.__call__))


def debug_print(obj: typing.Any) -> None:
    print("-" * 50)
    print(obj)
    print("-" * 50)
