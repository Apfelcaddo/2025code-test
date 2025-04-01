# 2 High-Concurrency LLM Chat Service
# Task:
# ■ Write an asyncio service with a multiprocessing pool for
# CPU-bound tasks.
# ■ Measure throughput (requests/sec) with/without GIL mitigation.
# Deliverables:
# ■ Service code with concurrency tests.
# ■ Throughput metrics and mitigation strategy explanation.

# import the 'web' module from aiohttp, which helps create async web servers
from aiohttp import web
import os
# print cpu numbers
print(os.cpu_count()) # print the number of CPU cores available
import asyncio # import the asyncio library for event-loop based concurrency
from concurrent.futures import ProcessPoolExecutor # import ProcessPoolExecutor, which creates a pool of separate process to run CPU-bound tasks in parallel

# Step1: Define a CPU-bound function
# This function will be executed in a separate process to benefit from parallelism
def cpu_bound_task(x:int) -> int:
  '''simulate heavy computation
  '''
  total = 0
  for i in range(10_000_000):
    total += i % x
  return total

# Step2: Create a global process pool
# Each process has its own GIL, allowing true parallel CPU execution on multi-core systems
# 'max_workers = 4' means up to 4 worker processes
process_pool = ProcessPoolExecutor(max_workers = os.cpu_count() - 4)

# Step3: Define an async handler that offloads CPU-bound tasks to the process pool
async def handle_request(request):
    # Get the current event loop to schedule work in the executor
    loop = asyncio.get_running_loop()
    # Offload the CPU-bound function to a separate process via 'run_in_executor'
    result = await loop.run_in_executor(process_pool, cpu_bound_task, 10)
    # Return a simple response with the result of the computation
    return web.Response(text=f"Calculation result: {result}")

# Step4: create an instance of an aiohttp Application, which acts as the main entry point for refining routes and handlers
app = web.Application()
# add a route for GET requests on the path '/'
# whenever the server receives an HTTP GET request at '/', it will call the 'handle_request' function.
app.router.add_get('/', handle_request)

# Step5: run the app if executed as the main program
if __name__ == '__main__':
# start the aiohttp server on host 0.0.0.0 (all interfaces), port 8000.
  web.run_app(app, host='0.0.0.0', port=8000)