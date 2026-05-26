from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gdpc.block import Block
from gdpc.transform import Transform
from matplotlib.axes import Axes

from src.simulation.enums import InfectionStatus
from src.utils import CustomEditor, mix

if TYPE_CHECKING:
    from src.simulation.player import Player

AIR: Block = Block("air")
COBWEB: Block = Block("cobweb")
BLOCK_PROPORTION: dict[InfectionStatus, dict[str, int]] = {
    InfectionStatus.Susceptible: {
        "normal": 100,  # %
        "cobweb": 0,  # %
        "damaged": 0,  # %
        "air": 0,  # %
    },
    InfectionStatus.Exposed: {
        "normal": 80,  # %
        "cobweb": 10,  # %
        "damaged": 10,  # %
        "air": 0,  # %
    },
    InfectionStatus.Infected: {
        "normal": 50,  # %
        "cobweb": 20,  # %
        "damaged": 20,  # %
        "air": 10,  # %
    },
    InfectionStatus.Dead: {
        "normal": 20,  # %
        "cobweb": 15,  # %
        "damaged": 15,  # %
        "air": 50,  # %
    },
    InfectionStatus.Recovered: {
        "normal": 100,  # %
        "cobweb": 0,  # %
        "damaged": 0,  # %
        "air": 0,  # %
    },
}


@dataclass
class House[P: Player]:
    """
    Dataclass representing a house that is built in Minecraft
    """

    player: P

    editor: CustomEditor

    x: int
    y: int
    z: int

    height: int
    depth: int
    width: int
    rotation: int

    def transformed(self, normal: Block, damaged: Block) -> list[Block]:
        """
        The cobweb blocks in the house.
        :return: The cobweb blocks
        """
        props = BLOCK_PROPORTION[self.player.infection_status]
        return mix(
            [
                (normal, props["normal"]),
                (damaged, props["damaged"]),
                (COBWEB, props["cobweb"]),
                (AIR, props["air"]),
            ]
        )

    def get_local_footprint(self) -> tuple[int, int, int, int]:
        """
        Calculates the local bounding box (minX, maxX, minZ, maxZ)
        relative to (0,0).
        """
        return -1, self.width + 1, -1, self.depth + 1

    def get_footprint(self) -> tuple[int, int, int, int]:
        """
        Transforms the unrotated local footprint boundaries into global world coordinates
        """
        min_x, max_x, min_z, max_z = self.get_local_footprint()

        # Instantiate the exact spatial translation and rotation matrix
        house_transform = Transform(
            translation=(self.x, self.y, self.z), rotation=self.rotation
        )

        # Map the 4 local 3D corners of the local bounding box layout
        local_corners = [
            (min_x, 0, min_z),
            (max_x, 0, min_z),
            (min_x, 0, max_z),
            (max_x, 0, max_z),
        ]

        # Process corners through the transform to project them into global world space
        global_corners = [house_transform.apply(corner) for corner in local_corners]

        # Extract extreme limits to form the final globally aligned 2D bounding box
        baseX = min(c[0] for c in global_corners)
        endX = max(c[0] for c in global_corners)
        baseZ = min(c[2] for c in global_corners)
        endZ = max(c[2] for c in global_corners)

        return baseX, endX, baseZ, endZ

    def clean_vegetation(self) -> None:
        """Scan the house 3D footprint space to clear intersecting trees."""
        baseX, endX, baseZ, endZ = self.get_footprint()

        # Delegate the 3D boundary cleaning task directly to the CustomEditor
        self.editor.clean_vegetation_area(
            min_x=baseX,
            max_x=endX,
            min_z=baseZ,
            max_z=endZ,
            min_y=self.y,
            max_y=self.y + self.height,
        )

    @abstractmethod
    def build(self) -> "House":
        """
        Builds the house.
        :return: The house object itself
        """
        self.clean_vegetation()

    @abstractmethod
    def plot(self, ax: Axes) -> "House":
        """
        Plots the house footprint in a graphic
        :param ax: The axe to plot the house in to
        :return: The house object itself
        """
