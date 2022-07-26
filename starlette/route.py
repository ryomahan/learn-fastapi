import re
import typing
import inspect
import functools
from enum import Enum

from starlette.type import ASGIApp, Scope, Receive, Send
from starlette.utils import is_async_callable, debug_print
from starlette.request import Request
from starlette.response import PlainTextResponse
from starlette.convertor import Convertor, CONVERTOR_TYPES
from starlette.exception import HTTPException
from starlette.websocket import WebSocketClose
from starlette.concurrency import run_in_threadpool
from starlette.datastructure import URLPath


class Match(Enum):
    NONE = 0
    PARTIAL = 1
    FULL = 2


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

    def matches(self, scope: Scope) -> typing.Tuple[Match, Scope]:
        raise NotImplementedError()

    def url_path_for(self, name: str, **path_params: typing.Any) -> URLPath:
        raise NotImplementedError()

    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        raise NotImplementedError()

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """ route 可以被作为一个独立的 ASGI Application 使用 """
        match, child_scope = self.matches(scope)

        if match == Match.NONE:
            if scope["type"] == "http":
                response = PlainTextResponse("Not Found", status_code=404)
                await response(scope, receive, send)
            elif scope["type"] == "websocket":
                websocket_close = WebSocketClose()
                await websocket_close(scope, receive, send)
            return

        scope.update(child_scope)
        await self.handle(scope, receive, send)


# 字母+多个字母、数字或下划线：字母+尽可能少的多个字母、数字或下划线
PARAM_REGEX = re.compile("{([a-zA-Z_][a-zA-Z0-9_]*)(:[a-zA-Z][a-zA-Z0-9_]*)?}")


def compile_path(path: str) -> typing.Tuple[typing.Pattern, str, typing.Dict[str, Convertor]]:
    # TODO question | what's mean
    is_host = not path.startswith("/")

    path_regex = "^"
    path_format = ""
    duplicated_params = set()

    idx = 0
    param_convertors = {}

    for match in PARAM_REGEX.finditer(path):
        param_name, convertor_type = match.groups("str")
        convertor_type = convertor_type.lstrip(":")

        assert (convertor_type in CONVERTOR_TYPES), f"Unknow path convertor '{convertor_type}'"

        convertor = CONVERTOR_TYPES[convertor_type]

        path_regex += re.escape(path[idx: match.start()])
        path_regex += f"(?P<{param_name}>{convertor.regex})"

        path_format += path[idx: match.start()]
        path_format += "{%s}" % param_name

        if param_name in param_convertors:
            duplicated_params.add(param_name)

        param_convertors[param_name] = convertor

        idx = match.end()

    if duplicated_params:
        names = ", ".join(sorted(duplicated_params))
        ending = "s" if len(duplicated_params) > 1 else ""
        raise ValueError(f"Duplicated param name{ending} {names} at path {path}")

    if is_host:
        hostname = path[idx:].split(":")[0]
        path_regex += re.escap(hostname) + "$"
    else:
        path_regex += re.escape(path[idx:]) + "$"

    path_format += path[idx:]

    return re.compile(path_regex), path_format, param_convertors


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

    def matches(self, scope: Scope) -> typing.Tuple[Match, Scope]:
        if scope["type"] == "http":
            # TODO question | what's means
            match = self.path_regex.match(scope["path"])

            if match:
                matched_params = match.groupdict()
                for key, value in matched_params.items():
                    # TODO question | what's means
                    matched_params[key] = self.param_convertors[key].convert(value)
                path_params = dict(scope.get("path_params", ""))
                # TODO question | why do this
                path_params.update(matched_params)
                child_scope = {"endpoint": self.endpoint, "path_params": path_params}
                # TODO question | what's mearns
                if self.methods and scope["method"] not in self.methods:
                    return Match.PARTIAL, child_scope
                else:
                    return Match.FULL, child_scope
        return Match.NONE, {}


    def url_path_for(self, name: str, **path_params: typing.Any) -> URLPath:
        pass

    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        debug_print("123", 123)
        if self.methods and scope["method"] not in self.methods:
            headers = {"Allow": ", ".join(self.methods)}
            if "app" in scope:
                raise HTTPException(status_code=405, headers=headers)
            else:
                response = PlainTextResponse("Method Not Allowed", status_code=405, headers=headers)
            await response(scope, receive, send)
        else:
            await self.app(scope, receive, send)
