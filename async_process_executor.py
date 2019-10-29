from asyncio import get_event_loop, sleep
from collections import namedtuple
from multiprocessing import Pool, cpu_count


Task = namedtuple("Task", ["function", "args"])


class AsyncProcessExecutor:
    """
    Execute tasks in processes and return its results asynchonously
    """

    def __init__(self, workers=cpu_count(), initializer=None, sleep_time=0.01):
        self.workers = workers
        self.initializer = initializer
        self.sleep_time = sleep_time

    def run(self):
        loop = get_event_loop()
        loop.run_until_complete(self.execute())

    async def tasks(self):
        raise NotImplementedError(
            "Method tasks of AsyncProcessExecutor must be overwritten"
        )

    async def process(self, result):
        raise NotImplementedError(
            "Method tasks of AsyncProcessExecutor must be overwritten"
        )

    async def close(self):
        pass

    async def execute(self):
        finished, has_more_tasks = False, True
        tasks = self.tasks()
        tasks_async_generator = tasks.__aiter__()

        with Pool(self.workers, initializer=self.initializer) as pool:
            results = []
            while not finished:
                for result in results:
                    if result.ready():
                        await self.process(result.get())
                        results.remove(result)
                for _ in range(self.workers - len(results)):
                    try:
                        task = await tasks_async_generator.__anext__()
                    except StopAsyncIteration:
                        has_more_tasks = False
                    else:
                        results.append(pool.apply_async(task.function, task.args))
                if not has_more_tasks and not results:
                    finished = True
                await sleep(self.sleep_time)
        await self.close()


if __name__ == "__main__":

    def my_task(task_number):
        import random
        import time

        sleep_time = random.randint(1, 100) / 10
        time.sleep(sleep_time)
        return task_number, sleep_time

    class MyTaskExecutor(AsyncProcessExecutor):
        async def tasks(self):
            for task_number in range(20):
                yield Task(function=my_task, args=(task_number,))
                print(f"Task #{task_number} consumed")

        async def process(self, result):
            task_number, sleep_time = result
            print(f"Task #{task_number} completed (sleep_time={sleep_time})")

    workers = 4
    print(f"Starting async task executor with {workers} workers.")
    MyTaskExecutor(workers=workers).run()
