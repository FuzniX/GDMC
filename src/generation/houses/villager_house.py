from dataclasses import dataclass
from random import choice

from gdpc.block import Block
from gdpc.geometry import placeCuboid
from gdpc.transform import Transform
from matplotlib import patches
from matplotlib.axes import Axes

from src.utils import get_palette_for_biome

from .house import House


@dataclass
class VillagerHouse(House):
    """
    Japanese-style villager house.
    """

    def __post_init__(self) -> None:
        self.width = 17
        self.depth = 17
        self.halfWidth = 8
        self.halfDepth = 8

        biome_string = self.editor.getBiome((self.x, self.y, self.z))
        palette = get_palette_for_biome(biome_string)

        self.base_stone = self.transformed(*palette["vil_base_stone"])
        self.base_stone_alt = self.transformed(*palette["vil_base_stone_alt"])
        self.porch_slab = self.transformed(*palette["vil_porch_slab"])

        self.pillar_wood = self.transformed(*palette["vil_pillar_wood"])
        self.beam_wood = self.transformed(*palette["vil_beam_wood"])
        self.wall_wood = self.transformed(*palette["vil_wall_wood"])

        self.shoji_block = self.transformed(*palette["vil_shoji_block"])
        self.shoji_trapdoor = self.transformed(*palette["vil_shoji_trapdoor"])

        self.roof_outline_stair = self.transformed(*palette["vil_roof_outline_stair"])
        self.roof_outline_slab = self.transformed(*palette["vil_roof_outline_slab"])
        self.roof_outline_block = self.transformed(*palette["vil_roof_outline_block"])

        self.roof_fill_stair = self.transformed(*palette["vil_roof_fill_stair"])
        self.roof_fill_slab = self.transformed(*palette["vil_roof_fill_slab"])
        self.roof_block = self.transformed(*palette["vil_roof_block"])

    def _get_bottom_y(self, lx: int, lz: int, house_tf: Transform) -> int:
        """Calculate the local terrain depth under a specific coordinate."""
        try:
            hm = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
        except (KeyError, AttributeError):
            hm = self.editor.worldSlice.heightmaps["WORLD_SURFACE"]

        global_pos = house_tf.apply((lx, 0, lz))
        sx, sz = hm.shape

        if 0 <= global_pos.x < sx and 0 <= global_pos.z < sz:
            ground_y = hm[global_pos.x, global_pos.z]
            return min(-1, ground_y - self.y - 1)

        return -1

    def build(self) -> "VillagerHouse":
        super().build()

        with self.editor.pushTransform(
            Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        ):
            placeCuboid(self.editor, (0, 1, 0), (16, 20, 16), Block("air"))

            self.build_foundation()
            self.build_story(2, 2, 14, 14, 3, is_ground=True)
            self.build_skirt_roof()
            self.build_story(4, 4, 12, 12, 8, is_ground=False)
            self.build_main_roof()
            self.build_decorations()
        return self

    def build_foundation(self) -> None:
        """Build foundations"""
        house_tf = Transform(
            translation=(self.x, self.y, self.z), rotation=self.rotation
        )

        for x in range(1, 16):
            for z in range(1, 16):
                # Deep pillars to the ground
                bottom = self._get_bottom_y(x, z, house_tf)
                for y_f in range(bottom, 1):
                    blk = self.base_stone if (x + z) % 2 == 0 else self.base_stone_alt
                    self.editor.placeBlock((x, y_f, z), choice(blk))

                if x == 1 or x == 15 or z == 1 or z == 15:
                    # Stone ring and porch
                    self.editor.placeBlock((x, 1, z), choice(self.base_stone))
                    selected_slab = choice(self.porch_slab)
                    b_slab = Block(selected_slab.id, {"type": "bottom"})
                    self.editor.placeBlock((x, 2, z), b_slab)
                else:
                    # Inner floor
                    self.editor.placeBlock((x, 1, z), choice(self.base_stone_alt))
                    self.editor.placeBlock((x, 2, z), Block("dark_oak_planks"))

        # Front entry stairs
        for x in [7, 8, 9]:
            stair = Block("stone_brick_stairs", {"facing": "south"})
            self.editor.placeBlock((x, 1, 0), stair)
            self.editor.placeBlock((x, 2, 0), Block("air"))

    def build_story(self, x1, z1, x2, z2, y_base, is_ground=False) -> None:
        pillars = [2, 6, 10, 14] if is_ground else [4, 8, 12]

        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                is_edge_x = x == x1 or x == x2
                is_edge_z = z == z1 or z == z2

                if not (is_edge_x or is_edge_z):
                    continue

                # Corners are always pillars
                if x in (x1, x2) and z in (z1, z2):
                    self._pillar_col(x, z, y_base, 4)
                    continue

                if is_edge_z:
                    face = "north" if z == z1 else "south"
                    out_z = z - 1 if z == z1 else z + 1
                    if x in pillars:
                        self._pillar_col(x, z, y_base, 4)
                        btn = Block("dark_oak_button", {"facing": face})
                        self.editor.placeBlock((x, y_base + 3, out_z), btn)
                        self.editor.placeBlock((x, y_base, out_z), btn)
                    else:
                        is_door = is_ground and x in [7, 8, 9] and z == z1
                        self._wall_col(x, z, y_base, face, out_z, "x", is_door)

                elif is_edge_x:
                    face = "west" if x == x1 else "east"
                    out_x = x - 1 if x == x1 else x + 1
                    if z in pillars:
                        self._pillar_col(x, z, y_base, 4)
                        btn = Block("dark_oak_button", {"facing": face})
                        self.editor.placeBlock((out_x, y_base + 3, z), btn)
                        self.editor.placeBlock((out_x, y_base, z), btn)
                    else:
                        self._wall_col(x, z, y_base, face, out_x, "z", False)

    def _pillar_col(self, x, z, y, h) -> None:
        for i in range(h):
            self.editor.placeBlock((x, y + i, z), choice(self.pillar_wood))

    def _wall_col(self, x, z, y, face, out_coord, axis, door=False) -> None:
        # Wood sill and top beam
        selected_wall = choice(self.wall_wood)
        selected_beam = choice(self.beam_wood)
        self.editor.placeBlock((x, y, z), Block(selected_wall.id, {"axis": "y"}))
        self.editor.placeBlock((x, y + 3, z), Block(selected_beam.id, {"axis": axis}))

        if door:
            db = Block("cherry_door", {"half": "lower", "facing": face})
            self.editor.placeBlock((x, y + 1, z), db)
        else:
            self.editor.placeBlock((x, y + 1, z), choice(self.shoji_block))
            self.editor.placeBlock((x, y + 2, z), choice(self.shoji_block))

            rx = out_coord if axis == "z" else x
            rz = out_coord if axis == "x" else z

            if (x + z) % 2 == 0:
                selected_shoji_td = choice(self.shoji_trapdoor)
                tb = Block(
                    selected_shoji_td.id,
                    {"facing": face, "half": "bottom", "open": "true"},
                )
                self.editor.placeBlock((rx, y + 1, rz), tb)
            else:
                self.editor.placeBlock((rx, y + 1, rz), Block("cherry_fence"))
                self.editor.placeBlock((rx, y + 2, rz), Block("cherry_fence"))

    def build_skirt_roof(self) -> None:
        self._build_roof_ring(0, 16, 0, 16, 6, "slab")
        self._build_roof_ring(1, 15, 1, 15, 6, "stair")
        self._build_roof_ring(2, 14, 2, 14, 7, "stair")

        for x in range(3, 14):
            for z in range(3, 14):
                self.editor.placeBlock((x, 7, z), choice(self.roof_block))

    def build_main_roof(self) -> None:
        """Build main roof"""
        y = 11
        self._build_roof_ring(2, 14, 2, 14, y, "slab")
        self._build_roof_ring(3, 13, 3, 13, y, "stair")
        self._build_roof_ring(4, 12, 4, 12, y + 1, "stair")

        y += 2
        # Gable construction
        for dz in range(4):
            cur_y = y + dz
            z1 = 5 + dz
            z2 = 11 - dz
            if z1 > z2:
                break

            # North / South slopes
            for x in range(5, 12):
                bn = self.roof_outline_stair if x in (5, 11) else self.roof_fill_stair
                bs = self.roof_outline_stair if x in (5, 11) else self.roof_fill_stair
                self.editor.placeBlock(
                    (x, cur_y, z1), Block(choice(bn).id, {"facing": "south"})
                )
                self.editor.placeBlock(
                    (x, cur_y, z2), Block(choice(bs).id, {"facing": "north"})
                )
                self.editor.placeBlock((x, cur_y - 1, z1), choice(self.roof_block))
                self.editor.placeBlock((x, cur_y - 1, z2), choice(self.roof_block))

            # East / West half-timbered walls
            for x in [5, 11]:
                for z_fill in range(z1 + 1, z2):
                    self.editor.placeBlock((x, cur_y, z_fill), choice(self.shoji_block))
                    if dz == 0 and z_fill == 8:
                        self.editor.placeBlock(
                            (x, cur_y, z_fill), Block("dark_oak_fence")
                        )
                    if dz == 1 and z_fill in (7, 9):
                        self.editor.placeBlock(
                            (x, cur_y, z_fill), Block("dark_oak_fence")
                        )

        # Ridge beam
        cur_y = 16
        for x in range(4, 13):
            selected_outline_slab = choice(self.roof_outline_slab)
            slab = Block(selected_outline_slab.id, {"type": "bottom"})
            self.editor.placeBlock((x, cur_y, 8), slab)
            self.editor.placeBlock((x, cur_y - 1, 8), choice(self.roof_block))

        # Ridge swoops
        e_stair = Block(choice(self.roof_outline_stair).id, {"facing": "west"})
        w_stair = Block(choice(self.roof_outline_stair).id, {"facing": "east"})
        self.editor.placeBlock((3, cur_y, 8), e_stair)
        self.editor.placeBlock((13, cur_y, 8), w_stair)

    def _build_roof_ring(self, x1, x2, z1, z2, y, part) -> None:
        """Helper to build a sloped ring with corners swooping upward."""
        for x in range(x1, x2 + 1):
            for z in range(z1, z2 + 1):
                if not (x == x1 or x == x2 or z == z1 or z == z2):
                    continue

                dist_corn = min(x - x1, x2 - x) + min(z - z1, z2 - z)
                stair = (
                    self.roof_outline_stair if dist_corn < 2 else self.roof_fill_stair
                )
                slab = self.roof_outline_slab if dist_corn < 2 else self.roof_fill_slab

                if part == "slab":
                    selected_slab = choice(slab)
                    self.editor.placeBlock(
                        (x, y, z), Block(selected_slab.id, {"type": "bottom"})
                    )
                    # Rafters underneath
                    if x == x1:
                        r_face = "west"
                    elif x == x2:
                        r_face = "east"
                    elif z == z1:
                        r_face = "north"
                    else:
                        r_face = "south"
                    cf = Block("campfire", {"lit": "false", "facing": r_face})
                    self.editor.placeBlock((x, y - 1, z), cf)
                elif part == "stair":
                    if x == x1:
                        facing = "east"
                    elif x == x2:
                        facing = "west"
                    elif z == z1:
                        facing = "south"
                    else:
                        facing = "north"
                    selected_stair = choice(stair)
                    self.editor.placeBlock(
                        (x, y, z), Block(selected_stair.id, {"facing": facing})
                    )

        # Upward corner swoops
        if part == "slab":
            for cx, cz in [(x1, z1), (x2, z1), (x1, z2), (x2, z2)]:
                selected_block = choice(self.roof_outline_block)
                slab_t = Block(selected_block.id)
                self.editor.placeBlock((cx, y, cz), slab_t)

    def build_decorations(self) -> None:
        # Hanging lanterns at the 4 corners of the lower roof
        for cx, cz in [(0, 0), (16, 0), (0, 16), (16, 16)]:
            self.editor.placeBlock((cx, 4, cz), Block("iron_chain"))
            self.editor.placeBlock((cx, 3, cz), Block("lantern", {"hanging": "true"}))

    def plot(self, ax: Axes) -> "VillagerHouse":
        rect = patches.Rectangle(
            (
                self.x + (0 if self.rotation in [0, 3] else 3),
                self.z + (0 if self.rotation in [0, 1] else 3),
            ),
            self.width + 3,
            self.depth + 3,
            edgecolor="green",
            fill=False,
            alpha=0.6,
            angle=self.rotation * 90,
        )
        ax.add_patch(rect)
        return self
