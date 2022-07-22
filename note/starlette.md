## starlette 手撸顺序

### main

给定一个最小执行程序：需要 Starlette Route JSONResponse

### tpye

ASGIApp | Scope | Receive | Send | Message

### application

Starlette -> Starlette.\_\_init\_\_ -> 
Starlette.build_middleware_stack -> Starlette.\_\_call\_\_ ->

## route

BaseRoute -> Route -> \_\_init\_\_ 

## utils

is_async_callable

## request

HTTPConnection -> Request

## response
参考资料：MDN-HTTP
response -> JSONResponse -> Response -> Response.\_\_init\_\_ ->
Response.render() -> Response.init_headers()
