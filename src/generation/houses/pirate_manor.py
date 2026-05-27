from dataclasses import dataclass
from random import choice
from typing import TYPE_CHECKING, ClassVar, Sequence

from gdpc.block import Block
from gdpc.transform import Transform
from matplotlib import patches
from matplotlib.axes import Axes

from src.utils import get_palette_for_biome

from .house import BLOCK_PROPORTION, House

if TYPE_CHECKING:
    from src.simulation.pirate import Pirate

TREASURY_THRESHOLDS: list[int] = [10_000, 50_000, 200_000]
QUARTILE_CONFIG: dict[int, dict] = {
    1: {"floors": 2, "size": 13, "tower_radius": 2, "height": 5},
    2: {"floors": 3, "size": 17, "tower_radius": 2, "height": 5},
    3: {"floors": 4, "size": 21, "tower_radius": 3, "height": 5},
    4: {"floors": 5, "size": 25, "tower_radius": 3, "height": 5},
}


@dataclass
class PirateManor(House["Pirate"]):
    floors: int = 2
    tower_radius: int = 2

    floorBlockOptions: ClassVar[Sequence[Block]] = [
        Block("dark_oak_planks"),
        Block("spruce_planks"),
    ]

    def __post_init__(self) -> None:
        biome_string = self.editor.getBiome((self.x, self.y, self.z))
        palette = get_palette_for_biome(biome_string)

        self.foundation = self.transformed(*palette["manor_foundation"])
        self.pillar = self.transformed(*palette["manor_pillar"])
        self.wall = self.transformed(*palette["manor_wall"])
        self.floor = self.transformed(*palette["manor_floor"])

        self.roofStair = self.transformed(*palette["manor_roof_stairs"])[0]
        self.roofSlab = self.transformed(*palette["manor_roof_slab"])[0]
        self.roofBlock = self.transformed(*palette["manor_roof_block"])[0]
        self.floor_block = choice(self.floorBlockOptions)
        self.floors = max(2, min(5, self.floors))
        self.tower_radius = max(2, min(3, self.tower_radius))
        self.halfWidth = self.width // 2
        self.halfDepth = self.depth // 2
        self.foundation_height = 2
        self.floor_height = self.height

    @staticmethod
    def treasury_quartile(treasury: int) -> int:
        for i, threshold in enumerate(TREASURY_THRESHOLDS):
            if treasury < threshold:
                return i + 1
        return 4

    @classmethod
    def from_pirates(
        cls, pirates: "list[Pirate]", editor, x: int, y: int, z: int, rotation: int = 0
    ) -> "PirateManor":

        if not pirates:
            raise ValueError("No pirates present")

        player = pirates[0]

        treasury = player.simulation.pirate_money
        quartile = cls.treasury_quartile(treasury)
        config = QUARTILE_CONFIG[quartile]

        return cls(
            player=player,
            editor=editor,
            x=x,
            y=y,
            z=z,
            rotation=rotation,
            height=config["height"],
            depth=config["size"],
            width=config["size"],
            floors=config["floors"],
            tower_radius=config["tower_radius"],
        )

    @property
    def block_proportion(self) -> dict[str, int]:
        from src.simulation.enums import InfectionStatus

        alive = self.player.simulation.alive_pirates

        if not alive:
            return super().block_proportion
        if all(p.infection_status == InfectionStatus.Infected for p in alive):
            return BLOCK_PROPORTION[InfectionStatus.Infected]

        return BLOCK_PROPORTION[InfectionStatus.Susceptible]

    def safe_place(self, x: int, y: int, z: int, block: Block) -> None:
        try:
            self.editor.placeBlock((x, y, z), block)
        except Exception:
            pass

    def _tower_centers(self) -> list[tuple[int, int]]:
        r = self.tower_radius
        return [
            (-r, -r),
            (self.width - 1 + r, -r),
            (-r, self.depth - 1 + r),
            (self.width - 1 + r, self.depth - 1 + r),
        ]

    def build(self) -> "PirateManor":
        super().build()

        try:
            try:
                hm = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
            except KeyError:
                hm = self.editor.worldSlice.heightmaps["WORLD_SURFACE"]
            max_y = self.y
            extra = self.tower_radius
            base_tf = Transform(translation=(self.x, 0, self.z), rotation=self.rotation)
            for lx in range(-extra, self.width + extra):
                for lz in range(-extra, self.depth + extra):
                    try:
                        global_pos = base_tf.apply((lx, 0, lz))
                        ground_y = hm[global_pos.x, global_pos.z]
                        if ground_y > max_y:
                            max_y = ground_y
                    except IndexError:
                        pass
            self.y = max_y
        except Exception:
            pass
        with self.editor.pushTransform(
            Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        ):
            self.clear_interior()
            self.build_foundation()
            for i in range(self.floors):
                y_off = self.foundation_height + i * self.floor_height
                self.build_walls(y_off)
                if i > 0:
                    self.build_floor_slab(y_off)
                if i < self.floors - 1:
                    junction_y = y_off + self.floor_height
                    self.build_intermediate_floor(junction_y)
                    self.build_floor_cornice(junction_y)
            self.build_corner_towers()
            top_y = self.foundation_height + self.floors * self.floor_height
            self.build_pagoda_roof(base_y=top_y)
            self.build_stairs()
            self.build_entrance()
            self.build_windows()
            self.build_decorations()
        return self

    def clear_interior(self) -> None:
        extra = self.tower_radius + 2
        total_h = self.foundation_height + self.floors * self.floor_height + 14
        for y in range(self.foundation_height, total_h):
            for x in range(-extra, self.width + extra):
                for z in range(-extra, self.depth + extra):
                    self.safe_place(x, y, z, Block("air"))

    def build_foundation(self) -> None:
        try:
            try:
                hm = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
            except KeyError:
                hm = self.editor.worldSlice.heightmaps["WORLD_SURFACE"]
            has_hm = True
        except Exception:
            has_hm = False
        house_tf = Transform(
            translation=(self.x, self.y, self.z), rotation=self.rotation
        )

        def get_bottom_y(lx: int, lz: int) -> int:
            if not has_hm:
                return -2
            try:
                global_pos = house_tf.apply((lx, 0, lz))
                ground_y = hm[global_pos.x, global_pos.z]
                local_y = ground_y - self.y
                # return max(-30, min(-2, local_y - 1))
                return min(-2, local_y - 1)
            except IndexError:
                return -2

        for x in range(self.width):
            for z in range(self.depth):
                bottom = get_bottom_y(x, z)
                for y in range(bottom, self.foundation_height):
                    self.safe_place(x, y, z, choice(self.foundation))
        for tx, tz in self._tower_centers():
            for dx in range(-self.tower_radius, self.tower_radius + 1):
                for dz in range(-self.tower_radius, self.tower_radius + 1):
                    lx, lz = tx + dx, tz + dz
                    bottom = get_bottom_y(lx, lz)
                    for y in range(bottom, self.foundation_height):
                        self.safe_place(lx, y, lz, choice(self.foundation))

    def build_walls(self, floor_y_offset: int = 0) -> None:

        end_y = floor_y_offset + self.floor_height - 1
        for y in range(floor_y_offset, end_y + 1):
            for x in range(self.width):
                for z in range(self.depth):
                    is_corner = (x in (0, self.width - 1)) and (
                        z in (0, self.depth - 1)
                    )
                    is_edge = (x in (0, self.width - 1)) or (z in (0, self.depth - 1))

                    if is_corner:
                        self.safe_place(x, y, z, choice(self.pillar))
                    elif is_edge:
                        self.safe_place(x, y, z, choice(self.wall))

    def build_floor_slab(self, y: int) -> None:

        for x in range(1, self.width - 1):
            for z in range(1, self.depth - 1):
                self.safe_place(x, y, z, self.floor_block)

    def build_intermediate_floor(self, y: int) -> None:

        for x in range(1, self.width - 1):
            for z in range(1, self.depth - 1):
                self.safe_place(x, y, z, self.roofBlock)

    def build_floor_cornice(self, y: int) -> None:

        w, d = self.width - 1, self.depth - 1
        corners = {(-1, -1), (-1, d + 1), (w + 1, -1), (w + 1, d + 1)}
        for x in range(-1, w + 2):
            for z_out, facing in [(-1, "north"), (d + 1, "south")]:
                if (x, z_out) in corners:
                    self.safe_place(x, y, z_out, self.roofBlock)
                else:
                    stair = self.transformed(
                        Block(self.roofStair.id, {"facing": facing}),
                        Block(self.roofStair.id, {"facing": facing}),
                    )
                    self.safe_place(x, y, z_out, stair)
        for z in range(0, d + 1):
            for x_out, facing in [(-1, "west"), (w + 1, "east")]:
                stair = self.transformed(
                    Block(self.roofStair.id, {"facing": facing}),
                    Block(self.roofStair.id, {"facing": facing}),
                )
                self.safe_place(x_out, y, z, stair)

    def build_corner_towers(self) -> None:

        tower_top = self.foundation_height + self.floors * self.floor_height + 2
        for tx, tz in self._tower_centers():
            for y in range(self.foundation_height, tower_top + 1):
                for dx in range(-self.tower_radius, self.tower_radius + 1):
                    for dz in range(-self.tower_radius, self.tower_radius + 1):
                        on_edge = (
                            abs(dx) == self.tower_radius or abs(dz) == self.tower_radius
                        )
                        block = choice(self.wall) if on_edge else Block("air")
                        self.safe_place(tx + dx, y, tz + dz, block)

            merlon_y = tower_top + 1
            for dx in range(-self.tower_radius, self.tower_radius + 1):
                for dz in range(-self.tower_radius, self.tower_radius + 1):
                    on_edge = (
                        abs(dx) == self.tower_radius or abs(dz) == self.tower_radius
                    )
                    is_merlon = (dx % 2 == 0) or (dz % 2 == 0)

                    if on_edge and is_merlon:
                        self.safe_place(tx + dx, merlon_y, tz + dz, Block("gold_block"))
            self.safe_place(
                tx, merlon_y + 1, tz, Block("lantern", {"hanging": "false"})
            )

    def build_pagoda_roof(self, base_y: int) -> None:

        for x in range(1, self.width - 1):
            for z in range(1, self.depth - 1):
                self.safe_place(x, base_y, z, self.roofBlock)

        self._build_roof_level(
            cx=self.halfWidth,
            cz=self.halfDepth,
            base_y=base_y,
            hw=self.halfWidth + 1,
            hd=self.halfDepth + 1,
        )
        mhw, mhd = max(2, self.halfWidth - 1), max(2, self.halfDepth - 1)
        self._build_roof_level(
            cx=self.halfWidth, cz=self.halfDepth, base_y=base_y + 2, hw=mhw, hd=mhd
        )
        top_y = base_y + 2 + max(mhw, mhd)

        self.safe_place(self.halfWidth, top_y, self.halfDepth, self.roofBlock)
        self.safe_place(self.halfWidth, top_y + 1, self.halfDepth, Block("gold_block"))
        self.safe_place(
            self.halfWidth, top_y + 2, self.halfDepth, Block("dark_oak_fence")
        )
        self.safe_place(
            self.halfWidth, top_y + 3, self.halfDepth, Block("dark_oak_fence")
        )
        self.safe_place(
            self.halfWidth, top_y + 4, self.halfDepth, Block("black_banner")
        )

    def _build_roof_level(
        self, cx: int, cz: int, base_y: int, hw: int, hd: int
    ) -> None:
        for i in range(min(hw, hd)):
            y = base_y + i
            x0, x1 = cx - hw + i, cx + hw - i
            z0, z1 = cz - hd + i, cz + hd - i

            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    ex, ez = x in (x0, x1), z in (z0, z1)

                    if not (ex or ez):
                        continue
                    if ex and ez:
                        self.safe_place(x, y, z, Block("gold_block"))
                    elif ez:
                        facing = "south" if z == z0 else "north"
                        self.safe_place(
                            x, y, z, Block(self.roofStair.id, {"facing": facing})
                        )
                    else:
                        facing = "east" if x == x0 else "west"
                        self.safe_place(
                            x, y, z, Block(self.roofStair.id, {"facing": facing})
                        )

    def build_stairs(self) -> None:

        if self.floors <= 1:
            return

        stair_x = self.width - 2

        for floor_index in range(self.floors - 1):
            junction_y = self.foundation_height + (floor_index + 1) * self.floor_height
            walk_y = (
                self.foundation_height
                if floor_index == 0
                else self.foundation_height + floor_index * self.floor_height + 1
            )
            num_steps = junction_y - walk_y + 1
            sz_start = 2

            for step in range(num_steps):
                sy, sz = walk_y + step, sz_start + step

                if sz >= self.depth - 1:
                    break

                self.safe_place(
                    stair_x,
                    sy,
                    sz,
                    Block("dark_oak_stairs", {"facing": "south", "half": "bottom"}),
                )
                self.safe_place(stair_x, sy + 1, sz, Block("air"))
                self.safe_place(stair_x, sy + 2, sz, Block("air"))

                if sy < junction_y:
                    self.safe_place(stair_x, junction_y, sz, Block("air"))

    def build_entrance(self) -> None:
        dx, dy = self.halfWidth, self.foundation_height + 1

        for side, hinge in [(-1, "right"), (1, "left")]:
            self.safe_place(
                dx + side,
                dy,
                0,
                Block(
                    "dark_oak_door",
                    {"facing": "north", "hinge": hinge, "half": "lower"},
                ),
            )
            self.safe_place(
                dx + side,
                dy + 1,
                0,
                Block(
                    "dark_oak_door",
                    {"facing": "north", "hinge": hinge, "half": "upper"},
                ),
            )

        for ddy in range(3):
            self.safe_place(dx, dy + ddy, 0, Block("air"))

        for side in [-2, 2]:
            for y_offset in range(3):
                self.safe_place(dx + side, (dy - 1) + y_offset, 0, Block("gold_block"))

        for x_offset in range(-2, 3):
            self.safe_place(dx + x_offset, dy + 2, 0, Block("gold_block"))

    def build_windows(self) -> None:
        pane = Block("light_gray_stained_glass_pane")
        for fi in range(self.floors):
            wy = self.foundation_height + fi * self.floor_height + 2

            for dz in [self.halfDepth - 1, self.halfDepth + 1]:
                self.safe_place(0, wy, dz, pane)
                self.safe_place(self.width - 1, wy, dz, pane)

            for dx in [self.halfWidth - 2, self.halfWidth + 2]:
                if fi == 0 and 0 == 0:
                    continue

                self.safe_place(dx, wy, 0, pane)
                self.safe_place(dx, wy, self.depth - 1, pane)

    def build_decorations(self) -> None:
        base_y, total_y = (
            self.foundation_height,
            self.foundation_height + self.floors * self.floor_height,
        )
        for cx, cz in [
            (2, 2),
            (self.width - 3, 2),
            (2, self.depth - 3),
            (self.width - 3, self.depth - 3),
        ]:
            self.safe_place(cx, base_y, cz + 1, Block("chest", {"facing": "north"}))
        for side in [-1, 1]:
            self.safe_place(self.halfWidth + side, total_y, 0, Block("iron_bars"))
            self.safe_place(
                self.halfWidth + side,
                total_y - 1,
                0,
                Block("lantern", {"hanging": "true"}),
            )
        roof_top = total_y + 2 + max(self.halfWidth - 1, self.halfDepth - 1)
        self.safe_place(
            self.halfWidth,
            roof_top + 1,
            self.halfDepth,
            Block("grindstone", {"face": "floor", "facing": "north"}),
        )

    def get_footprint(self) -> tuple[int, int, int, int]:
        bx, ex, bz, ez = super().get_footprint()
        padding = 4
        total_margin = self.tower_radius + 1 + padding
        return (
            bx - total_margin,
            ex + total_margin,
            bz - total_margin,
            ez + total_margin,
        )

    def get_door_pos(self) -> tuple[int, int]:
        """Returns the global absolute coordinates just outside the entrance."""
        tf = Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        pos = tf.apply((self.halfWidth, 0, -1))
        return pos[0], pos[2]

    def plot(self, ax: Axes) -> "PirateManor":
        bx, ex, bz, ez = self.get_footprint()
        rect = patches.Rectangle(
            (bx, bz),
            ex - bx,
            ez - bz,
            edgecolor="black",
            fill=False,
            alpha=0.8,
            linewidth=2,
        )
        ax.add_patch(rect)
        return self
