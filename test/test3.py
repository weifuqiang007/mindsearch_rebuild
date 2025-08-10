
"""
我们需要在Google Cloud credential console (https://console.cloud.google.com/apis/credentials)中获取GOOGLE_API_KEY，
在Programmable Search Enginge (https://programmablesearchengine.google.com/controlpanel/create)中获取GOOGLE_CSE_ID，
"""

# GOOGLE_API_KEY = "-"
#
# GOOGLE_CSE_ID = ""
#
# import os
#
# from langchain.tools import Tool
# from langchain_google_community import GoogleSearchAPIWrapper
#
# search = GoogleSearchAPIWrapper(
#     google_api_key="-",
#     google_cse_id=""
# )
#
# def top3_results(query):
#     return search.results(query, 3)
#
#
# tool = Tool(
#     name="Google Search",
#     description="Search Google for recent results.",
#     func=top3_results,
# )
#
# print(tool.run("2022年诺贝尔物理学奖获得者?"))

from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.runnables import RunnablePassthrough, RunnableParallel, RunnableLambda
from langchain_core.tools import Tool

from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.runnables import RunnablePassthrough
from langchain_core.tools import Tool
import os

# 代理设置（确保你的代理可用）
os.environ["https_proxy"] = "http://127.0.0.1:7890"
print(f"代理状态: {os.getenv('https_proxy')}")

# 初始化搜索工具（只需一个实例）
search = GoogleSearchAPIWrapper(
    google_api_key="AIzaSyBPGoydrz2XndeSITY3unrFO_i_nKt5QXI",
    google_cse_id="1422961cbc2734ba1",
    requests_kwargs={"verify": False}
)

google_tool = Tool(
    name="google_search",
    description="Search Google for recent results",
    func=search.run,
)

# 正确的链式构造
chain = RunnablePassthrough() | google_tool

# 执行并打印结果（两种方式）

# 方式1：直接调用
queries = ["What is LangChain?", "What is an LLM?"]
results = [chain.invoke(q) for q in queries]  # 串行执行避免限速

for i, res in enumerate(results):
    print(f"\n=== 结果 {i+1} ===")
    print(res)

# 方式2：使用batch（需处理输入格式）
batch_results = chain.batch([{"query": q} for q in queries])
for i, res in enumerate(batch_results):
    print(f"\n=== Batch结果 {i+1} ===")
    print(res)






