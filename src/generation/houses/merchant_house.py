import random as rnd
from dataclasses import dataclass
from random import choice

from gdpc.block import Block
from gdpc.editor_tools import placeSign
from gdpc.geometry import placeCuboid
from gdpc.transform import Transform
from matplotlib import patches
from matplotlib.axes import Axes

from src.simulation.merchant import Merchant
from src.utils import get_palette_for_biome

from .house import House


@dataclass
class MerchantHouse(House[Merchant]):
    """
    Represents a specialized merchant estate featuring an intersecting gable roof,
    structural timber framing, a right wing for shops, a rooftop bonsai,
    and dynamic chest filling for the merchant's store.
    """

    def __post_init__(self) -> None:
        """Initialize dimensions and dynamically map the biome palettes."""
        self.width = 27
        self.depth = 17
        self.halfWidth = self.width // 2
        self.halfDepth = self.depth // 2

        biome_string = self.editor.getBiome((self.x, self.y, self.z))
        palette = get_palette_for_biome(biome_string)

        self.base_stone = self.transformed(*palette["vil_base_stone_alt"])
        self.base_stone_alt = self.transformed(*palette["vil_base_stone"])
        self.porch_slab = self.transformed(*palette["vil_roof_fill_slab"])

        self.pillar_wood = self.transformed(*palette["vil_wall_wood"])
        self.beam_wood = self.transformed(*palette["vil_wall_wood"])
        self.wall_wood = self.transformed(*palette["vil_pillar_wood"])

        self.shoji_block = self.transformed(*palette["vil_shoji_block"])
        self.shoji_trapdoor = self.transformed(*palette["vil_shoji_trapdoor"])

        self.roof_outline_stair = self.transformed(*palette["vil_roof_fill_stair"])
        self.roof_outline_slab = self.transformed(*palette["vil_roof_fill_slab"])
        self.roof_outline_block = self.transformed(*palette["vil_roof_block"])

        self.roof_fill_stair = self.transformed(*palette["vil_roof_outline_stair"])
        self.roof_fill_slab = self.transformed(*palette["vil_roof_outline_slab"])
        self.roof_block = self.transformed(*palette["vil_roof_outline_block"])

        id_norm = palette["vil_roof_fill_slab"][0].id.replace("slab", "fence")
        id_dmg = palette["vil_roof_fill_slab"][1].id.replace("slab", "fence")
        if "fence" not in id_norm:
            id_norm = "dark_oak_fence"
        if "fence" not in id_dmg:
            id_dmg = "dark_oak_fence"
        self.porch_fence = self.transformed(Block(id_norm), Block(id_dmg))

        self.bonsai_log = self.transformed(Block("cherry_log"), Block("dead_tube"))
        self.bonsai_leaves = self.transformed(Block("cherry_leaves"), Block("air"))

    def _get_bottom_y(self, lx: int, lz: int, house_tf: Transform) -> int:
        """Calculate the local terrain depth under a specific coordinate."""
        assert self.editor.worldSlice is not None
        hm = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

        global_pos = house_tf.apply((lx, 0, lz))
        sx, sz = hm.shape

        if 0 <= global_pos.x < sx and 0 <= global_pos.z < sz:
            ground_y = hm[global_pos.x, global_pos.z]
            return min(-1, ground_y - self.y - 1)
        return -1

    def build(self) -> "MerchantHouse":
        super().build()

        with self.editor.pushTransform(
            Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        ):
            placeCuboid(self.editor, (0, 1, 0), (26, 22, 16), Block("air"))

            self.build_foundation_and_pond()
            self.build_main_building()
            self.build_right_wing()
            self.build_bonsai_tree()
            self.build_merchant_shops()

        return self

    def build_foundation_and_pond(self) -> None:
        house_tf = Transform(
            translation=(self.x, self.y, self.z), rotation=self.rotation
        )

        for x in range(1, 26):
            for z in range(1, 16):
                if 17 <= x <= 24 and 1 <= z <= 4:
                    continue

                bottom = self._get_bottom_y(x, z, house_tf)
                for y_f in range(bottom, 1):
                    blk = (
                        choice(self.base_stone)
                        if (x + z) % 2 == 0
                        else choice(self.base_stone_alt)
                    )
                    self.editor.placeBlock((x, y_f, z), blk)

                if x in (1, 15, 25) or z in (1, 5, 15):
                    self.editor.placeBlock((x, 1, z), choice(self.base_stone))
                    selected_slab = choice(self.porch_slab)
                    self.editor.placeBlock(
                        (x, 2, z), Block(selected_slab.id, {"type": "bottom"})
                    )
                else:
                    self.editor.placeBlock((x, 1, z), choice(self.base_stone_alt))
                    self.editor.placeBlock((x, 2, z), choice(self.roof_block))

        # Pond
        for x in range(17, 25):
            for z in range(1, 5):
                self.editor.placeBlock((x, 0, z), choice(self.base_stone))

                # South
                if z == 1:
                    stair = Block("stone_brick_stairs", {"facing": "south"})
                    self.editor.placeBlock((x, 1, z), stair)
                # North
                elif z == 4:
                    stair = Block("stone_brick_stairs", {"facing": "north"})
                    self.editor.placeBlock((x, 1, z), stair)
                # East
                elif x == 17:
                    stair = Block("stone_brick_stairs", {"facing": "east"})
                    self.editor.placeBlock((x, 1, z), stair)
                # West
                elif x == 24:
                    stair = Block("stone_brick_stairs", {"facing": "west"})
                    self.editor.placeBlock((x, 1, z), stair)
                else:
                    self.editor.placeBlock((x, 1, z), Block("water"))

        # Main entrance steps
        for x in [7, 8, 9]:
            stair = Block("stone_brick_stairs", {"facing": "south"})
            self.editor.placeBlock((x, 1, 0), stair)
            self.editor.placeBlock((x, 2, 0), Block("air"))

    def build_main_building(self) -> None:
        # Ground floor structural pillars
        for px in [2, 6, 10, 14]:
            for y in range(3, 7):
                self.editor.placeBlock((px, y, 2), choice(self.pillar_wood))
                self.editor.placeBlock((px, y, 14), choice(self.pillar_wood))
        for pz in [2, 6, 10, 14]:
            for y in range(3, 7):
                self.editor.placeBlock((2, y, pz), choice(self.pillar_wood))
                self.editor.placeBlock((14, y, pz), choice(self.pillar_wood))

        # Front Wall
        for x in range(3, 14):
            if x not in [6, 10]:
                for y in range(3, 6):
                    is_door = x in [7, 8, 9]
                    blk = Block("air") if is_door else choice(self.shoji_block)
                    self.editor.placeBlock((x, y, 2), blk)

        # Back Wall
        for x in range(3, 14):
            self.editor.placeBlock(
                (x, 6, 14), Block(choice(self.beam_wood).id, {"axis": "x"})
            )
            if x in [6, 10]:
                continue
            is_window = x in [4, 12]
            for y in range(3, 6):
                if is_window and y in [4, 5]:
                    self.editor.placeBlock((x, y, 14), choice(self.shoji_block))
                    td_face = "south" if y == 4 else "north"
                    self.editor.placeBlock(
                        (x, y, 15),
                        Block(
                            choice(self.shoji_trapdoor).id,
                            {"facing": td_face, "open": "true"},
                        ),
                    )
                else:
                    self.editor.placeBlock((x, y, 14), choice(self.wall_wood))

        # Left Wall
        for z in range(3, 14):
            self.editor.placeBlock(
                (2, 6, z), Block(choice(self.beam_wood).id, {"axis": "z"})
            )
            if z in [6, 10]:
                continue
            is_window = z in [4, 8, 12]
            for y in range(3, 6):
                if is_window and y in [4, 5]:
                    self.editor.placeBlock((2, y, z), choice(self.shoji_block))
                    self.editor.placeBlock(
                        (1, y, z),
                        Block(
                            choice(self.shoji_trapdoor).id,
                            {"facing": "east", "open": "true"},
                        ),
                    )
                else:
                    self.editor.placeBlock((2, y, z), choice(self.wall_wood))

        # Double doors (Front)
        db = Block("dark_oak_door", {"half": "lower", "facing": "north"})
        dt = Block("dark_oak_door", {"half": "upper", "facing": "north"})
        self.editor.placeBlock((8, 3, 2), db)
        self.editor.placeBlock((8, 4, 2), dt)

        # Skirt roof (Mokoshi)
        self._build_roof_ring(1, 15, 1, 15, 6, "slab")
        self._build_roof_ring(2, 14, 2, 14, 6, "stair")

        # Second floor inset pillars
        for px in [3, 7, 11, 13]:
            for y in range(7, 11):
                self.editor.placeBlock((px, y, 3), choice(self.pillar_wood))
                self.editor.placeBlock((px, y, 13), choice(self.pillar_wood))

        # Second Floor
        # Front Wall
        for x in range(4, 13):
            if x not in [7, 11]:
                self.editor.placeBlock((x, 7, 3), choice(self.wall_wood))
                self.editor.placeBlock((x, 8, 3), choice(self.shoji_block))
                self.editor.placeBlock((x, 9, 3), choice(self.shoji_block))

                # Window planters
                if x in [4, 5, 8, 9, 12]:
                    self.editor.placeBlock((x, 7, 2), Block("grass_block"))
                    self.editor.placeBlock((x, 8, 2), Block("peony"))
                    trapdoor = Block(
                        "spruce_trapdoor", {"facing": "north", "open": "true"}
                    )
                    self.editor.placeBlock((x, 7, 1), trapdoor)

        # Back & Side Timber Walls
        for x in range(4, 13):
            if x not in [7, 11]:
                self.editor.placeBlock(
                    (x, 10, 13), Block(choice(self.beam_wood).id, {"axis": "x"})
                )
                for y in range(7, 10):
                    self.editor.placeBlock((x, y, 13), choice(self.wall_wood))

        for z in range(4, 13):
            if z not in [7, 11]:
                self.editor.placeBlock(
                    (3, 10, z), Block(choice(self.beam_wood).id, {"axis": "z"})
                )
                self.editor.placeBlock(
                    (13, 10, z), Block(choice(self.beam_wood).id, {"axis": "z"})
                )
                for y in range(7, 10):
                    self.editor.placeBlock((3, y, z), choice(self.wall_wood))
                    self.editor.placeBlock((13, y, z), choice(self.wall_wood))

        # Main roof
        y_roof = 11
        self._build_roof_ring(2, 14, 2, 14, y_roof, "slab")
        self._build_roof_ring(3, 13, 3, 13, y_roof, "stair")
        self._build_roof_ring(4, 12, 4, 12, y_roof + 1, "stair")

        for dz in range(4):
            y_cur = y_roof + 2 + dz
            z_n = 5 + dz
            z_s = 11 - dz
            if z_n > z_s:
                break

            # Slopes
            for x in range(5, 12):
                bn = self.roof_outline_stair if x in (5, 11) else self.roof_fill_stair
                bs = self.roof_outline_stair if x in (5, 11) else self.roof_fill_stair
                self.editor.placeBlock(
                    (x, y_cur, z_n), Block(choice(bn).id, {"facing": "south"})
                )
                self.editor.placeBlock(
                    (x, y_cur, z_s), Block(choice(bs).id, {"facing": "north"})
                )
                self.editor.placeBlock((x, y_cur - 1, z_n), choice(self.roof_block))
                self.editor.placeBlock((x, y_cur - 1, z_s), choice(self.roof_block))

            # Gables
            for x in [5, 11]:
                for z_f in range(z_n + 1, z_s):
                    self.editor.placeBlock((x, y_cur, z_f), choice(self.shoji_block))

        # Roof ridge
        y_peak = 17
        for x in range(4, 13):
            slab = Block(choice(self.roof_outline_slab).id, {"type": "bottom"})
            self.editor.placeBlock((x, y_peak, 8), slab)
            self.editor.placeBlock((x, y_peak - 1, 8), choice(self.roof_block))

        self.editor.placeBlock(
            (3, y_peak, 8),
            Block(choice(self.roof_outline_stair).id, {"facing": "west"}),
        )
        self.editor.placeBlock(
            (13, y_peak, 8),
            Block(choice(self.roof_outline_stair).id, {"facing": "east"}),
        )

    def build_right_wing(self) -> None:
        """Constructs the attached 1-story merchant shop wing."""
        for x in range(16, 25):
            self.editor.placeBlock((x, 3, 5), choice(self.porch_fence))
        for z in range(5, 14):
            self.editor.placeBlock((25, 3, z), choice(self.porch_fence))

        # Closed back framing for the marketplace sector
        for x in range(16, 26):
            self.editor.placeBlock(
                (x, 6, 14), Block(choice(self.beam_wood).id, {"axis": "x"})
            )
            for y in range(3, 6):
                self.editor.placeBlock((x, y, 14), choice(self.wall_wood))

        self._build_roof_ring(16, 26, 4, 15, 6, "slab")
        for x in range(17, 25):
            for z in range(5, 14):
                self.editor.placeBlock((x, 6, z), choice(self.roof_block))

    def build_bonsai_tree(self) -> None:
        """Grows a large decorative bonsai tree on the right wing roof."""
        tx, ty, tz = 21, 7, 10
        for y in range(ty, ty + 5):
            self.editor.placeBlock((tx, y, tz), choice(self.bonsai_log))

        self.editor.placeBlock((tx - 1, ty + 2, tz), choice(self.bonsai_log))
        self.editor.placeBlock((tx + 1, ty + 3, tz), choice(self.bonsai_log))

        for dx in range(-2, 3):
            for dy in range(-2, 3):
                for dz in range(-2, 3):
                    if dx**2 + dy**2 + dz**2 <= 5:
                        self.editor.placeBlock(
                            (tx + dx, ty + 4 + dy, tz + dz), choice(self.bonsai_leaves)
                        )

    def build_merchant_shops(self) -> None:
        """Populate the right wing with multiple distributed merchant stands."""
        shops = self.player.store

        positions = [(17, 13), (20, 13), (23, 13), (18, 9), (22, 9)]

        for i, shop in enumerate(shops):
            if i >= len(positions):
                break

            sx, sz = positions[i]
            self._build_single_shop(sx, 3, sz, shop)

    def _build_single_shop(self, sx: int, sy: int, sz: int, shop) -> None:
        """Builds a detailed 2-block wide shop counter, inventory chest, and sign."""
        # Store Counter
        s1 = Block(choice(self.porch_slab).id, {"type": "top"})
        s2 = Block(choice(self.porch_slab).id, {"type": "top"})
        self.editor.placeBlock((sx, sy, sz - 1), s1)
        self.editor.placeBlock((sx + 1, sy, sz - 1), s2)

        # Randomly Distribute Items in Chest NBT
        qty = shop.owned_quantity
        slots = {}
        if qty > 0:
            for _ in range(qty):
                slot = rnd.randint(0, 26)
                slots[slot] = slots.get(slot, 0) + 1

        items_nbt = []
        clean_name = shop.name.replace("minecraft:", "")
        for slot, count in slots.items():
            items_nbt.append(
                f'{{Slot: {slot}b, id: "minecraft:{clean_name}", Count: {count}b}}'
            )

        chest_nbt = f"{{Items: [{', '.join(items_nbt)}]}}"

        # Place Chest facing North
        chest = Block("chest", {"facing": "north"}, data=chest_nbt)
        self.editor.placeBlock((sx, sy, sz), chest)

        # Place utility barrel
        self.editor.placeBlock((sx + 1, sy, sz), Block("barrel", {"facing": "up"}))

        # Informational Sign with Front Text
        display_name = clean_name.capitalize().replace("_", " ")

        placeSign(
            editor=self.editor,
            position=(sx, sy + 1, sz),
            wall=True,
            facing="north",
            frontLine1=display_name,
            frontLine2=f"Price: {shop.price}",
            frontLine3=f"Stock: {qty}/{shop.max_quantity}",
            frontLine4=f"Food: {shop.is_food}",
        )

        # Small Awning Canopy
        fence = choice(self.porch_fence)
        self.editor.placeBlock((sx, sy + 1, sz - 1), fence)
        self.editor.placeBlock((sx + 1, sy + 1, sz - 1), fence)
        self.editor.placeBlock((sx, sy + 2, sz - 1), choice(self.shoji_trapdoor))
        self.editor.placeBlock((sx + 1, sy + 2, sz - 1), choice(self.shoji_trapdoor))

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

        if part == "slab":
            for cx, cz in [(x1, z1), (x2, z1), (x1, z2), (x2, z2)]:
                selected_block = choice(self.roof_outline_block)
                self.editor.placeBlock((cx, y, cz), Block(selected_block.id))

    def get_local_footprint(self) -> tuple[int, int, int, int]:
        return 0, self.width, 0, self.depth

    def plot(self, ax: Axes) -> "MerchantHouse":
        rect = patches.Rectangle(
            (self.x, self.z),
            self.width,
            self.depth,
            edgecolor="orange",
            fill=False,
            alpha=0.6,
            angle=self.rotation * 90,
        )
        ax.add_patch(rect)
        return self
