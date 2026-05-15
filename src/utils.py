import traceback
from random import random, shuffle
from typing import Callable

from gdpc.block import Block
from gdpc.editor import Editor


def ingame_print(editor: Editor, text: str) -> None:
    """
    Prints a message in Minecraft
    :param editor: The editor that interacts with Minecraft
    :param text: The message to print
    :return: None
    """
    editor.runCommand(f'tellraw @a {{ "text": "{text}", "color": "white" }}')


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


def mix(specs: list[tuple[Block, int]]) -> list[Block]:
    """
    Creates a list of blocks respecting the proportions given.
    """
    mixed_list = [block for block, proportion in specs for _ in range(proportion)]
    shuffle(mixed_list)

    return mixed_list
