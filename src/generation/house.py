from dataclasses import dataclass, field
from random import choice
from typing import Sequence

from gdpc import Block, Editor, Transform
from gdpc.geometry import placeCuboid, placeCuboidHollow
from matplotlib import patches
from mpl_toolkits.axes_grid1.mpl_axes import Axes


@dataclass
class House:
    """
    Dataclass representing a house that is built in Minecraft
    """

    editor: Editor

    x: int
    y: int
    z: int

    height: int
    depth: int
    width: int
    rotation: int

    floorPalette: Sequence[Block]
    wallPalette: Sequence[Block]
    roofPalette: Sequence[Sequence[Block]]

    wallBlock: Block = field(init=False)
    halfWidth: int = field(init=False)

    def __post_init__(self) -> None:
        """
        Variables to define after initialization/instanciation
        :return: Nothing
        """
        # Choose wall material
        self.wallBlock = choice(self.wallPalette)

        self.halfWidth = self.width // 2

    def build(self) -> "House":
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
            self.wallBlock,
        )

        # Place blocks below to fit terrain
        placeCuboid(
            self.editor, (0, 0, 0), (self.width, -5, self.depth), self.floorPalette
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
        roofStairs, roofBlock = choice(self.roofPalette)
        # Build roof: loop through distance from the middle
        for dx in range(1, self.halfWidth + 2):
            yy = self.height + self.halfWidth - dx

            # Fill empty space in roof
            placeCuboid(
                self.editor,
                (self.halfWidth - dx, yy, 0),
                (self.halfWidth + dx, yy, self.depth),
                self.wallBlock,
            )

            # Build row of stairs blocks
            leftBlock = Block(roofStairs.id, {"facing": "east"})
            rightBlock = Block(roofStairs.id, {"facing": "west"})
            placeCuboid(
                self.editor,
                (self.halfWidth - dx, yy, -1),
                (self.halfWidth - dx, yy, self.depth + 1),
                leftBlock,
            )
            placeCuboid(
                self.editor,
                (self.halfWidth + dx, yy, -1),
                (self.halfWidth + dx, yy, self.depth + 1),
                rightBlock,
            )

            # Add upside-down accent blocks
            leftBlock = Block(roofStairs.id, {"facing": "west", "half": "top"})
            rightBlock = Block(roofStairs.id, {"facing": "east", "half": "top"})
            for zz in [-1, self.depth + 1]:
                self.editor.placeBlock((self.halfWidth - dx + 1, yy, zz), leftBlock)
                self.editor.placeBlock((self.halfWidth + dx - 1, yy, zz), rightBlock)

        # build the top row of the roof
        yy = self.height + self.halfWidth - 1
        placeCuboid(
            self.editor,
            (self.halfWidth, yy, -1),
            (self.halfWidth, yy, self.depth + 1),
            roofBlock,
        )

    def plot(self, ax: Axes) -> "House":
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
