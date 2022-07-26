import types
import typing
import inspect
import warnings
import functools
import contextlib
from enum import Enum
from contextlib import asynccontextmanager

from starlette.type import ASGIApp, Scope, Receive, Send
from starlette.route import BaseRoute
from starlette.response import PlainTextResponse, RedirectResponse
from starlette.exception import HTTPException
from starlette.websocket import WebSocketClose
from starlette.datastructure import URL


_T = typing.TypeVar("_T")


class Match(Enum):
    NONE = 0
    PARTIAL = 1
    FULL = 2


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

    async def lifespan(self, scope: Scope, receive: Receive, send: Send) -> None:
        pass

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        assert scope["type"] in ("http", "websocket", "lifespan")

        if "router" not in scope:
            scope["router"] = self

        if scope["type"] == "lifespan":
            await self.lifespan(scope, receive, send)
            return

        # 局部的
        partial = None

        for route in self.routes:
            match, child_scope = route.matches(scope)

            if match == Match.FULL:
                scope.update(child_scope)
                await route.handle(scope, receive, send)
                return
            elif match == Match.PARTIAL and partial is None:
                partial = route
                partial_scope = child_scope

        if partial is not None:
            scope.update(partial_scope)
            await partial.handle(scope, receive, send)
            return

        if scope["type"] == "http" and self.redirect_slashes and scope["path"] != "/":
            redirect_scope = dict(scope)
            if scope["path"].endswith("/"):
                redirect_scope["path"] = redirect_scope["path"].rstrip("/")
            else:
                redirect_scope["path"] = redirect_scope["path"] + "/"

            for route in self.routes:
                match, child_scope = route.matches(redirect_scope)
                if match != Match.NONE:
                    redirect_url = URL(scope=redirect_scope)
                    response = RedirectResponse(url=str(redirect_url))
                    await response(scope, receive, send)
                    return

        await self.default(scope, receive, send)




