import aiohttp
import asyncio
import time
import statistics
from concurrent.futures import ProcessPoolExecutor
from task2 import cpu_bound_task

async def measure_request_time():
    async with aiohttp.ClientSession() as session:
        start = time.time()
        async with session.get('http://localhost:8000') as response:
            await response.text()
        return time.time() - start

async def load_test(num_requests):
    tasks = [measure_request_time() for _ in range(num_requests)]
    results = await asyncio.gather(*tasks)
    return results

def run_direct_test(x):
    # Test without ProcessPoolExecutor
    return cpu_bound_task(x)

async def main():
    NUM_REQUESTS = 500
    
    print("\n=== Testing with ProcessPoolExecutor (GIL Mitigation) ===")
    print(f"Sending {NUM_REQUESTS} concurrent requests...")
    
    # Test with ProcessPoolExecutor
    times = await load_test(NUM_REQUESTS)
    
    throughput = NUM_REQUESTS / sum(times)
    avg_time = statistics.mean(times)
    
    print(f"\nResults with GIL Mitigation:")
    print(f"Total time: {sum(times):.2f} seconds")
    print(f"Average response time: {avg_time:.2f} seconds")
    print(f"Throughput: {throughput:.2f} requests/second")
    
    print("\n=== Testing without ProcessPoolExecutor ===")
    # Test without ProcessPoolExecutor
    start = time.time()
    for _ in range(NUM_REQUESTS):
        run_direct_test(10)
    total_time = time.time() - start
    
    print(f"\nResults without GIL Mitigation:")
    print(f"Total time: {total_time:.2f} seconds")
    print(f"Average time per request: {total_time/NUM_REQUESTS:.2f} seconds")
    print(f"Throughput: {NUM_REQUESTS/total_time:.2f} requests/second")

if __name__ == '__main__':
    print("Starting throughput tests...")
    print("Make sure the server (task2.py) is running first!")
    asyncio.run(main())
