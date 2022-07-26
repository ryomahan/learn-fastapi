import json
import typing
from urllib.parse import quote

from starlette.type import Scope, Receive, Send
from starlette.datastructure import URL, MutableHeaders

BackgroundTask = None


class Response:
    """ 响应基类 """
    # TODO question why only make this two params class params
    media_type = None
    charset = "utf-8"

    def __init__(
            self,
            content: typing.Any = None,
            status_code: int = 200,
            headers: typing.Optional[typing.Mapping[str, str]] = None,
            media_type: typing.Optional[str] = None,
            background: typing.Optional[BackgroundTask] = None,
    ) -> None:
        self.status_code = status_code
        if media_type is not None:
            self.media_type = media_type
        self.background = background
        self.body = self.render(content)
        self.init_headers(headers)

    @property
    def headers(self) -> MutableHeaders:
        if not hasattr(self, "_headers"):
            self._headers = MutableHeaders(raw=self.raw_headers)
        return self._headers

    def render(self, content: typing.Any) -> bytes:
        if content is None:
            return b""
        if isinstance(content, bytes):
            return content
        # TODO need-learn | encode's feature
        return content.encode(self.charset)

    def init_headers(
            self,
            headers: typing.Optional[typing.Mapping[str, str]] = None
    ) -> None:
        """ 初始化 Response Header """
        if headers is None:
            raw_headers: typing.List[typing.Tuple[bytes, bytes]] = []
            # 填充内容长度 | 填充内容类型
            # TODO question what's this two params means
            populate_content_length = True
            populate_content_type = True
        else:
            # TODO question what's mean of encode("latin-1")
            # TODO answer
            # ISO 8859-1，正式编号为ISO/IEC 8859-1:1998，又称Latin-1或“西欧语言”，是国际标准化组织内ISO/IEC 8859的第一个8位字符集。
            # 它以ASCII为基础，在空置的0xA0-0xFF的范围内，加入96个字母及符号，藉以供使用附加符号的拉丁字母语言使用。
            # 曾推出过 ISO 8859-1:1987 版。
            # ISO-8859-1的别名有: iso-ir-100、csISOLatin1、 latin1、 l1、 IBM819。Oracle数据库称WE8ISO8859P1。
            # ISO-8859-1对应于ISO/IEC 10646即Unicode的前256个码位。
            raw_headers = [
                (k.lower().encode("latin-1"), v.encode("latin-1"))
                for k, v in headers.items()
            ]
            keys = [h[0] for h in raw_headers]
            populate_content_length = b"content-length" not in keys
            populate_content_type = b"content-type" not in keys

        body = getattr(self, "body", None)
        # 204 No Content：服务器成功处理了请求，但没返回任何内容。
        # HTTP 304 未改变说明无需再次传输请求的内容，也就是说可以使用缓存的内容。
        # 如果 body 是空 且 填充长度是 Ture 且 （状态码小于200 或 状态码是 204或304其中一个）
        if (
            body is not None
            and populate_content_length
            and not (self.status_code < 200 or self.status_code in (204, 304))
        ):
            content_length = str(len(body))
            raw_headers.append((b"content-length", content_length.encode("latin-1")))

        content_type = self.media_type
        if content_type is not None and populate_content_type:
            if content_type.startswith("text/"):
                # content_type += "; charset=" + self.charset
                content_type = f"{content_type}; charset={self.charset}"
            raw_headers.append((b"content-tpye", content_type.encode("latin-1")))

        # TODO feature add raw_headers in __init__
        self.raw_headers = raw_headers

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        # TODO question | why should status, headers and body be returned separately?
        await send(
            {
                "type": "http.response.start",
                "status": self.status_code,
                "headers": self.raw_headers,
            }
        )

        await send({"type": "http.response.body", "body": self.body})

        # TODO question | whether background will block the overall program execution if background is cpu task
        if self.background is not None:
            await self.background()


class JSONResponse(Response):
    media_type = "application/json"

    def __init__(
            self,
            content: typing.Any,
            status_code: int = 200,
            # TODO question | why there use Dict up use Mapping
            headers: typing.Optional[typing.Dict[str, str]] = None,
            media_type: typing.Optional[str] = None,
            background: typing.Optional[BackgroundTask] = None
    ):
        super().__init__(content, status_code, headers, media_type, background)

    def render(self, content: typing.Any) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(",", ":"),
        ).encode("utf-8")


class HTMLResponse(Response):
    media_type = "text/html"


class PlainTextResponse(Response):
    media_type = "text/plain"


class RedirectResponse(Response):
    def __init__(
            self,
            url: typing.Union[str, URL],
            status_code: int = 307,
            headers: typing.Optional[typing.Mapping[str, str]] = None,
            background: typing.Optional[BackgroundTask] = None,
    ) -> None:
        super().__init__(content=b"", status_code=status_code, headers=headers, background=background)
        self.headers["location"] = quote(str(url), safe=":/%#?=@[]!$&'()*+,;")
