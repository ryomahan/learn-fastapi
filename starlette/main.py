from starlette.application import Starlette

from starlette.route import Route
from starlette.response import JSONResponse, PlainTextResponse


async def homepage(request):
    return JSONResponse({'hello': 'world'})


async def apple(request):
    return JSONResponse({"an": "apple"})


def user_me(request):
    return PlainTextResponse("Hello, World!")


def user(request):
    username = request.path_params["username"]
    return PlainTextResponse(f"Hello, {username}!")


app = Starlette(debug=True, routes=[
    Route('/', homepage),
    Route("/apple", apple),
    Route("/user/me", user_me),
    Route("/user/{username}", user),
])
