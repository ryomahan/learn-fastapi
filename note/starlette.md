## starlette 手撸顺序

tpye

application -> Starlette -> Starlette.\_\_init\_\_ -> 
Starlette.build_middleware_stack -> Starlette.\_\_call\_\_ ->

参考资料：MDN-HTTP
response -> JSONResponse -> Response -> Response.\_\_init\_\_ ->
Response.render() -> Response.init_headers()

route
