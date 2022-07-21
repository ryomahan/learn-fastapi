# uvicorn 执行顺序

uvicorn.run(app)

config = Config(app)

server = Server(config)

server.run | 开启异步事件循环

return async.run(server.server(socket))

config.load

初始化 config.loaded_app


