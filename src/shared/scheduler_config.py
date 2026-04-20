import logging
import time
from multiprocessing.pool import ThreadPool
from typing import Any, Callable

import schedule

log = logging.getLogger(__name__)


class Scheduler:
    """Simple scheduler class that holds all scheduled functions."""

    registered_tasks: list[dict[str, Any]] = []
    running: bool = True

    def __init__(self, num_workers: int = 100) -> None:
        self.pool = ThreadPool(processes=num_workers)

    def add(self, job: Any, *args: Any, **kwargs: Any) -> Callable[..., None]:
        def decorator(func: Callable[..., Any]) -> None:
            if not kwargs.get("name"):
                name = func.__name__
            else:
                name = kwargs.pop("name")

            self.registered_tasks.append(
                {"name": name, "func": func, "job": job.do(self.pool.apply_async, func)}
            )

        return decorator

    def remove(self, task: dict[str, Any]) -> None:
        schedule.cancel_job(task["job"])

    def start(self) -> None:
        log.info("Starting scheduler...")
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    def stop(self) -> None:
        log.debug("Stopping scheduler...")
        self.pool.close()
        self.running = False


scheduler = Scheduler()


def stop_scheduler(signum: int, frame: Any) -> None:
    scheduler.stop()
