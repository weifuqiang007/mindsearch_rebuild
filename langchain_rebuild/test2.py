# # -*- coding: utf-8 -*-
# # 开发团队   ：tianyikeji
# # 开发人员   ：weifuqiang
# # 开发时间   ：2025/8/4  13:42
# # 文件名称   ：test2.PY
# # 开发工具   ：PyCharm
#
# # import asyncio
# # import time
# #
# # async def async_hello_world():
# #     now = time.time()
# #     await asyncio.sleep(1)
# #     print(time.time() - now) # 1.0013360977172852
# #     print("Hello, world!") # Hello, world!
# #     await asyncio.sleep(1)
# #     print(time.time() - now) # 2.0025689601898193
# # # print("===")
# # print(asyncio.sleep(1)) # <coroutine object sleep at 0x102f663b0>
# # coro = async_hello_world()
# # asyncio.run(coro)
#
# # import asyncio
# # import time
# #
# # async def async_hello_world():
# #     now = time.time()
# #     await asyncio.sleep(1)
# #     print(time.time() - now)
# #     print("Hello, world!")
# #     await asyncio.sleep(1)
# #     print(time.time() - now)
# #
# # async def main():
# #     await asyncio.gather(async_hello_world(), async_hello_world(), async_hello_world())
# #
# # now = time.time()
# # # run 3 async_hello_world() coroutine concurrently
# # asyncio.run(main())
# #
# # print(f"Total time for running 3 coroutine: {time.time() - now}")
# #
# # import time
# # def normal_hello_world():
# #     now = time.time()
# #     time.sleep(1)
# #     print(time.time() - now)
# #     print("Hello, world!")
# #     time.sleep(1)
# #     print(time.time() - now)
# #
# # now = time.time()
# # normal_hello_world()
# # normal_hello_world()
# # normal_hello_world()
# # print(f"Total time for running 3 normal function: {time.time() - now}")
#
# # import asyncio
# # import time
# #
# # async def async_hello_world():
# #     now = time.time()
# #     print("dengdai")
# #     await asyncio.sleep(1)
# #     print(time.time() - now)
# #     print("Hello, world!")
# #     await asyncio.sleep(1)
# #     print(time.time() - now)
# #
# # async def main():
# #     task1 = asyncio.create_task(async_hello_world())
# #     task2 = asyncio.create_task(async_hello_world())
# #     task3 = asyncio.create_task(async_hello_world())
# #     await task1
# #     await task2
# #     await task3
# #
# # now = time.time()
# # # run 3 async_hello_world() coroutine concurrently
# # asyncio.run(main())
# #
# # print(f"Total time for running 3 coroutine: {time.time() - now}")
#
# """
# 阶段性总结
# 如果我们只是简单地使用asyncio，那么看到这里就可以结束了。asyncio里面，await的用法有两种：
#
# await coroutine，就像普通的函数调用一样，执行coroutine对应的代码
# await task，中断当前代码的执行，event loop开始调度任务，直到task执行结束，恢复执行当前代码。
# """
#
# # 进阶代码 await + future
# # 上述用法是把asyncio.sleep当做一个内置的黑盒函数来看待的，当我们await asyncio.sleep(1)时，协程就会休眠1秒。
#
# # 事实上，asyncio.sleep的实现并不复杂，就是纯Python的代码：
#
# # async def sleep(delay, result=None):
# #     """Coroutine that completes after a given time (in seconds)."""
# #     if delay <= 0:
# #         await __sleep0()
# #         return result
# #
# #     loop = events.get_running_loop()
# #     future = loop.create_future()
# #     h = loop.call_later(delay,
# #                         futures._set_result_unless_cancelled,
# #                         future, result)
# #     try:
# #         return await future
# #     finally:
# #         h.cancel()
#
#
# # event loop API
#
# import asyncio
#
# # 创建了一个新的事件循环。事件循环作用：负责调度和执行异步任务（async/await 代码、回调函数、Future 等）
# # 处理I/O事件（如网络请求、文件读写等）
# loop = asyncio.new_event_loop()
#
# # 设置为当前线程的事件循环。把这个新创建的 loop 设置为当前线程的默认事件循环（如果不设置，get_event_loop() 会报错）。
# asyncio.set_event_loop(loop)
# # loop.time()：返回事件循环内部维护的单调时钟时间（单位：秒）
# # 这个时间从事件循环启动（run_forever 或 run_until_complete）开始计算，不是现实世界的挂钟时间。
# # 这里打印的是 初始时间（通常是 0 或一个很小的浮点数）。
# print(loop.time())
#
# # loop.call_soon(callback) 安排回调函数 callback "尽快"执行 (在下一次事件循环迭代时调用）。迭代时调用）。
# # 不保证立即执行，但优先级高于 call_later/call_at
# # 输出：通常是第一个打印，在call_later/call_at之前
# loop.call_soon(lambda: print("Hello, world! at call_soon"))
# # loop.call_later(delay, callback)
# # 在delay秒后执行 callback。delay 从loop.run_forever() 开始计算，不是从当前时间计算。
# loop.call_later(1, lambda: print("Hello, world! at call_later"))
# # loop.call_at(when, callback)。在事件循环时间 when 时调用 callback。
# # when 是 loop.time() + 延迟时间。
# # 这里的loop.time() + 1 和 call_later(1,...) 效果相同。
# loop.call_at(loop.time() + 1, lambda: print("Hello, world! at call_at"))
# loop.call_later(2, loop.stop)
# # 强制停止事件循环的运行（run_forever 退出）。
# # 死循环。只有在2秒后，loop。stop被调用，event loop才会停止。
# loop.run_forever()
#
# # 正因为event loop提供了call_soon、call_later等功能，我们有了在未来某个时刻执行函数的机会。
# # 为了观察这个函数是否被执行了，我们就有了future的概念；为了控制（例如，取消）这个函数的执行，我们有了handle的概念：
# #

