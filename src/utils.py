import traceback
from random import random, shuffle
from typing import Callable

from gdpc.block import Block
from gdpc.editor import Editor

TREE_KEYWORDS = ["leaves", "log", "wood"]


class CustomEditor(Editor):
    def ingame_print(self, text: str) -> None:
        """
        Prints a message in Minecraft
        :param editor: The editor that interacts with Minecraft
        :param text: The message to print
        :return: None
        """
        self.runCommand(f'tellraw @a {{ "text": "{text}", "color": "white" }}')

    def ingame_exception(self, e: Exception) -> None:
        """
        Prints an exception message in Minecraft
        :param editor: The editor that interacts with Minecraft
        :param e: The exception that occurred
        :return: None
        """
        traceback.print_exc()
        self.runCommand('tellraw @a {"text": "Error: ' + str(e) + '", "color": "red"}')

    def is_tree_block(self, block_id: str) -> bool:
        """Check if a given block ID matches tree component keywords."""
        return any(key in block_id for key in TREE_KEYWORDS)

    def destroy_tree_flood_fill(self, start_pos: tuple[int, int, int]) -> None:
        """Vaporize an entire connected tree structure using a 3D Flood Fill."""
        queue = [start_pos]
        visited = {start_pos}
        neighbors = [
            (1, 0, 0),
            (-1, 0, 0),
            (0, 1, 0),
            (0, -1, 0),
            (0, 0, 1),
            (0, 0, -1),
        ]

        while queue:
            cx, cy, cz = queue.pop(0)
            block = self.getBlock((cx, cy, cz))
            assert block.id is not None

            if not self.is_tree_block(block.id):
                continue

            # Clear the tree block components
            self.placeBlock((cx, cy, cz), Block("air"))

            for dx, dy, dz in neighbors:
                neighbor_pos = (cx + dx, cy + dy, cz + dz)
                if neighbor_pos not in visited:
                    visited.add(neighbor_pos)
                    queue.append(neighbor_pos)

    def clean_vegetation_area(
        self,
        min_x: int,
        max_x: int,
        min_z: int,
        max_z: int,
        min_y: int,
        max_y: int,
    ) -> None:
        """Scan a specific 3D volume bounding box and vaporize trees."""
        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x):
                for z in range(min_z, max_z):
                    block = self.getBlock((x, y, z))
                    assert block.id is not None
                    if self.is_tree_block(block.id):
                        self.destroy_tree_flood_fill((x, y, z))


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


class AllowedTimeExceededError(Exception):
    """
    Raised when the allowed time is exceeded.
    """
