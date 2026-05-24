from dataclasses import dataclass
from random import choice
from typing import TYPE_CHECKING, ClassVar, Sequence
from gdpc.block import Block
from gdpc.transform import Transform
from matplotlib import patches
from matplotlib.axes import Axes
from .house import House

if TYPE_CHECKING:
    from src.simulation.pirate import Pirate

@dataclass
class PirateHouse(House["Pirate"]):
    floors: int = 1 
    wallPalette: ClassVar[Sequence[Sequence[Block]]] = [
        [Block("polished_blackstone_bricks"), Block("dark_oak_planks")],
        [Block("cracked_polished_blackstone_bricks"), Block("spruce_planks")],
    ]
    pillarPalette: ClassVar[Sequence[Sequence[Block]]] = [
        [Block("dark_oak_log"), Block("dark_oak_log")],
    ]
    foundationPalette: ClassVar[Sequence[Sequence[Block]]] = [
        [Block("blackstone"), Block("cobblestone")],
        [Block("polished_blackstone"), Block("stone_bricks")],
    ]
    roofPalette: ClassVar[Sequence[Sequence[Block]]] = [
        [Block("deepslate_brick_stairs"), Block("deepslate_brick_slab"), Block("deepslate_bricks")],
        [Block("polished_deepslate_stairs"), Block("polished_deepslate_slab"), Block("polished_deepslate")],
    ]

    def __post_init__(self) -> None:

        self.wall = self.transformed(*choice(self.wallPalette))
        self.pillar = self.transformed(*choice(self.pillarPalette))
        self.foundation = self.transformed(*choice(self.foundationPalette))
        self.roofStair, self.roofSlab, self.roofBlock = choice(self.roofPalette)

        self.floors = max(1, min(4, self.floors))

        if self.width % 2 == 0: 
            self.width += 1
        if self.depth % 2 == 0: 
            self.depth += 1

        self.halfWidth = self.width // 2
        self.halfDepth = self.depth // 2
        self.foundation_height = 1
        self.floor_height = self.height

    def safe_place(self, x: int, y: int, z: int, block: Block) -> None:

        try: 
            self.editor.placeBlock((x, y, z), block)
        except Exception: 
            pass

    def build(self) -> "PirateHouse":
        try:

            try:
                hm = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
            except KeyError: 
                hm = self.editor.worldSlice.heightmaps["WORLD_SURFACE"]

            max_y = self.y
            extra = 1
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
        with self.editor.pushTransform(Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)):

            self.build_foundation()
            self.clear_interior()
            self.clear_cliff_entrance()

            for floor_index in range(self.floors):
                floor_y_offset = self.foundation_height + floor_index * self.floor_height
                self.build_walls(floor_y_offset=floor_y_offset)

                if floor_index < self.floors - 1:
                    junction_y = floor_y_offset + self.floor_height
                    self.build_intermediate_floor(junction_y)
                    self.build_floor_cornice(junction_y)

            top_y = self.foundation_height + self.floors * self.floor_height
            self.build_japanese_roof(base_y=top_y)
            self.build_stairs()
            self.build_door()
            self.build_windows()
            self.build_decorations()
        return self

    def build_foundation(self) -> None:
        try:
            try: 
                hm = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
            except KeyError: 
                hm = self.editor.worldSlice.heightmaps["WORLD_SURFACE"]

            has_hm = True
        except Exception: 
            has_hm = False

        house_tf = Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        def get_bottom_y(lx: int, lz: int) -> int:
            if not has_hm: 
                return -1
            
            try:
                global_pos = house_tf.apply((lx, 0, lz))
                ground_y = hm[global_pos.x, global_pos.z]
                local_y = ground_y - self.y

                return max(-30, min(-1, local_y - 1))
            except IndexError: 
                return -1
            
        for x in range(self.width):
            for z in range(self.depth):
                bottom = get_bottom_y(x, z)
                for y in range(bottom, self.foundation_height):
                    self.safe_place(x, y, z, choice(self.foundation))

    def build_walls(self, floor_y_offset: int = 0) -> None:

        start_y = floor_y_offset
        end_y = floor_y_offset + self.floor_height - 1

        for y in range(start_y, end_y + 1):
            for x in range(self.width):
                for z in range(self.depth):

                    is_corner = (x in (0, self.width - 1)) and (z in (0, self.depth - 1))
                    is_edge = (x in (0, self.width - 1)) or (z in (0, self.depth - 1))

                    if is_corner: 
                        self.safe_place(x, y, z, Block("air"))
                    elif is_edge: 
                        self.safe_place(x, y, z, choice(self.wall))

    def build_intermediate_floor(self, y: int) -> None:

        for x in range(1, self.width - 1):
            for z in range(1, self.depth - 1):
                self.safe_place(x, y, z, self.roofBlock)

    def build_floor_cornice(self, y: int) -> None:

        w = self.width - 1
        d = self.depth - 1
        corners = {(-1, -1), (-1, d + 1), (w + 1, -1), (w + 1, d + 1)}

        for x in range(-1, w + 2):
            for z_out, facing in [(-1, "north"), (d + 1, "south")]:
                pos = (x, z_out)
                if pos in corners: 
                    self.safe_place(x, y, z_out, self.roofBlock)
                else:
                    stair = self.transformed(Block(self.roofStair.id, {"facing": facing, "half": "bottom"}), Block(self.roofStair.id, {"facing": facing, "half": "bottom"}))
                    self.safe_place(x, y, z_out, stair)
        for z in range(0, d + 1):
            for x_out, facing in [(-1, "west"), (w + 1, "east")]:
                stair = self.transformed(Block(self.roofStair.id, {"facing": facing, "half": "bottom"}), Block(self.roofStair.id, {"facing": facing, "half": "bottom"}))
                self.safe_place(x_out, y, z, stair)

    def build_japanese_roof(self, base_y: int | None = None) -> None:
        if base_y is None: base_y = self.height
        self._build_roof_level(center_x=self.halfWidth, center_z=self.halfDepth, base_y=base_y, half_w=self.halfWidth + 1, half_d=self.halfDepth + 1)
        for x in range(1, self.width - 1):
            for z in range(1, self.depth - 1):
                self.safe_place(x, base_y, z, self.roofBlock)

        mini_half_w = max(2, self.halfWidth - 1)
        mini_half_d = max(2, self.halfDepth - 1)
        self._build_roof_level(center_x=self.halfWidth, center_z=self.halfDepth, base_y=base_y + 2, half_w=mini_half_w, half_d=mini_half_d)
        top_y = base_y + 2 + max(mini_half_w, mini_half_d)
        self.safe_place(self.halfWidth, top_y, self.halfDepth, self.roofBlock)
        self.safe_place(self.halfWidth, top_y + 1, self.halfDepth, Block("grindstone", {"face": "floor", "facing": "north"}))

    def _build_roof_level(self, center_x: int, center_z: int, base_y: int, half_w: int, half_d: int) -> None:
        
        layers = min(half_w, half_d)
        for i in range(layers):
            y = base_y + i
            x0, x1 = center_x - half_w + i, center_x + half_w - i
            z0, z1 = center_z - half_d + i, center_z + half_d - i
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    on_edge_x = (x == x0 or x == x1)
                    on_edge_z = (z == z0 or z == z1)
                    if not (on_edge_x or on_edge_z): 
                        continue
                    if on_edge_x and on_edge_z: 
                        self.safe_place(x, y, z, self.roofBlock)
                    elif on_edge_z:
                        facing = "south" if z == z0 else "north"
                        stair = self.transformed(Block(self.roofStair.id, {"facing": facing}), Block(self.roofStair.id, {"facing": facing}))
                        self.safe_place(x, y, z, stair)
                    else:
                        facing = "east" if x == x0 else "west"
                        stair = self.transformed(Block(self.roofStair.id, {"facing": facing}), Block(self.roofStair.id, {"facing": facing}))
                        self.safe_place(x, y, z, stair)

    def build_stairs(self) -> None:

        if self.floors <= 1: return
        stair_x = self.width - 2

        for floor_index in range(self.floors - 1):

            junction_y = self.foundation_height + (floor_index + 1) * self.floor_height
            walk_y = self.foundation_height if floor_index == 0 else self.foundation_height + floor_index * self.floor_height + 1
            num_steps = junction_y - walk_y + 1
            sz_start = 2
            for step in range(num_steps):

                sy, sz = walk_y + step, sz_start + step
                if sz >= self.depth - 1: 
                    break
                self.safe_place(stair_x, sy, sz, Block("dark_oak_stairs", {"facing": "south", "half": "bottom"}))
                self.safe_place(stair_x, sy + 1, sz, Block("air"))
                self.safe_place(stair_x, sy + 2, sz, Block("air"))
                if sy < junction_y: 
                    self.safe_place(stair_x, junction_y, sz, Block("air"))

    def build_door(self) -> None:

        door_x, door_y, door_z = self.halfWidth, self.foundation_height + 1, 0

        self.safe_place(door_x, door_y, door_z, Block("dark_oak_door", {"facing": "north", "hinge": "left", "half": "lower"}))
        self.safe_place(door_x, door_y + 1, door_z, Block("dark_oak_door", {"facing": "north", "hinge": "left", "half": "upper"}))
        self.safe_place(door_x - 1, door_y, door_z, Block("lantern", {"hanging": "false"}))
        self.safe_place(door_x + 1, door_y, door_z, Block("lantern", {"hanging": "false"}))

        house_tf = Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)

        try: 
            hm, has_hm = self.editor.worldSlice.heightmaps["WORLD_SURFACE"], True

        except Exception: has_hm = False

        for step in range(20):
            local_y, local_z = door_y - 1 - step, -1 - step
            world_pos = house_tf.apply((door_x, local_y, local_z))
            if has_hm and world_pos.y < hm[world_pos.x, world_pos.z]: 
                break

            self.safe_place(door_x, local_y, local_z, Block("polished_deepslate_stairs", {"facing": "south"}))

            for clear_h in range(1, 4): 
                self.safe_place(door_x, local_y + clear_h, local_z, Block("air"))

    def build_windows(self) -> None:

        pane = Block("black_stained_glass_pane")

        for floor_index in range(self.floors):
            window_y = self.foundation_height + floor_index * self.floor_height + 2
            if self.halfWidth > 1:
                self.safe_place(self.halfWidth - 1, window_y, 0, pane)
                self.safe_place(self.halfWidth + 1, window_y, 0, pane)
            if self.halfDepth > 0:
                self.safe_place(0, window_y, self.halfDepth, pane)
                self.safe_place(self.width - 1, window_y, self.halfDepth, pane)
            if self.halfWidth > 1:
                self.safe_place(self.halfWidth - 1, window_y, self.depth - 1, pane)
                self.safe_place(self.halfWidth + 1, window_y, self.depth - 1, pane)

    def build_decorations(self) -> None:

        total_wall_height = self.foundation_height + self.floors * self.floor_height

        if self.halfWidth > 1:
            self.safe_place(self.halfWidth - 1, self.foundation_height, 1, Block("barrel", {"facing": "up"}))
            self.safe_place(self.halfWidth + 1, self.foundation_height, 1, Block("barrel", {"facing": "up"}))

        self.safe_place(self.halfWidth, total_wall_height, 0, Block("iron_bars"))
        self.safe_place(self.halfWidth, total_wall_height - 1, 0, Block("lantern", {"hanging": "true"}))

    def get_footprint(self) -> tuple[int, int, int, int]:

        bx, ex, bz, ez = super().get_footprint()
        padding = 3
        return bx - padding, ex + padding, bz - padding, ez + padding

    def plot(self, ax: Axes) -> "PirateHouse":

        x0, z0, x1, z1 = self.get_footprint()
        rect = patches.Rectangle((x0, z0), x1 - x0, z1 - z0, edgecolor="black", fill=False, alpha=0.8)
        ax.add_patch(rect)
        return self

    def clear_interior(self) -> None:

        total_interior_height = self.floors * self.floor_height + 14
        
        for y in range(self.foundation_height, self.foundation_height + total_interior_height):
            for x in range(1, self.width - 1):
                for z in range(1, self.depth - 1):
                    self.safe_place(x, y, z, Block("air"))

    def clear_cliff_entrance(self) -> None:

        door_x, door_y = self.halfWidth, self.foundation_height + 1
        mini_half_w, mini_half_d = max(2, self.halfWidth - 1), max(2, self.halfDepth - 1)
        roof_peak_y = self.foundation_height + self.floors * self.floor_height + 2 + max(mini_half_w, mini_half_d) + 1
        
        for dz in range(1, 6):
            clear_z = -dz
            for clear_x in [door_x - 1, door_x, door_x + 1]:
                for clear_y in range(door_y, roof_peak_y + 1):
                    self.safe_place(clear_x, clear_y, clear_z, Block("air"))