import typing
import inspect
import functools

from starlette.request import Request
from starlette.utils import is_async_callable
from starlette.convertor import Convertor
from starlette.concurrency import run_in_threadpool
from starlette.type import ASGIApp, Scope, Receive, Send


def request_response(func: typing.Callable) -> ASGIApp:
    """ 接收一个 函数 或 协程，并且返回一个 ASGI application """
    is_coroutine = is_async_callable(func)

    async def app(scope: Scope, receive: Receive, send: Send) -> None:
        request = Request(scope, receive=receive, send=send)

        # 如果给到的函数是协程（异步函数），将请求传入得到响应
        # 如果给到的函数不是协程（异步函数），
        if is_coroutine:
            response = await func(request)
        else:
            response = await run_in_threadpool(func, request)
        await response(scope, receive, send)

    return app


def get_name(endpoint: typing.Callable) -> str:
    # isroutine 如果该对象是一个用户定义的或内置的函数或方法，返回True。 routine 正常的，日常的
    if inspect.isroutine(endpoint) or inspect.isclass(endpoint):
        return endpoint.__name__
    return endpoint.__class__.__name__


class BaseRoute:
    pass


def compile_path(path: str) -> typing.Tuple[typing.Pattern, str, typing.Dict[str, Convertor]]:
    is_host = not path.startswith("/")

    path_regex = "^"
    path_format = ""
    pass


class Route(BaseRoute):

    def __init__(
            self,
            path: str,
            endpoint: typing.Callable,
            *,
            methods: typing.Optional[typing.List[str]] = None,
            name: typing.Optional[str] = None,
            include_in_schema: bool = True,
    ) -> None:
        assert path.startswith("/"), "Route path must start with '/'"

        # 路由路径
        self.path = path
        # 处理端（类似 django view）
        self.endpoint = endpoint
        # 路由名称
        self.name = get_name(endpoint) if name is None else name

        # TODO question | why use endpoint_handler to wrapper endpoint
        # TODO answer   | maybe don't want to destroy endpoint
        endpoint_handler = endpoint

        # 如果 endpoint_handler 是偏函数
        while isinstance(endpoint_handler, functools.partial):
            endpoint_handler = endpoint_handler.func

        # 如果 endpoint_handler 是一个函数或方法
        if inspect.isfunction(endpoint_handler) or inspect.ismethod(endpoint_handler):
            self.app = request_response(endpoint)
            if methods is None:
                methods = ["GET"]
        else:
            self.app = endpoint

        if methods is None:
            self.methods = None
        else:
            self.methods = {method.upper() for method in methods}
            # TODO question | what's mean
            if "GET" in self.methods:
                self.methods.add("HEAD")

        self.path_regex, self.path_format, self.param_convertors = compile_path(path)

