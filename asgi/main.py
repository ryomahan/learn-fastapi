import pprint

class Response:

    def __init__(self, body):
        self.body = body.encode("utf-8")
        raw_headers = []
        content_length = str(len(body))
        raw_headers.append((b"content-length", content_length.encode("latin-1")))
        content_type = "text/plain"
        raw_headers.append((b"content-tpye", content_type.encode("latin-1")))
        self.raw_headers = raw_headers

    async def __call__(self, scope, receive, send):
        await send(
            {
                "type": "http.response.start",
                "status": 200,
                "headers": self.raw_headers,
            }
        )

        await send({"type": "http.response.body", "body": self.body})


class ASGIApplication:

    def __init__(self, func):

        async def app(scope, receive, send) -> None:
            response = await func(None)
            await response(scope, receive, send)

        self.app = app

    async def __call__(self, scope, receive, send):
        await self.app(scope, receive, send)


async def hello_world(request):
    return Response()


# app = ASGIApplication(func=hello_world)


async def app(scope, receive, send):
    body = "Hello, world!".encode("utf-8")
    raw_headers = []
    content_length = str(len(body))
    raw_headers.append((b"content-length", content_length.encode("latin-1")))
    content_type = "text/plain"
    raw_headers.append((b"content-tpye", content_type.encode("latin-1")))
    await send(
        {
            "type": "http.response.start",
            "status": 200,
            "headers": raw_headers,
        }
    )

    await send({"type": "http.response.body", "body": body})
