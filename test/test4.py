import os
import socks
import socket
from langchain_google_community import GoogleSearchAPIWrapper
from langchain_core.tools import Tool

# 1. Clash代理核心配置
os.environ["ALL_PROXY"] = "socks5h://127.0.0.1:7890"
socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", 7890)
socket.socket = socks.socksocket

# 2. 修复DNS解析
original_getaddrinfo = socket.getaddrinfo
def new_getaddrinfo(*args):
    try:
        return original_getaddrinfo(*args)
    except:
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, '', (args[0], args[1]))]
socket.getaddrinfo = new_getaddrinfo

# 3. 创建搜索实例（新版API的正确用法）
search = GoogleSearchAPIWrapper(
    google_api_key="AIzaSyBPGoydrz2XndeSITY3unrFO_i_nKt5QXI",
    google_cse_id="1422961cbc2734ba1"
)

def top3_results(query):
    return search.results(query, 3)

tool = Tool(
    name="Google Search",
    description="Search Google for recent results.",
    func=top3_results,
)

# 4. 通过环境变量设置代理（推荐方式）
os.environ["HTTP_PROXY"] = "socks5h://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "socks5h://127.0.0.1:7890"

# 5. 测试查询
try:
    result = tool.run("2022年诺贝尔物理学奖获得者?")
    # result = search.run("2022年诺贝尔物理学奖获得者?")
    print("✅ 搜索成功:")
    print(result)
except Exception as e:
    print(f"❌ 错误: {type(e).__name__}")
    print(str(e)[:500])
