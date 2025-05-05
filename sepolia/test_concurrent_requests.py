import asyncio
import aiohttp
import time

# 目标URL
url = "http://127.0.0.1:5000/codes_by_eth_balance?page=1&page_size=20"
# 并发请求数
concurrency = 10

async def fetch(session, url, request_id):
    """发送单个请求并返回结果"""
    print(f"开始请求 {request_id}")
    start_time = time.time()
    try:
        async with session.get(url) as response:
            data = await response.text()
            elapsed = time.time() - start_time
            print(f"请求 {request_id} 完成，状态码: {response.status}, 耗时: {elapsed:.2f}秒")
            return data
    except Exception as e:
        elapsed = time.time() - start_time
        print(f"请求 {request_id} 失败: {str(e)}, 耗时: {elapsed:.2f}秒")
        return None

async def main():
    """主函数，发起多个并发请求"""
    print(f"开始执行 {concurrency} 个并发请求到 {url}")
    
    start_time = time.time()
    
    # 创建会话
    async with aiohttp.ClientSession() as session:
        # 创建任务列表
        tasks = [fetch(session, url, i+1) for i in range(concurrency)]
        
        # 等待所有任务完成
        results = await asyncio.gather(*tasks)
        
        # 统计成功的请求数
        success_count = sum(1 for r in results if r is not None)
        
    total_time = time.time() - start_time
    print(f"\n请求统计:")
    print(f"总请求数: {concurrency}")
    print(f"成功请求数: {success_count}")
    print(f"失败请求数: {concurrency - success_count}")
    print(f"总耗时: {total_time:.2f}秒")
    
if __name__ == "__main__":
    # 在Windows上需要使用这个事件循环策略
    if hasattr(asyncio, 'WindowsSelectorEventLoopPolicy'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main()) 