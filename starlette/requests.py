import typing

from starlette.types import Scope, Receive


class HTTPConnection(typing.Mapping[str, typing.Any]):
    """
    HTTP 请求连接基类，用于提供 Request 和 WebSocket 的通用功能。
    """

    def __init__(self, scope: Scope, receive: typing.Optional[Receive] = None) -> None:
        pass


class Request(HTTPConnection):
    pass
