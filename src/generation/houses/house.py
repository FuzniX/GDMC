from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gdpc.block import Block
from gdpc.editor import Editor
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

    def get_footprint(self) -> tuple[int, int, int, int]:
        """
        Calculates the raw bounding box (baseX, endX, baseZ, endZ) of the house
        including any external extensions (like merchant shops), without matrix bounds checking.
        """
        baseX = self.x
        baseZ = self.z

        match self.rotation:
            case 1:
                baseX = self.x - self.depth
            case 2:
                baseX = self.x - self.width
                baseZ = self.z - self.depth
            case 3:
                baseZ = self.z - self.width

        endX = baseX + 3 + (self.width if self.rotation % 2 == 0 else self.depth)
        endZ = baseZ + 3 + (self.depth if self.rotation % 2 == 0 else self.width)

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
