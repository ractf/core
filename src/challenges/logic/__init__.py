"""A package of methods and classes containing logic specific to the challenges app."""

from typing import Optional

from challenge import models


def get_file_path(file: "models.File", file_name: str) -> str:
    """Given a file model and the relevant root filename, return the file path."""
    return f"{file.challenge.pk}/{file.md5}/{file_name}"


def evaluate_rpn(requirements: Optional[str], solves: list[int]) -> bool:
    """
    Parse challenge requirements encoded in Reverse Polish Notation.

    Examples of RPN-encoded requirements include:

    >>> evaluate_rpn("1 2 OR", [9, 10])  # Challenges 1 or 2 are solved
    False
    >>> evaluate_rpn("3 4 AND", [3, 4])  # Challenges 3 and 4 are solved
    True
    """
    state = []

    if not requirements:
        return True

    for requirement in requirements.split():
        if requirement.isdigit():
            state.append(int(requirement) in solves)
        elif requirement == "OR":
            if len(state) >= 2:
                a, b = state.pop(), state.pop()
                state.append(a or b)
        elif requirement == "AND":
            if len(state) >= 2:
                a, b = state.pop(), state.pop()
                state.append(a and b)

    if not state:
        return False

    return bool(state[0])
