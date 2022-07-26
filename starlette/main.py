from starlette.application import Starlette

from starlette.route import Route
from starlette.response import JSONResponse


async def homepage(request):
    return JSONResponse({'hello': 'world'})


async def apple(request):
    return JSONResponse({"an": "apple"})

app = Starlette(debug=True, routes=[
    Route('/', homepage),
    Route("/apple", apple)
])
