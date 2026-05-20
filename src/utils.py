import traceback
from random import random, shuffle
from typing import Callable

from gdpc.block import Block
from gdpc.editor import Editor

TREE_KEYWORDS = ["leaves", "log", "wood"]
BIOME_PALETTES: dict[str, dict[str, list[Block]]] = {
    "desert": {
        "foundation": [Block("smooth_sandstone"), Block("sandstone")],
        "pillar": [Block("cut_sandstone"), Block("chiseled_sandstone")],
        "wall": [Block("sandstone"), Block("smooth_sandstone")],
        "roof_stairs": [Block("sandstone_stairs"), Block("sandstone_stairs")],
        "roof_block": [Block("cut_sandstone"), Block("cut_sandstone")],
        "street": [Block("smooth_sandstone")],
    },
    "badlands": {
        "foundation": [Block("red_sandstone"), Block("chiseled_red_sandstone")],
        "pillar": [Block("terracotta"), Block("brown_terracotta")],
        "wall": [Block("orange_terracotta"), Block("yellow_terracotta")],
        "roof_stairs": [Block("red_sandstone_stairs"), Block("red_sandstone_stairs")],
        "roof_block": [Block("smooth_red_sandstone"), Block("smooth_red_sandstone")],
        "street": [Block("smooth_red_sandstone")],
    },
    "birch": {
        "foundation": [Block("stone_bricks"), Block("cracked_stone_bricks")],
        "pillar": [Block("stripped_birch_log"), Block("stripped_birch_log")],
        "wall": [Block("white_terracotta"), Block("bone_block")],
        "roof_stairs": [Block("birch_stairs"), Block("birch_stairs")],
        "roof_block": [Block("birch_planks"), Block("birch_planks")],
        "street": [Block("dirt_path")],
    },
    "dark_forest": {
        "foundation": [Block("cobblestone"), Block("mossy_cobblestone")],
        "pillar": [Block("stripped_dark_oak_log"), Block("stripped_dark_oak_log")],
        "wall": [Block("dark_oak_planks"), Block("spruce_planks")],
        "roof_stairs": [Block("dark_oak_stairs"), Block("dark_oak_stairs")],
        "roof_block": [Block("dark_oak_planks"), Block("dark_oak_planks")],
        "street": [Block("dirt_path")],
    },
    "spruce": {
        "foundation": [Block("cobblestone"), Block("mossy_cobblestone")],
        "pillar": [Block("stripped_spruce_log"), Block("stripped_spruce_log")],
        "wall": [Block("spruce_planks"), Block("mud_bricks")],
        "roof_stairs": [Block("spruce_stairs"), Block("spruce_stairs")],
        "roof_block": [Block("spruce_planks"), Block("spruce_planks")],
        "street": [Block("dirt_path")],
    },
    "snowy": {
        "foundation": [Block("stone_bricks"), Block("cobblestone")],
        "pillar": [Block("stripped_spruce_log"), Block("stripped_spruce_log")],
        "wall": [Block("snow_block"), Block("white_wool")],
        "roof_stairs": [Block("spruce_stairs"), Block("spruce_stairs")],
        "roof_block": [Block("spruce_planks"), Block("spruce_planks")],
        "street": [Block("stone_bricks")],
    },
    "swamp": {
        "foundation": [Block("mossy_cobblestone"), Block("mud_bricks")],
        "pillar": [Block("stripped_mangrove_log"), Block("stripped_mangrove_log")],
        "wall": [Block("mud_bricks"), Block("packed_mud")],
        "roof_stairs": [Block("mangrove_stairs"), Block("mangrove_stairs")],
        "roof_block": [Block("mangrove_planks"), Block("mangrove_planks")],
        "street": [Block("dirt_path")],
    },
    "ocean": {
        "foundation": [Block("prismarine_bricks"), Block("dark_prismarine")],
        "pillar": [Block("stripped_oak_log"), Block("stripped_oak_log")],
        "wall": [Block("mossy_stone_bricks"), Block("stone_bricks")],
        "roof_stairs": [Block("prismarine_stairs"), Block("prismarine_stairs")],
        "roof_block": [Block("prismarine_slabs"), Block("prismarine_slabs")],
        "street": [Block("stripped_oak_wood", {"axis": "y"})],
    },
    "default": {
        "foundation": [Block("stone_bricks"), Block("cracked_stone_bricks")],
        "pillar": [Block("stripped_oak_log"), Block("stripped_oak_log")],
        "wall": [Block("oak_planks"), Block("birch_planks")],
        "roof_stairs": [Block("oak_stairs"), Block("oak_stairs")],
        "roof_block": [Block("oak_planks"), Block("oak_planks")],
        "street": [Block("dirt_path")],
    },
}


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


def get_palette_for_biome(biome_id: str) -> dict:
    """Returns the matching block configuration based on sub-string lookups."""
    biome_id = biome_id.lower()
    if "desert" in biome_id:
        return BIOME_PALETTES["desert"]
    if "badlands" in biome_id or "eroded" in biome_id:
        return BIOME_PALETTES["badlands"]
    if "birch" in biome_id:
        return BIOME_PALETTES["birch"]
    if "dark_forest" in biome_id:
        return BIOME_PALETTES["dark_forest"]
    if "taiga" in biome_id or "pine" in biome_id or "spruce" in biome_id:
        return BIOME_PALETTES["spruce"]
    if "snowy" in biome_id or "ice" in biome_id or "frozen" in biome_id:
        return BIOME_PALETTES["snowy"]
    if "swamp" in biome_id or "mangrove" in biome_id:
        return BIOME_PALETTES["swamp"]
    if "ocean" in biome_id or "river" in biome_id or "beach" in biome_id:
        return BIOME_PALETTES["ocean"]

    return BIOME_PALETTES["default"]


class AllowedTimeExceededError(Exception):
    """
    Raised when the allowed time is exceeded.
    """
