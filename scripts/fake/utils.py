"""A set of classes and utility methods for use in the faker script."""

import sys
import time
from dataclasses import dataclass
from random import randint


@dataclass
class TimedLog:
    """A simple context manager for timing log events."""

    message: str
    ending: str = " "

    entry_time: float = 0.0

    @property
    def time_elapsed(self) -> float:
        """Get the time elapsed since the log was started."""
        return time.time() - self.entry_time

    def __enter__(self) -> None:
        """Start the timer and print a relevant log line."""
        self.entry_time = time.time()
        print(self.message, end=self.ending, flush=True, file=sys.stderr)

    def __exit__(self, *_) -> None:
        """Print out how long this context manager lasted for."""
        print(f"Done ({self.time_elapsed}s)")


def random_rpn_op(depth: int = 0) -> str:
    """Return a random set of unlock requirements."""
    depth += 1

    if depth > 4 or (randint(1, 4) < 3 and depth > 1):
        return str(randint(1, 1000))

    if randint(1, 2) == 1:
        return f"{random_rpn_op(depth)} {random_rpn_op(depth)} OR"
    else:
        return f"{random_rpn_op(depth)} {random_rpn_op(depth)} AND"
