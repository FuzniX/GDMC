from dataclasses import dataclass
from random import choice
from typing import ClassVar, Sequence

from gdpc.block import Block
from gdpc.geometry import placeCuboid, placeCuboidHollow
from gdpc.transform import Transform
from matplotlib import patches
from matplotlib.axes import Axes

from src.simulation.merchant import Merchant

from .house import House


@dataclass
class MerchantHouse(House[Merchant]):
    """
    Represents a specialized merchant estate featuring an intersecting gable roof,
    structural timber framing, a stone baseline, and exterior market stalls.
    """

    foundationPalette: ClassVar[Sequence[Sequence[Block]]] = [
        [Block("stone_bricks"), Block("cracked_stone_bricks")],
        [Block("cobblestone"), Block("mossy_cobblestone")],
    ]
    pillarPalette: ClassVar[Sequence[Sequence[Block]]] = [
        [Block("stripped_oak_log"), Block("stripped_birch_log")],
        [Block("stripped_spruce_log"), Block("stripped_dark_oak_log")],
    ]
    wallPalette: ClassVar[Sequence[Sequence[Block]]] = [
        [Block("white_terracotta"), Block("bone_block")],
        [Block("smooth_sandstone"), Block("sandstone")],
    ]
    roofPalette: ClassVar[Sequence[Sequence[Sequence[Block]]]] = [
        [
            [Block("oak_stairs"), Block("birch_stairs")],
            [Block("oak_planks"), Block("birch_planks")],
        ],
        [
            [Block("spruce_stairs"), Block("spruce_stairs")],
            [Block("spruce_planks"), Block("spruce_planks")],
        ],
    ]
    roofTrimPalette: ClassVar[Sequence[Sequence[Sequence[Block]]]] = [
        [
            [Block("stone_brick_stairs"), Block("cobblestone_stairs")],
            [Block("stone_bricks"), Block("cobblestone")],
        ]
    ]
    shopStructurePalette: ClassVar[Sequence[Block]] = [
        Block("oak_fence"),
        Block("spruce_slab"),
        Block("oak_trapdoor"),
    ]
    shopRoofPalette: ClassVar[Sequence[Block]] = [
        Block("green_wool"),
        Block("green_carpet"),
    ]

    def __post_init__(self) -> None:
        """Initialize and resolve random material selections and core building dimensions."""
        self.foundation = self.transformed(*choice(self.foundationPalette))
        self.pillar = self.transformed(*choice(self.pillarPalette))
        self.wall = self.transformed(*choice(self.wallPalette))

        # Select primary wooden roof components
        (roofStairs, roofDamagedStairs), (roofBlock, roofDamagedBlock) = choice(
            self.roofPalette
        )
        self.roofStairsBase = (roofStairs, roofDamagedStairs)

        # Map corresponding straight wooden slabs
        self.roofSlabBase = (
            Block(roofStairs.id.replace("stairs", "slab")),
            Block(roofDamagedStairs.id.replace("stairs", "slab")),
        )

        # Select stone border outline components
        (trimStairs, trimDamaged), (trimBlock, trimBlockDamaged) = choice(
            self.roofTrimPalette
        )
        self.roofTrim = (trimStairs, trimDamaged)
        self.roofTrimBlock = (trimBlock, trimBlockDamaged)
        self.roofTrimSlab = (
            Block(trimStairs.id.replace("stairs", "slab")),
            Block(trimDamaged.id.replace("stairs", "slab")),
        )

        # Enforce odd dimensions for clean geometric alignment
        if self.width % 2 == 0:
            self.width += 1
        if self.depth % 2 == 0:
            self.depth += 1
        self.halfWidth = self.width // 2
        self.halfDepth = self.depth // 2

        self.foundation_height = 2

    def build(self) -> "MerchantHouse":
        with self.editor.pushTransform(
            Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        ):
            self.build_foundation()
            self.build_frame_and_walls()
            self.build_roof()
            self.build_door_and_porch()
            self.build_windows()
            self.build_chimney()
            self.build_merchant_shops()

        return self

    def build_foundation(self) -> None:
        """Place the sub-surface and lower visible stone foundation layout."""
        placeCuboid(
            self.editor,
            (0, -5, 0),
            (self.width - 1, self.foundation_height - 1, self.depth - 1),
            self.foundation,
        )

    def build_frame_and_walls(self) -> None:
        """Erect hollow layout walls and reinforce corners with vertical logs."""
        start_y = self.foundation_height
        end_y = self.height - 1

        placeCuboidHollow(
            self.editor,
            (0, start_y, 0),
            (self.width - 1, end_y, self.depth - 1),
            self.wall,
        )

        corners = [
            (0, 0),
            (self.width - 1, 0),
            (0, self.depth - 1),
            (self.width - 1, self.depth - 1),
        ]
        for cx, cz in corners:
            placeCuboid(
                self.editor,
                (cx, start_y, cz),
                (cx, end_y, cz),
                self.pillar,
            )

    def _get_stairs(self, palette, facing: str, half: str = "bottom") -> list[Block]:
        """Generate structurally oriented and state-mixed stair block arrays."""
        normal, damaged = palette
        return self.transformed(
            Block(normal.id, {"facing": facing, "half": half}),
            Block(damaged.id, {"facing": facing, "half": half}),
        )

    def _get_slabs(self, palette) -> list[Block]:
        """Generate uniform flat base slab block arrays."""
        normal, damaged = palette
        return self.transformed(
            Block(normal.id, {"type": "bottom"}),
            Block(damaged.id, {"type": "bottom"}),
        )

    def build_roof(self) -> None:
        """Process layer-by-layer cross-intersecting roof segments and outer facade gables."""
        max_half = max(self.halfWidth, self.halfDepth)

        for h in range(max_half + 1):
            yy = self.height + h - 1

            self._build_roof_slope_x(h, yy)
            self._build_roof_slope_z(h, yy)

            if h > 0:
                self._fill_gable_facades(h, yy)

    def _build_roof_slope_x(self, h: int, yy: int) -> None:
        """Trace North and South facing slopes while appending eaves and structural gap fill blocks."""
        if h > self.halfDepth:
            return

        z_north, z_south = h, self.depth - 1 - h
        is_peak = h == self.halfDepth

        for x in range(-1, self.width + 1):
            is_trim = x == -1 or x == self.width
            palette = (
                self.roofTrimSlab
                if is_peak
                else (self.roofTrim if is_trim else self.roofStairsBase)
            )
            transversal_h = min(x, self.width - 1 - x) if 0 <= x < self.width else -1

            if h >= transversal_h:
                if is_peak:
                    # Finalize central ridge line with top slabs and solid blocks below
                    self.editor.placeBlock((x, yy, z_north), self._get_slabs(palette))
                    normal_trim_block, damaged_trim_block = self.roofTrimBlock
                    full_block = self.transformed(normal_trim_block, damaged_trim_block)
                    self.editor.placeBlock((x, yy - 1, z_north), full_block)
                else:
                    self.editor.placeBlock(
                        (x, yy, z_north), self._get_stairs(palette, "south")
                    )
                    self.editor.placeBlock(
                        (x, yy, z_south), self._get_stairs(palette, "north")
                    )

                    # Mount support fixtures under outer stone overhang eaves
                    if is_trim:
                        self.editor.placeBlock(
                            (x, yy - 1, z_north),
                            self._get_stairs(palette, "north", "top"),
                        )
                        self.editor.placeBlock(
                            (x, yy - 1, z_south),
                            self._get_stairs(palette, "south", "top"),
                        )

    def _build_roof_slope_z(self, h: int, yy: int) -> None:
        """Trace East and West facing slopes while appending eaves and structural gap fill blocks."""
        if h > self.halfWidth:
            return

        x_west, x_east = h, self.width - 1 - h
        is_peak = h == self.halfWidth

        for z in range(-1, self.depth + 1):
            is_trim = z == -1 or z == self.depth
            palette = (
                self.roofTrimSlab
                if is_peak
                else (self.roofTrim if is_trim else self.roofStairsBase)
            )
            transversal_h = min(z, self.depth - 1 - z) if 0 <= z < self.depth else -1

            if h >= transversal_h:
                if is_peak:
                    # Finalize central ridge line with top slabs and solid blocks below
                    self.editor.placeBlock((x_west, yy, z), self._get_slabs(palette))
                    normal_trim_block, damaged_trim_block = self.roofTrimBlock
                    full_block = self.transformed(normal_trim_block, damaged_trim_block)
                    self.editor.placeBlock((x_west, yy - 1, z), full_block)
                else:
                    self.editor.placeBlock(
                        (x_west, yy, z), self._get_stairs(palette, "east")
                    )
                    self.editor.placeBlock(
                        (x_east, yy, z), self._get_stairs(palette, "west")
                    )

                    # Mount support fixtures under outer stone overhang eaves
                    if is_trim:
                        self.editor.placeBlock(
                            (x_west, yy - 1, z),
                            self._get_stairs(palette, "west", "top"),
                        )
                        self.editor.placeBlock(
                            (x_east, yy - 1, z),
                            self._get_stairs(palette, "east", "top"),
                        )

    def _fill_gable_facades(self, h: int, yy: int) -> None:
        """Seal triangular open profiles under structural roof slopes using native wall elements."""
        z_in1, z_in2 = h, self.depth - 1 - h
        if z_in1 <= z_in2:
            placeCuboid(self.editor, (0, yy - 1, z_in1), (0, yy - 1, z_in2), self.wall)
            placeCuboid(
                self.editor,
                (self.width - 1, yy - 1, z_in1),
                (self.width - 1, yy - 1, z_in2),
                self.wall,
            )

        x_in1, x_in2 = h, self.width - 1 - h
        if x_in1 <= x_in2:
            placeCuboid(self.editor, (x_in1, yy - 1, 0), (x_in2, yy - 1, 0), self.wall)
            placeCuboid(
                self.editor,
                (x_in1, yy - 1, self.depth - 1),
                (x_in2, yy - 1, self.depth - 1),
                self.wall,
            )

    def build_door_and_porch(self) -> None:
        """Carve and anchor the front entryway door alongside external step platforms."""
        door_x = self.halfWidth
        door_y = self.foundation_height + 1
        door_z = 0

        doorBlock = Block(
            "dark_oak_door", {"facing": "north", "hinge": "left", "half": "lower"}
        )
        self.editor.placeBlock((door_x, door_y, door_z), doorBlock)
        self.editor.placeBlock((door_x, door_y, door_z), doorBlock)

        stair_block = self.transformed(
            Block("stone_brick_stairs", {"facing": "south"}),
            Block("cracked_stone_bricks"),
        )
        self.editor.placeBlock((door_x, door_y - 1, door_z - 1), stair_block)

    def build_windows(self) -> None:
        """Embed window frames and side shutter trapdoors across center wall profiles."""
        window_y = self.height // 2
        glass = Block("glass_pane")

        # West-facing wall window placement
        self.editor.placeBlock((0, window_y, self.halfDepth), glass)
        self.editor.placeBlock(
            (-1, window_y, self.halfDepth),
            Block("spruce_trapdoor", {"facing": "west", "open": "true"}),
        )

        # East-facing wall window placement
        self.editor.placeBlock((self.width - 1, window_y, self.halfDepth), glass)
        self.editor.placeBlock(
            (self.width, window_y, self.halfDepth),
            Block("spruce_trapdoor", {"facing": "east", "open": "true"}),
        )

    def build_chimney(self) -> None:
        """Erect an external brick exhaust stack equipped with an active campfire exhaust topper."""
        chimney_x = self.width - 2
        chimney_z = self.depth - 2
        roof_peak_y = self.height + max(self.halfWidth, self.halfDepth)

        placeCuboid(
            self.editor,
            (chimney_x, self.foundation_height, chimney_z),
            (chimney_x, roof_peak_y + 1, chimney_z),
            self.foundation,
        )

        self.editor.placeBlock(
            (chimney_x, roof_peak_y + 2, chimney_z), Block("cobblestone_wall")
        )
        self.editor.placeBlock(
            (chimney_x, roof_peak_y + 3, chimney_z), Block("campfire")
        )
        self.editor.placeBlock(
            (chimney_x, roof_peak_y + 3, chimney_z), Block("campfire")
        )

    def build_merchant_shops(self) -> None:
        """Calculate alignment coordinates and systematically deploy front-facing storefront modules."""
        nb_shops = len(self.player.store)

        shop_w = 3
        spacing = 1

        total_shops_width = (nb_shops * shop_w) + ((nb_shops - 1) * spacing)
        start_shop_x = (self.width - total_shops_width) // 2

        shop_z = -4
        shop_y = 1

        for i in range(nb_shops):
            current_x = start_shop_x + i * (shop_w + spacing)
            self._build_single_shop(current_x, shop_y, shop_z)

    def _build_single_shop(self, sx: int, sy: int, sz: int) -> None:
        """Build an individual covered market stall containing descriptive wares and storage crates."""
        # Erect support corner fences
        for dx in [0, 2]:
            for dz in [0, 1]:
                self.editor.placeBlock((sx + dx, sy, sz - dz), Block("oak_fence"))
                self.editor.placeBlock((sx + dx, sy + 1, sz - dz), Block("oak_fence"))

        # Stretch roof canvas and hanging drapery carpets
        roof_y = sy + 2
        placeCuboid(
            self.editor, (sx, roof_y, sz - 1), (sx + 2, roof_y, sz), Block("green_wool")
        )

        for dx in range(3):
            self.editor.placeBlock((sx + dx, roof_y, sz + 1), Block("green_carpet"))

        # Anchor functional utility and layout storage containers
        self.editor.placeBlock((sx, sy, sz), Block("barrel", {"facing": "up"}))
        self.editor.placeBlock((sx + 2, sy, sz), Block("composter"))

        # Position central trading vault with open access ventilation space above
        self.editor.placeBlock((sx + 1, sy, sz), Block("chest", {"facing": "north"}))
        self.editor.placeBlock((sx + 1, sy + 1, sz), Block("air"))

    def get_footprint(self) -> tuple[int, int, int, int]:
        baseX, endX, baseZ, endZ = super().get_footprint()

        nb_shops = len(self.player.store)
        shop_w = 3
        spacing = 1
        total_shops_width = (nb_shops * shop_w) + ((nb_shops - 1) * spacing)
        shop_extension = 5

        # Expand footprint boundaries based on local rotational facing direction
        if self.rotation % 2 == 0:
            house_w = endX - baseX
            if total_shops_width > house_w:
                diff = (total_shops_width - house_w) // 2
                baseX -= diff
                endX += diff

            if self.rotation == 0:
                baseZ -= shop_extension
            else:
                endZ += shop_extension
        else:
            house_d = endZ - baseZ
            if total_shops_width > house_d:
                diff = (total_shops_width - house_d) // 2
                baseZ -= diff
                endZ += diff

            if self.rotation == 1:
                baseX -= shop_extension
            else:
                endX += shop_extension

        return baseX, endX, baseZ, endZ

    def plot(self, ax: Axes) -> "MerchantHouse":
        rect = patches.Rectangle(
            (
                self.x + (0 if self.rotation in [0, 3] else 3),
                self.z + (0 if self.rotation in [0, 1] else 3),
            ),
            self.width + 3,
            self.depth + 3,
            edgecolor="red",
            fill=False,
            alpha=0.6,
            angle=self.rotation * 90,
        )
        ax.add_patch(rect)
        return self
