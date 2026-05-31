from dataclasses import dataclass, field
from random import choice
from typing import TYPE_CHECKING, Sequence

from gdpc.block import Block
from gdpc.transform import Transform

from src.utils import get_palette_for_biome

from .house import House

if TYPE_CHECKING:
    from src.simulation.pirate import Pirate

TREASURY_THRESHOLDS: list[int] = [1000, 5000, 10000]


@dataclass
class PirateManor(House["Pirate"]):
    # specific attribute for the pagoda
    quartile: int = 1

    # calculated after init
    floors: int = field(init=False)

    def __post_init__(self):
        # ranges from 4 to 7 floors depending on pirate wealth
        self.floors = 3 + self.quartile

    @classmethod
    def from_pirates(cls, pirates: Sequence["Pirate"], x: int, y: int, z: int, rotation: int = 0) -> "PirateManor":
        """
        Calculate the size of the manor based on the pirate faction's shared treasury.
        The manor size scales through 4 quartiles to represent economic prosperity.
        """
        # Retrieve the shared treasury from the first pirate in the sequence
        total_treasury = getattr(pirates[0], "treasury", 0) if pirates else 0

        # Determine the size quartile (1 to 4) based on treasury thresholds
        quartile = 1
        for threshold in TREASURY_THRESHOLDS:
            if total_treasury >= threshold:
                quartile += 1
        
        # Clamp the quartile to a maximum of 4 to keep generation within limits
        quartile = min(quartile, 4)

        # Define building dimensions using a buffer margin for placement
        BUFFER = 3
        base_size = 19 + (quartile * 2)
        width = base_size + (BUFFER * 2)
        depth = base_size + (BUFFER * 2)
        height = 55

        # Assign the first pirate as the manor owner/player if available

        # Return a new instance with the calculated spatial parameters
        return cls(
            x=x, y=y, z=z, 
            rotation=rotation, 
            quartile=quartile, 
            width=width, 
            depth=depth, 
            height=height,
        )

    def get_door_pos(self) -> tuple[int, int]:
        # computes the global coordinates for the front entrance location
        tf = Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        pos = tf.apply((self.width // 2, 0, -1))
        return pos[0], pos[2]

    def _rotate_facing(self, facing: str) -> str:
        # shifts directional strings clockwise depending on manor rotation
        order = ["north", "east", "south", "west"]
        return order[(order.index(facing) + self.rotation) % 4]

    def build(self) -> "PirateManor":
        # main orchestration method to build the manor
        super().build()

        try:
            biome_string = self.editor.getBiome((self.x, self.y, self.z))
        except Exception:
            biome_string = "default"

        palette = get_palette_for_biome(biome_string)

        f_blocks = palette.get("manor_foundation", [Block("stone_bricks")])
        p_blocks = palette.get("manor_pillar", [Block("stripped_mangrove_log")])
        w_blocks = palette.get("manor_wall", [Block("white_concrete")])
        r_stairs = palette.get(
            "manor_roof_stairs", [Block("oxidized_cut_copper_stairs")]
        )
        r_slabs = palette.get("manor_roof_slab", [Block("oxidized_cut_copper_slab")])
        r_blocks = palette.get("manor_roof_block", [Block("oxidized_cut_copper")])
        floor_blocks = palette.get("manor_floor", [Block("smooth_sandstone")])
        t_blocks = palette.get("manor_timber", [Block("mangrove_fence")])
        self._door_block = palette.get("pirate_door", [Block("mangrove_door")])[0]
        self._trapdoor_id = palette.get("pirate_trapdoor", [Block("warped_trapdoor")])[0].id

        calculated_floors = 4 + self.quartile

        # calculate max height
        try:
            hm = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
        except KeyError:
            hm = self.editor.worldSlice.heightmaps["WORLD_SURFACE"]

        max_y = 0
        for x in range(-2, self.width + 2):
            for z in range(-2, self.depth + 2):
                global_pos = Transform(
                    translation=(self.x, 0, self.z), rotation=self.rotation
                ).apply((x, 0, z))
                if 0 <= global_pos.x < hm.shape[0] and 0 <= global_pos.z < hm.shape[1]:
                    h = hm[global_pos.x, global_pos.z]
                    if h > max_y:
                        max_y = h

        self.y = max_y

        with self.editor.pushTransform(
            Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        ):
            current_y = 0
            cx = self.width // 2
            cz = self.depth // 2

            self._build_adaptive_foundation(hm, f_blocks)
            self._build_stone_base(current_y, f_blocks)
            current_y += 1

            for floor_idx in range(calculated_floors):
                shrink = floor_idx * 2
                min_x, max_x = shrink, self.width - 1 - shrink
                min_z, max_z = shrink, self.depth - 1 - shrink

                # keep a minimum size for the top floors
                if (max_x - min_x) < 5 or (max_z - min_z) < 5:
                    min_x, max_x = cx - 3, cx + 3
                    min_z, max_z = cz - 3, cz + 3

                self._build_floor_level(
                    min_x,
                    max_x,
                    min_z,
                    max_z,
                    current_y,
                    floor_blocks,
                    t_blocks,
                    p_blocks,
                    w_blocks,
                )

                if floor_idx == 0:
                    self._build_random_door(
                        cx, cz, min_x, max_x, min_z, max_z, current_y, floor_blocks
                    )

                height_of_floor = 4
                roof_base_y = current_y + height_of_floor
                self._build_pagoda_roof(
                    min_x, max_x, min_z, max_z, roof_base_y, r_slabs, r_blocks, r_stairs
                )

                current_y = roof_base_y + 2

            self._build_sorin_top(cx, cz, current_y, p_blocks)

        return self

    def _build_adaptive_foundation(self, hm, f_blocks):
        # adaptive foundations
        for x in range(-2, self.width + 2):
            for z in range(-2, self.depth + 2):
                global_pos = Transform(
                    translation=(self.x, 0, self.z), rotation=self.rotation
                ).apply((x, 0, z))
                if 0 <= global_pos.x < hm.shape[0] and 0 <= global_pos.z < hm.shape[1]:
                    ground_y = hm[global_pos.x, global_pos.z]
                    for y in range(ground_y, self.y):
                        self.editor.placeBlock((x, y - self.y, z), choice(f_blocks))

    def _build_stone_base(self, current_y, f_blocks):
        # stone base
        for x in range(-1, self.width + 1):
            for z in range(-1, self.depth + 1):
                self.editor.placeBlock((x, current_y, z), choice(f_blocks))

    def _build_floor_level(
        self,
        min_x,
        max_x,
        min_z,
        max_z,
        current_y,
        floor_blocks,
        t_blocks,
        p_blocks,
        w_blocks,
    ):
        # floor blocks
        for x in range(min_x - 1, max_x + 2):
            for z in range(min_z - 1, max_z + 2):
                self.editor.placeBlock((x, current_y - 1, z), choice(floor_blocks))
                self.editor.placeBlock((x, current_y, z), choice(floor_blocks))

        # front facade
        for x in range(min_x, max_x + 1):
            if x == min_x:
                self.editor.placeBlock(
                    (x - 1, current_y + 1, min_z - 1), choice(t_blocks)
                )
            if x == max_x:
                self.editor.placeBlock(
                    (x + 1, current_y + 1, min_z - 1), choice(t_blocks)
                )
            self.editor.placeBlock((x, current_y + 1, min_z - 1), choice(t_blocks))
            self.editor.placeBlock(
                (x, current_y + 3, min_z - 1),
                Block(self._trapdoor_id, {"facing": "north", "half": "top", "open": "true"}),
            )

        # back facade
        for x in range(min_x, max_x + 1):
            if x == min_x:
                self.editor.placeBlock(
                    (x - 1, current_y + 1, max_z + 1), choice(t_blocks)
                )
            if x == max_x:
                self.editor.placeBlock(
                    (x + 1, current_y + 1, max_z + 1), choice(t_blocks)
                )
            self.editor.placeBlock((x, current_y + 1, max_z + 1), choice(t_blocks))
            self.editor.placeBlock(
                (x, current_y + 3, max_z + 1),
                Block(self._trapdoor_id, {"facing": "south", "half": "top", "open": "true"}),
            )

        # left facade
        for z in range(min_z, max_z + 1):
            if z == min_z:
                self.editor.placeBlock(
                    (min_x + 1, current_y + 1, z - 1), choice(t_blocks)
                )
            if z == max_z:
                self.editor.placeBlock(
                    (min_x + 1, current_y + 1, z + 1), choice(t_blocks)
                )
            self.editor.placeBlock((min_x - 1, current_y + 1, z), choice(t_blocks))
            self.editor.placeBlock(
                (min_x - 1, current_y + 3, z),
                Block(self._trapdoor_id, {"facing": "west", "half": "top", "open": "true"}),
            )

        # right facade
        for z in range(min_z, max_z + 1):
            if z == min_z:
                self.editor.placeBlock(
                    (max_x - 1, current_y + 1, z - 1), choice(t_blocks)
                )
            if z == max_z:
                self.editor.placeBlock(
                    (max_x - 1, current_y + 1, z + 1), choice(t_blocks)
                )
            self.editor.placeBlock((max_x + 1, current_y + 1, z), choice(t_blocks))
            self.editor.placeBlock(
                (max_x + 1, current_y + 3, z),
                Block(self._trapdoor_id, {"facing": "east", "half": "top", "open": "true"}),
            )

        # walls and details
        height_of_floor = 4
        for h in range(height_of_floor):
            y_pos = current_y + 1 + h
            for x in range(min_x, max_x + 1):
                for z in range(min_z, max_z + 1):
                    is_corner = (x == min_x or x == max_x) and (
                        z == min_z or z == max_z
                    )
                    is_edge = (x == min_x or x == max_x) or (z == min_z or z == max_z)

                    if is_corner:
                        self.editor.placeBlock((x, y_pos, z), choice(p_blocks))
                    elif is_edge:
                        self.editor.placeBlock((x, y_pos, z), choice(w_blocks))
                        self.editor.placeBlock((x, y_pos - 2, z), choice(w_blocks))

    def _build_random_door(
        self, cx, cz, min_x, max_x, min_z, max_z, current_y, floor_blocks
    ):
        # random door placement on ground floor
        local_facing = choice(["north", "east", "south", "west"])
        door_facing = self._rotate_facing(local_facing)
        door_block = self._door_block

        if local_facing == "north":
            door_x, door_z, air_x, air_z = cx, min_z, cx, min_z - 1
        elif local_facing == "south":
            door_x, door_z, air_x, air_z = cx, max_z, cx, max_z + 1
        elif local_facing == "west":
            door_x, door_z, air_x, air_z = min_x, cz, min_x - 1, cz
        else:  # east
            door_x, door_z, air_x, air_z = max_x, cz, max_x + 1, cz

        self.editor.placeBlock(
            (door_x, current_y + 1, door_z),
            Block(door_block.id, {"half": "lower", "facing": door_facing}),
        )
        self.editor.placeBlock(
            (door_x, current_y + 2, door_z),
            Block(door_block.id, {"half": "upper", "facing": door_facing}),
        )
        self.editor.placeBlock((door_x, current_y, door_z), choice(floor_blocks))

        self.editor.placeBlock((air_x, current_y + 1, air_z), Block("air"))
        self.editor.placeBlock((air_x, current_y + 2, air_z), Block("air"))

    def _build_pagoda_roof(
        self, min_x, max_x, min_z, max_z, roof_base_y, r_slabs, r_blocks, r_stairs
    ):
        # pagoda style roof
        for x in range(min_x - 2, max_x + 3):
            for z in range(min_z - 2, max_z + 3):
                is_outer_corner = (x == min_x - 2 or x == max_x + 2) and (
                    z == min_z - 2 or z == max_z + 2
                )
                if is_outer_corner:
                    self.editor.placeBlock((x, roof_base_y + 1, z), choice(r_slabs))
                    self.editor.placeBlock((x, roof_base_y, z), choice(r_blocks))
                elif (x == min_x - 2 or x == max_x + 2) or (
                    z == min_z - 2 or z == max_z + 2
                ):
                    self.editor.placeBlock((x, roof_base_y, z), choice(r_slabs))
                else:
                    self.editor.placeBlock((x, roof_base_y, z), choice(r_blocks))

        # roof slope
        for x in range(min_x - 1, max_x + 2):
            for z in range(min_z - 1, max_z + 2):
                if x == min_x - 1:
                    self.editor.placeBlock(
                        (x, roof_base_y + 1, z),
                        Block(r_stairs[0].id, {"facing": "east"}),
                    )
                elif x == max_x + 1:
                    self.editor.placeBlock(
                        (x, roof_base_y + 1, z),
                        Block(r_stairs[0].id, {"facing": "west"}),
                    )
                elif z == min_z - 1:
                    self.editor.placeBlock(
                        (x, roof_base_y + 1, z),
                        Block(r_stairs[0].id, {"facing": "south"}),
                    )
                elif z == max_z + 1:
                    self.editor.placeBlock(
                        (x, roof_base_y + 1, z),
                        Block(r_stairs[0].id, {"facing": "north"}),
                    )

    def _build_sorin_top(self, cx, cz, current_y, p_blocks):
        # sorin top
        self.editor.placeBlock((cx, current_y - 1, cz), choice(p_blocks))
        self.editor.placeBlock((cx, current_y, cz), Block("red_nether_brick_wall"))
        self.editor.placeBlock((cx, current_y + 1, cz), Block("lightning_rod"))

    def plot(self, ax) -> "PirateManor":
        # renders a purple outline representing the manor boundary on a matplotlib plot
        from matplotlib import patches

        x0, z0, x1, z1 = self.get_footprint()
        rect = patches.Rectangle(
            (x0, z0), x1 - x0, z1 - z0, edgecolor="purple", fill=False, alpha=0.8, lw=2
        )
        ax.add_patch(rect)
        return self