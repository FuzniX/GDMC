from dataclasses import dataclass
from random import choice

from gdpc.block import Block
from gdpc.geometry import placeCuboid, placeCuboidHollow
from gdpc.transform import Transform
from matplotlib import patches
from matplotlib.axes import Axes

from src.utils import get_palette_for_biome

from .house import House


@dataclass
class BasicHouse(House):
    """
    Dataclass representing a basic house that is built in Minecraft
    """

    # floorPalette: ClassVar[Sequence[Sequence[Block]]] = [
    #     [Block("stone_bricks"), Block("cracked_stone_bricks")],
    #     [Block("cobblestone"), Block("mossy_cobblestone")],
    # ]
    # wallPalette: ClassVar[Sequence[Sequence[Block]]] = [
    #     [Block("oak_planks"), Block("birch_planks")],
    #     [Block("spruce_planks"), Block("dark_oak_planks")],
    #     [Block("white_terracotta"), Block("green_terracotta")],
    # ]
    # roofPalette: ClassVar[Sequence[Sequence[Sequence[Block]]]] = [
    #     [
    #         [Block("oak_stairs"), Block("birch_stairs")],
    #         [Block("oak_planks"), Block("birch_planks")],
    #     ],
    #     [
    #         [Block("spruce_stairs"), Block("dark_oak_stairs")],
    #         [Block("spruce_planks"), Block("dark_oak_planks")],
    #     ],
    # ]

    def __post_init__(self) -> None:
        """
        Variables to define after initialization/instanciation
        :return: Nothing
        """
        biome_string = self.editor.getBiome((self.x, self.y, self.z))
        palette = get_palette_for_biome(biome_string)

        # Set the palette attributes expected by the building methods
        self.floor = palette["foundation"]
        self.wall = palette["wall"]
        self.roof = palette["roof_stairs"], palette["roof_block"]

        # self.wall = self.transformed(*choice(self.wallPalette))
        # self.floor = self.transformed(*choice(self.floorPalette))

        self.halfWidth = self.width // 2

    def _get_bottom_y(self, lx: int, lz: int, house_tf: Transform) -> int:
        """Calculate the local terrain depth under a specific local coordinate."""
        assert self.editor.worldSlice is not None
        hm = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

        global_pos = house_tf.apply((lx, 0, lz))
        sx, sz = hm.shape

        # Bound check to protect matrix indexation
        if 0 <= global_pos.x < sx and 0 <= global_pos.z < sz:
            ground_y = hm[global_pos.x, global_pos.z]
            return min(-1, ground_y - self.y - 1)

        return -1

    def build(self) -> "BasicHouse":
        """
        Builds the house.
        :return: The house object itself
        """
        super().build()

        with self.editor.pushTransform(
            Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        ):
            self.build_foundation()
            self.build_shape()
            self.build_door()
            self.build_roof()
        return self

    def build_foundation(self) -> None:
        """Erect a solid block base beneath the house structure down to ground."""
        house_tf = Transform(
            translation=(self.x, self.y, self.z), rotation=self.rotation
        )

        # Fill the entire floor area down to the custom landscape depth
        for x in range(self.width + 1):
            for z in range(self.depth + 1):
                bottom = self._get_bottom_y(x, z, house_tf)
                # Draw foundation blocks mix up to the house floor level (0)
                for y in range(bottom, 1):
                    self.editor.placeBlock((x, y, z), choice(self.floor))

    def build_shape(self) -> None:
        """
        Builds the shape of the house and clears the interior
        :return: None
        """
        # Clear the inside of the house
        placeCuboid(
            self.editor,
            (0, 0, 0),
            (self.width, self.height, self.depth),
            Block("air"),
        )

        # Build walls
        placeCuboidHollow(
            self.editor,
            (0, 0, 0),
            (self.width, self.height, self.depth),
            self.wall,
        )

        placeCuboid(
            self.editor,
            (0, 0, 0),
            (self.width, -5, self.depth),
            self.floor,
        )

    def build_door(self) -> None:
        """
        Builds the door of the house
        :return: None
        """
        doorPosition = self.halfWidth
        # Add a door
        doorBlock = Block("oak_door", {"facing": "north", "hinge": "left"})
        self.editor.placeBlock((doorPosition, 1, 0), doorBlock)

        # Clear some space in front of the door
        placeCuboid(
            self.editor,
            (doorPosition - 1, 1, -1),
            (doorPosition + 1, 3, -1),
            Block("air"),
        )

    def build_roof(self) -> None:
        """
        Builds the roof of the house
        :return: None
        """
        # (roofStairs, roofStairsDamaged), roofBlock = choice(self.roofPalette)
        (roofStairs, roofStairsDamaged), roofBlock = self.roof

        roofStairsEast = self.transformed(
            Block(roofStairs.id, {"facing": "east"}),
            Block(roofStairsDamaged.id, {"facing": "east"}),
        )
        roofStairsWest = self.transformed(
            Block(roofStairs.id, {"facing": "west"}),
            Block(roofStairsDamaged.id, {"facing": "west"}),
        )
        roofStairsEastTop = self.transformed(
            Block(roofStairs.id, {"facing": "east", "half": "top"}),
            Block(roofStairsDamaged.id, {"facing": "east", "half": "top"}),
        )
        roofStairsWestTop = self.transformed(
            Block(roofStairs.id, {"facing": "west", "half": "top"}),
            Block(roofStairsDamaged.id, {"facing": "west", "half": "top"}),
        )

        # Build roof: loop through distance from the middle
        for dx in range(1, self.halfWidth + 2):
            yy = self.height + self.halfWidth - dx

            # Fill empty space in roof
            placeCuboid(
                self.editor,
                (self.halfWidth - dx, yy, 0),
                (self.halfWidth + dx, yy, self.depth),
                self.wall,
            )

            placeCuboid(
                self.editor,
                (self.halfWidth - dx, yy, -1),
                (self.halfWidth - dx, yy, self.depth + 1),
                roofStairsEast,
            )
            placeCuboid(
                self.editor,
                (self.halfWidth + dx, yy, -1),
                (self.halfWidth + dx, yy, self.depth + 1),
                roofStairsWest,
            )

            # Add upside-down accent blocks
            for zz in [-1, self.depth + 1]:
                self.editor.placeBlock(
                    (self.halfWidth - dx + 1, yy, zz),
                    roofStairsWestTop,
                )
                self.editor.placeBlock(
                    (self.halfWidth + dx - 1, yy, zz),
                    roofStairsEastTop,
                )

        # build the top row of the roof
        yy = self.height + self.halfWidth - 1
        placeCuboid(
            self.editor,
            (self.halfWidth, yy, -1),
            (self.halfWidth, yy, self.depth + 1),
            self.transformed(*roofBlock),
        )

    def plot(self, ax: Axes) -> "BasicHouse":
        """
        Plots the house footprint in a graphic
        :param ax: The axe to plot the house in to
        :return: The house object itself
        """

        # 0 : xz+0
        # 1 : x+3
        # 2 : xz+3
        # 3 : z+3

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
