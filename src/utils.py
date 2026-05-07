import traceback
from random import random
from typing import Callable

from gdpc import Editor


def ingame_exception(editor: Editor, e: Exception) -> None:
    """
    Prints an exception message in Minecraft
    :param editor: The editor that interacts with Minecraft
    :param e: The exception that occurred
    :return: None
    """
    traceback.print_exc()
    editor.runCommand('tellraw @a {"text": "Error: ' + str(e) + '", "color": "red"}')


def probability(p: float) -> bool:
    return random() < p


def do_with_probability[T](
    p: float, function: Callable[..., T]
) -> tuple[T | None, bool]:
    if probability(p):
        return function(), True
    return None, False
