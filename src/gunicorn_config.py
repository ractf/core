"""
Configuration for our gunicorn workers.

Primarily used for marking workers as unresponsive for Prometheus.
"""

from prometheus_client import multiprocess


def child_exit(_, worker):
    """Mark this worker's process as dead once it exits."""
    multiprocess.mark_process_dead(worker.pid)
