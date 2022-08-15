import typing

from starlette.type import Scope, Receive, Send


class WebSocketClose:

    def __init__(self, code: int = 1000, reason: typing.Optional[str] = None) -> None:
        self.code = code
        self.reason = reason or ""

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        await send(
            {"type": "websocket.close", "code": self.code, "reason": self.reason}
        )
