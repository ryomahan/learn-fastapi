import asyncio


async def set_after(fut):
    await asyncio.sleep(2)
    fut.set_result("666")


async def main():
    # 获取当前事件循环
    loop = asyncio.get_running_loop()

    # 创建一个任务（Future对象），没绑定任何行为，则这个任务永远不知道什么时候结束。
    fut = loop.create_future()

    print(loop.time())

    # 创建一个任务（Task对象），绑定了set_after函数，函数内部在2s之后，会给fut赋值。
    # 即手动设置 future 任务的最终结果，那么fut就可以结束了。
    await loop.create_task(set_after(fut))

    # 等待 Future对象获取 最终结果，否则一直等下去
    data = await fut
    print(data)


if __name__ == "__main__":
    import asyncio
    import datetime
    import time


    def function_1(end_time, loop):
        print("function_1 called")
        if (loop.time() + 1.0) < end_time:
            loop.call_later(1, function_2, end_time, loop)
        else:
            loop.stop()


    def function_2(end_time, loop):
        print("function_2 called ")
        if (loop.time() + 1.0) < end_time:
            loop.call_later(1, function_3, end_time, loop)
        else:
            loop.stop()


    def function_3(end_time, loop):
        print("function_3 called")
        if (loop.time() + 1.0) < end_time:
            loop.call_later(1, function_1, end_time, loop)
        else:
            loop.stop()


    def function_4(end_time, loop):
        print("function_5 called")
        if (loop.time() + 1.0) < end_time:
            loop.call_later(1, function_4, end_time, loop)
        else:
            loop.stop()


    loop = asyncio.get_event_loop()

    end_loop = loop.time() + 12.0
    loop.call_soon(function_1, end_loop, loop)
    # loop.call_soon(function_4, end_loop, loop)
    loop.run_forever()
    loop.close()
