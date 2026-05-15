from abc import abstractmethod
from dataclasses import dataclass
from typing import TYPE_CHECKING

from gdpc.editor import Editor
from matplotlib.axes import Axes

if TYPE_CHECKING:
    from src.simulation.player import Player


@dataclass
class House:
    """
    Dataclass representing a house that is built in Minecraft
    """

    player: Player

    editor: Editor

    x: int
    y: int
    z: int

    height: int
    depth: int
    width: int
    rotation: int

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
