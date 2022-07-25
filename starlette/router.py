import types
import typing
import inspect
import warnings
import functools
import contextlib
from contextlib import asynccontextmanager

from starlette.type import ASGIApp, Scope, Receive, Send
from starlette.route import BaseRoute
from starlette.response import PlainTextResponse
from starlette.exception import HTTPException
from starlette.websocket import WebSocketClose


_T = typing.TypeVar("_T")


# TODO question | why not _AsyncLifeContextManager?
class _AsyncLiftContextManager(typing.AsyncContextManager[_T]):
    def __init__(self, cm: typing.ContextManager[_T]):
        self._cm = cm

    async def __aenter__(self) -> _T:
        return self._cm.__enter__()

    async def __aexit__(
            self,
            exc_type: typing.Optional[typing.Type[BaseException]],
            exc_value: typing.Optional[BaseException],
            traceback: typing.Optional[types.TracebackType],
    ) -> typing.Optional[bool]:
        return self._cm.__exit__(exc_type, exc_value, traceback)


def _wrap_gen_lifespan_context(
        lifespan_context: typing.Callable[[typing.Any], typing.Generator]
) -> typing.Callable[[typing.Any], typing.AsyncContextManager]:
    cmgr = contextlib.contextmanager(lifespan_context)

    @functools.wraps(cmgr)
    def wrapper(app: typing.Any) -> _AsyncLiftContextManager:
        return _AsyncLiftContextManager(cmgr(app))

    return wrapper


class _DefaultLifespan:

    def __init__(self, router: "Router") -> None:
        self._router = router

    async def __aenter__(self) -> None:
        await self._router.startup()

    async def __aexit__(self, *exc_info: object) -> None:
        await self._router.shutdown()

    def __call__(self, _T, app: object) -> _T:
        return self


class Router:

    def __init__(
            self,
            routes: typing.Optional[typing.Sequence[BaseRoute]] = None,
            # 是否开启路径尾部的斜线
            redirect_slashes: bool = True,
            default: typing.Optional[ASGIApp] = None,
            on_startup: typing.Optional[typing.Sequence[typing.Callable]] = None,
            on_shutdown: typing.Optional[typing.Sequence[typing.Callable]] = None,
            lifespan: typing.Optional[typing.Callable[[typing.Any], typing.AsyncContextManager]] = None,
    ) -> None:
        self.routes = [] if routes is None else list(routes)
        self.redirect_slashes = redirect_slashes
        self.default = self.not_found if default is None else default
        self.on_startup = [] if on_startup is None else list(on_startup)
        self.on_shutdown = [] if on_startup is None else list(on_shutdown)

        if lifespan is None:
            self.lifespan_context: typing.Callable[[typing.Any], typing.AsyncContextManager] = _DefaultLifespan(self)
        elif inspect.isasyncgenfunction(lifespan):
            warnings.warn("async generator function lifespans are deprecated, use an @contextlib.asynccontextmanager function instead", DeprecationWarning)
            self.lifespan_context = asynccontextmanager(lifespan,)
        elif inspect.isgeneratorfunction(lifespan):
            warnings.warn("generator function lifespans are deprecated, use an @contextlib.asynccontextmanager function instead", DeprecationWarning)
            self.lifespan_context = _wrap_gen_lifespan_context(lifespan,)  # type: ignore[arg-type]
        else:
            self.lifespan_context = lifespan

    async def not_found(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "websocket":
            websocket_close = WebSocketClose()
            await websocket_close(scope, receive, send)
            return

        # 如果运行在一个 Starlette Application 内部，抛出一个异常，目的是内置的异常处理器能够处理并返回响应
        # 如果是 plain ASGI apps，则只需要返回一个响应即可
        if "app" in scope:
            raise HTTPException(status_code=404)
        else:
            response = PlainTextResponse("Not Found", status_code=404)
        await response(scope, receive, send)