from core.llm_manager import get_llm_manager

llm = get_llm_manager()
print(llm.list_providers())

# messages = [HumanMessage(
    # content="python中多线程和协程是什么呀？语法怎么写？有什么区别？能不能给写一些代码示例？尽量用通俗易懂和举例子、做对比的方式进行讲解。"),
    #         SystemMessage(
    #             content="你是一个开发的专家，尤其是在AI编程领域有非常丰富的经验，你需要非常细致的将我的问题进行回答。而且需要配合上一些代码示例进行讲解回答")]  # ✅ 标准消息格式
prompt : str = "python中多线程和协程是什么呀？语法怎么写？有什么区别？能不能给写一些代码示例？尽量用通俗易懂和举例子、做对比的方式进行讲解。"
system_promet : str = "你是一个开发的专家，尤其是在AI编程领域有非常丰富的经验，你需要非常细致的将我的问题进行回答。而且需要配合上一些代码示例进行讲解回答"
res = llm.agenerate(prompt, system_promet)

# print(res)

import asyncio
# async def run_stream():
#     llm = get_llm_manager()
#     prompt: str = "python中多线程和协程是什么呀？语法怎么写？有什么区别？能不能给写一些代码示例？尽量用通俗易懂和举例子、做对比的方式进行讲解。"
#     system_promet: str = "你是一个开发的专家，尤其是在AI编程领域有非常丰富的经验，你需要非常细致的将我的问题进行回答。而且需要配合上一些代码示例进行讲解回答"
#
#     async for chunk in llm.agenerate(prompt, system_promet):
#         print(chunk, end="", flush=True) # 实时打印流式结果
#
# asyncio.run(run_stream())

# async def run_once():
#     llm = get_llm_manager()
#     prompt: str = "python中多线程和协程是什么呀？语法怎么写？有什么区别？能不能给写一些代码示例？尽量用通俗易懂和举例子、做对比的方式进行讲解。"
#     system_promet: str = "你是一个开发的专家，尤其是在AI编程领域有非常丰富的经验，你需要非常细致的将我的问题进行回答。而且需要配合上一些代码示例进行讲解回答"
#
#     # 直接 await agenerate（）
#     result = await llm.agenerate(prompt, system_promet)
#     print(result)
#
# asyncio.run(run_once())


async def run_stream():
    llm = get_llm_manager()
    prompt: str = "python中多线程和协程是什么呀？语法怎么写？有什么区别？能不能给写一些代码示例？尽量用通俗易懂和举例子、做对比的方式进行讲解。"
    system_promet: str = "你是一个开发的专家，尤其是在AI编程领域有非常丰富的经验，你需要非常细致的将我的问题进行回答。而且需要配合上一些代码示例进行讲解回答"

    async for chunk in llm.astream(prompt, system_promet):
        print(chunk, end="", flush=True)

asyncio.run(run_stream())