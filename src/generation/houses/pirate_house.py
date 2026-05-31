from dataclasses import dataclass
from random import choice

from gdpc.block import Block
from gdpc.transform import Transform
from matplotlib import patches
from matplotlib.axes import Axes

from src.utils import get_palette_for_biome

from .house import House


@dataclass
class PirateHouse(House["Pirate"]):
    floors: int = 1

    def __post_init__(self) -> None:
        # load the correct block palette for the current biome
        biome_string = self.editor.getBiome((self.x, self.y, self.z))
        palette = get_palette_for_biome(biome_string)

        # map palette components to local variables
        self.foundation = self.transformed(*palette["pirate_foundation"])
        self.pillar = self.transformed(*palette["pirate_pillar"])
        self.wall = self.transformed(*palette["pirate_wall"])

        self.roofStair = self.transformed(*palette["pirate_roof_stairs"])[0]
        self.roofSlab = self.transformed(*palette["pirate_roof_slab"])[0]
        self.roofBlock = self.transformed(*palette["pirate_roof_block"])[0]
        self.door = palette["pirate_door"][0]
        self.fence = palette["pirate_fence"][0]
        self.trapdoor = palette["pirate_trapdoor"][0]
        self.innerStair = palette["pirate_inner_stair"][0]
        self.window = palette["pirate_window"][0]

        # keep floor count within reasonable bounds
        self.floors = max(1, min(4, self.floors))

        # enforce odd dimensions for symmetrical roof alignment
        if self.width % 2 == 0:
            self.width += 1
        if self.depth % 2 == 0:
            self.depth += 1

        self.halfWidth = self.width // 2
        self.halfDepth = self.depth // 2
        self.foundation_height = 1
        self.floor_height = self.height

    def build(self) -> "PirateHouse":
        # main orchestration method to build the whole house structure
        super().build()

        try:
            # retrieve heightmap data to find the highest ground point
            try:
                hm = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
            except KeyError:
                hm = self.editor.worldSlice.heightmaps["WORLD_SURFACE"]

            max_y = self.y
            extra = 1
            base_tf = Transform(translation=(self.x, 0, self.z), rotation=self.rotation)

            # scan the building footprint area to adjust base height
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

            # execute building steps using local coordinates transform
            with self.editor.pushTransform(
                Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
            ):
                self.build_foundation()
                self.clear_interior()
                self.clear_cliff_entrance()

                # loop to construct each floor and intermediate sections
                for floor_index in range(self.floors):
                    floor_y_offset = (
                        self.foundation_height + floor_index * self.floor_height
                    )
                    self.build_walls(floor_y_offset=floor_y_offset)

                    if floor_index < self.floors - 1:
                        junction_y = floor_y_offset + self.floor_height
                        self.build_intermediate_floor(junction_y)
                        self.build_floor_cornice(junction_y)

                # finish with the roof and remaining details
                top_y = self.foundation_height + self.floors * self.floor_height
                self.build_japanese_roof(base_y=top_y)
                self.build_stairs()
                self.build_door()
                self.build_windows()
                self.build_decorations()
            return self
        except Exception:
            pass

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
                return -1
            try:
                global_pos = house_tf.apply((lx, 0, lz))
                ground_y = hm[global_pos.x, global_pos.z]
                local_y = ground_y - self.y
                return min(-1, local_y - 1)
            except IndexError:
                return -1

        for x in range(self.width):
            for z in range(self.depth):
                bottom = get_bottom_y(x, z)
                for y in range(bottom, self.foundation_height):
                    self.editor.placeBlock((x, y, z), choice(self.foundation))

        # stone platform border around the base (1 block wide)
        for x in range(-1, self.width + 1):
            for z in [-1, self.depth]:
                self.editor.placeBlock((x, 0, z), choice(self.foundation))
                self.editor.placeBlock((x, -1, z), choice(self.foundation))
        for z in range(0, self.depth):
            for x in [-1, self.width]:
                self.editor.placeBlock((x, 0, z), choice(self.foundation))
                self.editor.placeBlock((x, -1, z), choice(self.foundation))

    def build_walls(self, floor_y_offset: int = 0) -> None:
        start_y = floor_y_offset
        end_y = floor_y_offset + self.floor_height - 1

        # horizontal beam bands (every 2 rows)
        beam_ys = set(range(start_y, end_y + 1, 2))

        for y in range(start_y, end_y + 1):
            for x in range(self.width):
                for z in range(self.depth):
                    is_corner = (x in (0, self.width - 1)) and (
                        z in (0, self.depth - 1)
                    )
                    is_edge = (x in (0, self.width - 1)) or (
                        z in (0, self.depth - 1)
                    )
                    if is_corner:
                        self.editor.placeBlock((x, y, z), choice(self.pillar))
                    elif is_edge:
                        self.editor.placeBlock((x, y, z), choice(self.wall))

        # weathered trapdoors on the last wall row of each floor (all 4 sides)
        td_y = end_y
        w = self.width - 1
        d = self.depth - 1

        # front wall (z=0)
        for x in range(self.width):
            self.editor.placeBlock(
                (x, td_y, -1),
                Block(self.trapdoor.id, {"facing": "north", "half": "top", "open": "true"}),
            )
        # back wall (z=depth-1)
        for x in range(self.width):
            self.editor.placeBlock(
                (x, td_y, d+1),
                Block(self.trapdoor.id, {"facing": "south", "half": "top", "open": "true"}),
            )
        # left wall (x=0)
        for z in range(self.depth):
            self.editor.placeBlock(
                (-1, td_y, z),
                Block(self.trapdoor.id, {"facing": "west", "half": "top", "open": "true"}),
            )
        # right wall (x=width-1)
        for z in range(self.depth):
            self.editor.placeBlock(
                (w+1, td_y, z),
                Block(self.trapdoor.id, {"facing": "east", "half": "top", "open": "true"}),
            )

    def build_intermediate_floor(self, y: int) -> None:
        # fills the ceiling/floor layout between two levels
        for x in range(1, self.width - 1):
            for z in range(1, self.depth - 1):
                self.editor.placeBlock((x, y, z), self.roofBlock)

    def build_floor_cornice(self, y: int) -> None:
        w = self.width - 1
        d = self.depth - 1
        corners = {(-1, -1), (-1, d + 1), (w + 1, -1), (w + 1, d + 1)}

        # cornice stairs with bug fix applied
        for x in range(-1, w + 2):
            for z_out, facing in [(-1, "north"), (d + 1, "south")]:
                pos = (x, z_out)
                if pos in corners:
                    self.editor.placeBlock((x, y, z_out), self.roofBlock)
                else:
                    stair = self.transformed(
                        Block(self.roofStair.id, {"facing": facing, "half": "bottom"}),
                        Block(self.roofStair.id, {"facing": facing, "half": "bottom"}),
                    )[0]
                    self.editor.placeBlock((x, y, z_out), stair)

        for z in range(0, d + 1):
            for x_out, facing in [(-1, "west"), (w + 1, "east")]:
                stair = self.transformed(
                    Block(self.roofStair.id, {"facing": facing, "half": "bottom"}),
                    Block(self.roofStair.id, {"facing": facing, "half": "bottom"}),
                )[0]
                self.editor.placeBlock((x_out, y, z), stair)

        # fence railing on the cornice for japanese balcony style
        fence = self.fence
        for x in range(0, w + 1):
            self.editor.placeBlock((x, y + 1, -1), fence)
            self.editor.placeBlock((x, y + 1, d + 1), fence)
        for z in range(0, d + 1):
            self.editor.placeBlock((-1, y + 1, z), fence)
            self.editor.placeBlock((w + 1, y + 1, z), fence)

        # hanging lanterns at the cornice corners
        for cx, cz in [(-1, -1), (-1, d + 1), (w + 1, -1), (w + 1, d + 1)]:
            self.editor.placeBlock(
                (cx, y - 1, cz), Block("lantern", {"hanging": "true"})
            )
            self.editor.placeBlock((cx, y + 1, cz), fence)

        # lanterns every 2 blocks along the edges
        for x in range(1, w, 2):
            self.editor.placeBlock(
                (x, y - 1, -1), Block("lantern", {"hanging": "true"})
            )
            self.editor.placeBlock(
                (x, y - 1, d + 1), Block("lantern", {"hanging": "true"})
            )
        for z in range(1, d, 2):
            self.editor.placeBlock(
                (-1, y - 1, z), Block("lantern", {"hanging": "true"})
            )
            self.editor.placeBlock(
                (w + 1, y - 1, z), Block("lantern", {"hanging": "true"})
            )

    def build_japanese_roof(self, base_y: int | None = None) -> None:
        if base_y is None:
            base_y = self.height
        self._build_roof_level(
            center_x=self.halfWidth,
            center_z=self.halfDepth,
            base_y=base_y,
            half_w=self.halfWidth + 1,
            half_d=self.halfDepth + 1,
        )
        for x in range(1, self.width - 1):
            for z in range(1, self.depth - 1):
                self.editor.placeBlock((x, base_y, z), self.roofBlock)

        mini_half_w = max(2, self.halfWidth - 1)
        mini_half_d = max(2, self.halfDepth - 1)
        self._build_roof_level(
            center_x=self.halfWidth,
            center_z=self.halfDepth,
            base_y=base_y + 2,
            half_w=mini_half_w,
            half_d=mini_half_d,
        )
        top_y = base_y + 2 + max(mini_half_w, mini_half_d)
        self.editor.placeBlock((self.halfWidth, top_y, self.halfDepth), self.roofBlock)
        self.editor.placeBlock(
            (self.halfWidth, top_y + 1, self.halfDepth),
            self.roofBlock,
        )

    def _build_roof_level(
        self, center_x: int, center_z: int, base_y: int, half_w: int, half_d: int
    ) -> None:
        layers = min(half_w, half_d)
        for i in range(layers):
            y = base_y + i
            x0, x1 = center_x - half_w + i, center_x + half_w - i
            z0, z1 = center_z - half_d + i, center_z + half_d - i
            for x in range(x0, x1 + 1):
                for z in range(z0, z1 + 1):
                    on_edge_x = x == x0 or x == x1
                    on_edge_z = z == z0 or z == z1
                    if not (on_edge_x or on_edge_z):
                        continue
                    if on_edge_x and on_edge_z:
                        self.editor.placeBlock((x, y, z), self.roofBlock)
                    elif on_edge_z:
                        facing = "south" if z == z0 else "north"
                        stair = self.transformed(
                            Block(self.roofStair.id, {"facing": facing}),
                            Block(self.roofStair.id, {"facing": facing}),
                        )
                        self.editor.placeBlock((x, y, z), stair)
                    else:
                        facing = "east" if x == x0 else "west"
                        stair = self.transformed(
                            Block(self.roofStair.id, {"facing": facing}),
                            Block(self.roofStair.id, {"facing": facing}),
                        )
                        self.editor.placeBlock((x, y, z), stair)

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
                self.editor.placeBlock(
                    (stair_x, sy, sz),
                    Block(self.innerStair.id, {"facing": "south", "half": "bottom"}),
                )
                self.editor.placeBlock((stair_x, sy + 1, sz), Block("air"))
                self.editor.placeBlock((stair_x, sy + 2, sz), Block("air"))
                if sy < junction_y:
                    self.editor.placeBlock((stair_x, junction_y, sz), Block("air"))

    def build_door(self) -> None:
        door_x, door_y, door_z = self.halfWidth, self.foundation_height + 1, 0

        # door
        self.editor.placeBlock(
            (door_x, door_y - 1, door_z),
            Block(
                self.door.id, {"facing": "north", "hinge": "left", "half": "lower"}
            ),
        )
        self.editor.placeBlock(
            (door_x, door_y, door_z),
            Block(
                self.door.id, {"facing": "north", "hinge": "left", "half": "upper"}
            ),
        )

    def build_windows(self) -> None:
        pane = self.window

        for floor_index in range(self.floors):
            window_y = self.foundation_height + floor_index * self.floor_height + 2

            if self.halfWidth > 1:
                # front and back facade with glass and a solid block above
                for wx in [self.halfWidth - 1, self.halfWidth + 1]:
                    above = choice(self.wall)
                    self.editor.placeBlock((wx, window_y, 0), pane)
                    self.editor.placeBlock((wx, window_y + 1, 0), above)
                    self.editor.placeBlock((wx, window_y, self.depth - 1), pane)
                    self.editor.placeBlock((wx, window_y + 1, self.depth - 1), above)

            if self.halfDepth > 0:
                # sides with glass and a solid block above
                above_side = (
                    choice(self.wall)
                    if self.halfDepth % 2 == 0
                    else choice(self.wall)
                )
                self.editor.placeBlock((0, window_y, self.halfDepth), pane)
                self.editor.placeBlock((self.width - 1, window_y, self.halfDepth), pane)
                self.editor.placeBlock((0, window_y + 1, self.halfDepth), above_side)
                self.editor.placeBlock(
                    (self.width - 1, window_y + 1, self.halfDepth), above_side
                )

    def build_decorations(self) -> None:
        total_wall_height = self.foundation_height + self.floors * self.floor_height

        # mangrove fences around the ground floor (1st floor only)
        # placed at foundation_height level, one block outside the walls
        fence_y = self.foundation_height
        fence = self.fence

        # door zone to skip on front face (z=-1): halfWidth-1, halfWidth, halfWidth+1
        door_xs = {self.halfWidth, self.halfWidth, self.halfWidth}

        # front face (z=-1)
        for x in range(self.width+1):
            if x not in door_xs:
                self.editor.placeBlock((x, fence_y, -1), fence)

        # back face (z=depth)
        for x in range(self.width+1):
            self.editor.placeBlock((x, fence_y, self.depth), fence)

        # left face (x=-1)
        for z in range(self.depth+1):
            self.editor.placeBlock((-1, fence_y, z), fence)

        # right face (x=width)
        for z in range(self.depth+1):
            self.editor.placeBlock((self.width, fence_y, z), fence)

        
        # hanging lanterns along the roof eave edges
        roof_y = self.foundation_height + self.floors * self.floor_height
        w = self.width - 1
        d = self.depth - 1

        # every 2 blocks along front and back eaves
        for x in range(1, w, 2):
            self.editor.placeBlock((x, roof_y - 1, -1), Block("lantern", {"hanging": "true"}))
            self.editor.placeBlock((x, roof_y - 1, d + 1), Block("lantern", {"hanging": "true"}))

        # every 2 blocks along left and right eaves
        for z in range(1, d, 2):
            self.editor.placeBlock((-1, roof_y - 1, z), Block("lantern", {"hanging": "true"}))
            self.editor.placeBlock((w + 1, roof_y - 1, z), Block("lantern", {"hanging": "true"}))

    def get_footprint(self) -> tuple[int, int, int, int]:
        # returns the expanded bounding box area including safety padding
        bx, ex, bz, ez = super().get_footprint()
        padding = 3
        return bx - padding, ex + padding, bz - padding, ez + padding

    def plot(self, ax: Axes) -> "PirateHouse":
        # draws a bounding box representation for debugging or map visualization
        x0, z0, x1, z1 = self.get_footprint()
        rect = patches.Rectangle(
            (x0, z0), x1 - x0, z1 - z0, edgecolor="black", fill=False, alpha=0.8
        )
        ax.add_patch(rect)
        return self

    def clear_interior(self) -> None:
        # clears out blocks inside the house boundaries to ensure hollow rooms
        total_interior_height = self.floors * self.floor_height + 14
        for y in range(
            self.foundation_height + 1, self.foundation_height + total_interior_height
        ):
            for x in range(1, self.width - 1):
                for z in range(1, self.depth - 1):
                    self.editor.placeBlock((x, y, z), Block("air"))

    def clear_cliff_entrance(self) -> None:
        # clears an open air corridor in front of the building to prevent terrain blocking
        door_x, door_y = self.halfWidth, self.foundation_height + 1
        mini_half_w, mini_half_d = (
            max(2, self.halfWidth - 1),
            max(2, self.halfDepth - 1),
        )
        roof_peak_y = (
            self.foundation_height
            + self.floors * self.floor_height
            + 2
            + max(mini_half_w, mini_half_d)
            + 1
        )
        for dz in range(1, 6):
            clear_z = -dz
            for clear_x in [door_x - 1, door_x, door_x + 1]:
                for clear_y in range(door_y, roof_peak_y + 1):
                    self.editor.placeBlock((clear_x, clear_y, clear_z), Block("air"))

    def get_door_pos(self) -> tuple[int, int]:
        # computes global coordinates for the door placement point
        tf = Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        pos = tf.apply((self.halfWidth, 0, -1))
        return pos[0], pos[2]