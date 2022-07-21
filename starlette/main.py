from starlette.application import Starlette
from starlette.response import JSONResponse
from starlette.route import Route


async def homepage(request):
    return JSONResponse({'hello': 'world'})


app = Starlette(debug=True, routes=[
    Route('/', homepage),
])