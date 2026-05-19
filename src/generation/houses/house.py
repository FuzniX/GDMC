from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gdpc.block import Block
from gdpc.editor import Editor
from gdpc.transform import Transform
from matplotlib.axes import Axes

from src.simulation.enums import InfectionStatus
from src.utils import mix

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

    editor: Editor

    x: int
    y: int
    z: int

    height: int
    depth: int
    width: int
    rotation: int

    @property
    def block_proportion(self) -> dict[str, int]:
        """
        The proportion of cobweb in the house.
        :return: The cobweb proportion
        """
        return BLOCK_PROPORTION[self.player.infection_status]

    def transformed(self, normal: Block, damaged: Block) -> list[Block]:
        """
        The cobweb blocks in the house.
        :return: The cobweb blocks
        """
        return mix(
            [
                (normal, self.block_proportion["normal"]),
                (damaged, self.block_proportion["damaged"]),
                (COBWEB, self.block_proportion["cobweb"]),
                (AIR, self.block_proportion["air"]),
            ]
        )

    def get_local_footprint(self) -> tuple[int, int, int, int]:
        """
        Calculates the local bounding box (minX, maxX, minZ, maxZ)
        relative to (0,0).
        """
        return -1, self.width + 1, -1, self.depth

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

    @abstractmethod
    def build(self) -> "House":
        """
        Builds the house.
        :return: The house object itself
        """

    @abstractmethod
    def plot(self, ax: Axes) -> "House":
        """
        Plots the house footprint in a graphic
        :param ax: The axe to plot the house in to
        :return: The house object itself
        """
