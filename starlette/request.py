import typing

from starlette.type import Scope, Receive, Send, Message
from starlette.datastructure import Headers


class HTTPConnection(typing.Mapping[str, typing.Any]):
    """
    HTTP 请求连接基类，用于提供 Request 和 WebSocket 的通用功能。
    """

    def __init__(self, scope: Scope, receive: typing.Optional[Receive] = None) -> None:
        # TODO question | why HTTPConnection class type in http or websocket
        assert scope["type"] in ("http", "websocket",)

        self.scope = scope

    def __getitem__(self, key: str) -> typing.Any:
        return self.scope[key]

    def __iter__(self) -> typing.Iterator[str]:
        return iter(self.scope)

    def __len__(self) -> int:
        return len(self.scope)

    @property
    def headers(self) -> Headers:
        if not hasattr(self, "_headers"):
            self._headers = Headers(scope=self.scope)
        return self._headers


async def empty_receive() -> typing.NoReturn:
    raise RuntimeError("Receive channel has not been made available")


async def empty_send(message: Message) -> typing.NoReturn:
    raise RuntimeError("Send channel has not been made available")


class Request(HTTPConnection):

    def __init__(self, scope: Scope, receive: Receive = empty_receive, send: Send = empty_send):
        super().__init__(scope)
        assert scope["type"] == "http"
        self._receive = receive
        self._send = send
        self._stream_consumed = False
        self._is_disconnected = False

