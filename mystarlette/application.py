from cgitb import handler
import typing

from starlette.type import ASGIApp, Scope, Receive, Send
from starlette.route import BaseRoute
from starlette.router import Router
from starlette.request import Request
from starlette.response import Response
from starlette.middleware import Middleware
from starlette.datastructure import State
from starlette.middleware.error import ServerErrorMiddleware
from starlette.middleware.exception import ExceptionMiddleware


class Starlette:
    
    def __init__(
        self,
        debug: bool = False,
        routes: typing.Optional[typing.Sequence[BaseRoute]] = None,
        middleware: typing.Optional[typing.Sequence[Middleware]] = None,
        exception_handlers: typing.Optional[
            typing.Mapping[
                typing.Any,
                typing.Callable[
                    [Request, Exception],
                    typing.Union[Response, typing.Awaitable[Response]]
                ]
            ]
        ] = None,
        on_startup: typing.Optional[typing.Sequence[typing.Callable]] = None,
        on_shutdown: typing.Optional[typing.Sequence[typing.Callable]] = None,
        lifespan: typing.Optional[
            typing.Callable[["Starlette"], typing.AsyncContextManager]
        ] = None
    ) -> None:
        # lifespan 上下文函数是 on_startup 和 on_shutdown 处理器的一种新写法
        # 使用其中一个即可，不要同时设置两者
        assert lifespan is None or (on_startup is None and on_shutdown is None), "Use either 'lifespan' or 'on_startup'/'on_shutdown', not both."

        # 初始化应用必要数据
        self._debug = debug
        self.state = State()
        self.router = Router(
            routes, on_startup=on_startup, on_shutdown=on_shutdown, lifespan=lifespan, redirect_slashes=False,
        )
        self.exception_handlers = (
            {} if exception_handlers is None else dict(exception_handlers)
        )
        self.user_middleware = [] if middleware is None else list(middleware)

        self.middleware_stack = self.build_middleware_stack()

    @property
    def debug(self) -> bool:
        return self._debug

    @debug.setter
    def debug(self, value: bool):
        # TODO question What does this function do?
        self._debug = value
        self.middleware_stack = self.build_middleware_stack()

    def build_middleware_stack(self) -> ASGIApp:
        """
        这实质上应该是 Starlette 项目中 App 的生成装置，但是不知道为什么会被冠以 build_middleware_stack 之名
        感觉这部分是不是应该可以尝试重构一下，把这部分的业务逻辑梳理清楚让各种模块各归其位，方便后续的扩展
        当然这也有可能是作者有意为之，还需要继续阅读才能确定
        """
        # TODO question there is not self.debug
        # TODO answer   debug is a property
        debug = self.debug
        error_handler = None
        exception_handlers: typing.Dict[
            typing.Any, typing.Callable[[Request, Exception], Response]
        ] = {}

        # 通过遍历 exception_handlers 拆分 error_handler（服务器报错） 和 exception_handlers（代码报错）
        for key, value in self.exception_handlers.items():
            if key in (500, Exception):
                error_handler = value
            else:
                # TODO question what's means
                exception_handlers[key] = value
        
        middleware = (
            [Middleware(ServerErrorMiddleware, handler=error_handler, debug=debug)]
            + self.user_middleware
            + [
                Middleware(ExceptionMiddleware, handlers=exception_handlers, debug=debug)
            ]
        )

        app = self.router

        # 将 middleware 顺序进行反转，然后不断进行套娃
        for cls, options in reversed(middleware):
            app = cls(app=app, **options)

        return app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        scope["app"] = self
        await self.middleware_stack(scope, receive, send)

