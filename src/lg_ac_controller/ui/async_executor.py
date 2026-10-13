"""Executa corrotinas em um loop asyncio dedicado fora da thread Qt."""

from __future__ import annotations

import asyncio
import inspect
import threading
from collections.abc import Awaitable, Callable
from typing import Any

from PySide6.QtCore import QObject, Signal


class AsyncExecutor(QObject):
    """Bridge Qt/asyncio com um único loop persistente para o provedor."""

    completed = Signal(int, object)
    failed = Signal(int, str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._next_task_id = 0
        self._ready = threading.Event()
        self._closed = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._completed_results: dict[int, Any] = {}
        self._result_lock = threading.Lock()
        self._thread = threading.Thread(
            target=self._run_loop,
            name="lg-ac-asyncio",
            daemon=True,
        )
        self._thread.start()
        self._ready.wait()

    def submit(self, operation: Callable[[], Awaitable[Any]]) -> int:
        if self._closed or self._loop is None:
            raise RuntimeError("O executor assíncrono já foi encerrado.")

        self._next_task_id += 1
        task_id = self._next_task_id
        future = asyncio.run_coroutine_threadsafe(operation(), self._loop)

        def finish(completed_future: Any) -> None:
            try:
                result = completed_future.result()
            except Exception as exc:  # noqa: BLE001 - boundary for UI feedback
                self.failed.emit(task_id, str(exc))
            else:
                with self._result_lock:
                    self._completed_results[task_id] = result
                self.completed.emit(task_id, result)

        future.add_done_callback(finish)
        return task_id

    def close(self, cleanup: Callable[[], Awaitable[Any]] | None = None) -> None:
        if self._closed:
            return
        self._closed = True
        if self._loop is not None:
            async def drain_and_stop() -> None:
                current = asyncio.current_task()
                pending = [
                    task
                    for task in asyncio.all_tasks()
                    if task is not current and not task.done()
                ]
                if pending:
                    for task in pending:
                        task.cancel()
                    await asyncio.gather(*pending, return_exceptions=True)
                with self._result_lock:
                    completed_results = tuple(self._completed_results.values())
                    self._completed_results.clear()
                for result in completed_results:
                    close_result = getattr(result, "close", None)
                    if close_result is None:
                        continue
                    maybe_awaitable = close_result()
                    if inspect.isawaitable(maybe_awaitable):
                        await maybe_awaitable
                if cleanup is not None:
                    await cleanup()
                self._loop.stop()

            future = asyncio.run_coroutine_threadsafe(drain_and_stop(), self._loop)
            try:
                future.result(timeout=5)
            except Exception:
                try:
                    if not self._loop.is_closed():
                        self._loop.call_soon_threadsafe(self._loop.stop)
                except RuntimeError:
                    # The loop may have completed shutdown concurrently.
                    pass
        self._thread.join(timeout=5)

    def discard_completed(self, task_id: int) -> None:
        """Forget a result after the Qt side has consumed it."""

        with self._result_lock:
            self._completed_results.pop(task_id, None)

    def _run_loop(self) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self._loop = loop
        self._ready.set()
        loop.run_forever()
        loop.close()
