"""
Asynchronous Task Queue Module

Provides a ThreadPoolExecutor-based task queue for running background tasks
such as thumbnail generation. Handles task submission, tracking, and cleanup.
"""

import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, Optional, Set

# Configure logger
logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """Task execution status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class TaskInfo:
    """Information about a submitted task."""
    task_id: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class TaskManager:
    """
    Manages asynchronous task execution using ThreadPoolExecutor.

    Features:
    - ThreadPoolExecutor with configurable max workers
    - Task status tracking
    - Automatic cleanup of completed tasks
    - Error handling and logging

    Usage:
        task_manager = TaskManager(max_workers=3)
        task_id = task_manager.submit_task(my_function, arg1, arg2)
        info = task_manager.get_task_status(task_id)
    """

    def __init__(self, max_workers: int = 3):
        """
        Initialize the task manager.

        Args:
            max_workers: Maximum number of worker threads (default: 3)
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="thumbnail_worker_"
        )
        self._tasks: Dict[str, TaskInfo] = {}
        self._futures: Dict[str, Future] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = 300  # 5 minutes
        self._last_cleanup = time.time()

        logger.info(f"TaskManager initialized with {max_workers} workers")

    def submit_task(
        self,
        fn: Callable,
        *args,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for asynchronous execution.

        Args:
            fn: Function to execute
            *args: Positional arguments for the function
            task_id: Optional custom task ID (auto-generated if not provided)
            metadata: Optional metadata to store with the task
            **kwargs: Keyword arguments for the function

        Returns:
            str: Task ID for tracking
        """
        # Generate task ID if not provided
        if task_id is None:
            task_id = str(uuid.uuid4())

        # Create task info
        task_info = TaskInfo(
            task_id=task_id,
            status=TaskStatus.PENDING,
            created_at=datetime.utcnow(),
            metadata=metadata or {}
        )

        with self._lock:
            self._tasks[task_id] = task_info

        # Submit to executor
        future = self.executor.submit(
            self._execute_task,
            task_id,
            fn,
            *args,
            **kwargs
        )

        with self._lock:
            self._futures[task_id] = future

        # Add completion callback
        future.add_done_callback(
            lambda f, tid=task_id: self._task_completed(tid, f)
        )

        logger.debug(f"Task {task_id} submitted: {fn.__name__}")
        return task_id

    def _execute_task(
        self,
        task_id: str,
        fn: Callable,
        *args,
        **kwargs
    ) -> Any:
        """
        Execute the task and update status.

        This runs in the worker thread.
        """
        with self._lock:
            if task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.RUNNING
                self._tasks[task_id].started_at = datetime.utcnow()

        logger.info(f"Task {task_id} started: {fn.__name__}")

        try:
            result = fn(*args, **kwargs)
            logger.info(f"Task {task_id} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}", exc_info=True)
            raise

    def _task_completed(self, task_id: str, future: Future) -> None:
        """
        Handle task completion callback.

        Updates task status based on the future result.
        """
        with self._lock:
            if task_id not in self._tasks:
                return

            task_info = self._tasks[task_id]
            task_info.completed_at = datetime.utcnow()

            try:
                if future.cancelled():
                    task_info.status = TaskStatus.CANCELLED
                    task_info.error = "Task was cancelled"
                elif future.exception():
                    task_info.status = TaskStatus.FAILED
                    task_info.error = str(future.exception())
                else:
                    task_info.status = TaskStatus.COMPLETED
                    task_info.result = future.result()
            except Exception as e:
                task_info.status = TaskStatus.FAILED
                task_info.error = f"Error retrieving result: {e}"

            # Clean up future reference
            if task_id in self._futures:
                del self._futures[task_id]

        # Trigger cleanup if needed
        self._maybe_cleanup()

    def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """
        Get the current status of a task.

        Args:
            task_id: Task ID to look up

        Returns:
            TaskInfo if found, None otherwise
        """
        with self._lock:
            return self._tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        """
        Attempt to cancel a pending or running task.

        Args:
            task_id: Task ID to cancel

        Returns:
            bool: True if cancelled, False if not found or already completed
        """
        with self._lock:
            if task_id not in self._futures:
                return False

            future = self._futures[task_id]
            cancelled = future.cancel()

            if cancelled and task_id in self._tasks:
                self._tasks[task_id].status = TaskStatus.CANCELLED
                self._tasks[task_id].completed_at = datetime.utcnow()

            return cancelled

    def _maybe_cleanup(self) -> None:
        """
        Clean up old completed tasks if cleanup interval has passed.
        """
        current_time = time.time()
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        self._cleanup_completed_tasks()
        self._last_cleanup = current_time

    def _cleanup_completed_tasks(self, max_age_seconds: int = 3600) -> int:
        """
        Remove old completed tasks from memory.

        Args:
            max_age_seconds: Maximum age of completed tasks to keep

        Returns:
            int: Number of tasks removed
        """
        cutoff = datetime.utcnow().timestamp() - max_age_seconds
        to_remove: Set[str] = set()

        with self._lock:
            for task_id, task_info in self._tasks.items():
                if task_info.status in (TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED):
                    if task_info.completed_at and task_info.completed_at.timestamp() < cutoff:
                        to_remove.add(task_id)

            for task_id in to_remove:
                del self._tasks[task_id]

        if to_remove:
            logger.debug(f"Cleaned up {len(to_remove)} completed tasks")

        return len(to_remove)

    def get_active_tasks(self) -> Dict[str, TaskInfo]:
        """
        Get all currently active (pending or running) tasks.

        Returns:
            Dict mapping task IDs to TaskInfo
        """
        with self._lock:
            return {
                task_id: task_info
                for task_id, task_info in self._tasks.items()
                if task_info.status in (TaskStatus.PENDING, TaskStatus.RUNNING)
            }

    def shutdown(self, wait: bool = True) -> None:
        """
        Shutdown the task manager and executor.

        Args:
            wait: Whether to wait for running tasks to complete
        """
        logger.info("Shutting down TaskManager")
        self.executor.shutdown(wait=wait)

        with self._lock:
            self._tasks.clear()
            self._futures.clear()


# Global task manager instance
_task_manager: Optional[TaskManager] = None
_lock = threading.Lock()


def get_task_manager(max_workers: int = 3) -> TaskManager:
    """
    Get or create the global task manager instance.

    Args:
        max_workers: Maximum number of worker threads

    Returns:
        TaskManager instance
    """
    global _task_manager

    with _lock:
        if _task_manager is None:
            _task_manager = TaskManager(max_workers=max_workers)
        return _task_manager


def submit_task(
    fn: Callable,
    *args,
    task_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    **kwargs
) -> str:
    """
    Submit a task to the global task manager.

    Convenience function that uses the global task manager instance.

    Args:
        fn: Function to execute
        *args: Positional arguments for the function
        task_id: Optional custom task ID
        metadata: Optional metadata to store with the task
        **kwargs: Keyword arguments for the function

    Returns:
        str: Task ID for tracking
    """
    manager = get_task_manager()
    return manager.submit_task(fn, *args, task_id=task_id, metadata=metadata, **kwargs)


def get_task_status(task_id: str) -> Optional[TaskInfo]:
    """
    Get the status of a task from the global task manager.

    Args:
        task_id: Task ID to look up

    Returns:
        TaskInfo if found, None otherwise
    """
    manager = get_task_manager()
    return manager.get_task_status(task_id)
