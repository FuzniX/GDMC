from dataclasses import dataclass
from random import choice
from typing import ClassVar, Sequence

from gdpc.block import Block
from gdpc.geometry import placeCuboid, placeCuboidHollow
from gdpc.transform import Transform
from matplotlib import patches
from matplotlib.axes import Axes

from .house import House


@dataclass
class BasicHouse(House):
    """
    Dataclass representing a basic house that is built in Minecraft
    """

    floorPalette: ClassVar[Sequence[Sequence[Block]]] = [
        [Block("stone_bricks"), Block("cracked_stone_bricks")],
        [Block("cobblestone"), Block("mossy_cobblestone")],
    ]
    wallPalette: ClassVar[Sequence[Sequence[Block]]] = [
        [Block("oak_planks"), Block("birch_planks")],
        [Block("spruce_planks"), Block("dark_oak_planks")],
        [Block("white_terracotta"), Block("green_terracotta")],
    ]
    roofPalette: ClassVar[Sequence[Sequence[Sequence[Block]]]] = [
        [
            [Block("oak_stairs"), Block("birch_stairs")],
            [Block("oak_planks"), Block("birch_planks")],
        ],
        [
            [Block("spruce_stairs"), Block("dark_oak_stairs")],
            [Block("spruce_planks"), Block("dark_oak_planks")],
        ],
        # [Block("cobblestone_stairs"), Block("cobblestone")],
    ]

    def __post_init__(self) -> None:
        """
        Variables to define after initialization/instanciation
        :return: Nothing
        """
        self.wall = self.transformed(*choice(self.wallPalette))
        self.floor = self.transformed(*choice(self.floorPalette))

        self.halfWidth = self.width // 2

    def build(self) -> "BasicHouse":
        """
        Builds the house.
        :return: The house object itself
        """
        with self.editor.pushTransform(
            Transform(translation=(self.x, self.y, self.z), rotation=self.rotation)
        ):
            self.build_shape()
            self.build_door()
            self.build_roof()
        return self

    def build_shape(self) -> None:
        """
        Builds the shape of the house
        :return: None
        """
        # Build walls
        placeCuboidHollow(
            self.editor,
            (0, 0, 0),
            (self.width, self.height, self.depth),
            self.wall,
        )

        # Place blocks below to fit terrain
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
        (roofStairs, roofStairsDamaged), roofBlock = choice(self.roofPalette)

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
