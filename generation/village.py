from dataclasses import dataclass, field
from random import randint
from typing import Sequence, Callable

import matplotlib.pyplot as plt
import numpy as np
from gdpc import Block, Editor
from numpy import ndarray

from house import House


@dataclass
class Village:
    """
    Dataclass representing a village that is built in Minecraft
    """
    editor: Editor
    heightmap: ndarray

    floorPalette: Sequence[Block]
    wallPalette: Sequence[Block]
    roofPalette: Sequence[Sequence[Block]]

    x: int = field(init=False)
    z: int = field(init=False)
    endX: int = field(init=False)
    endZ: int = field(init=False)

    houseNumber: int
    houses: list[House] = field(default_factory=list)
    houseMap: ndarray = field(init=False)

    height: Callable[[], int] = lambda: randint(3, 7)
    depth: Callable[[], int] = lambda: randint(3, 10)
    width: Callable[[], int] = lambda: randint(2, 5) * 2  # Odd for a centered door
    rotation: Callable[[], int] = lambda: randint(0, 3)

    def __post_init__(self) -> None:
        """
        Variables to define after initialization/instanciation.
        Prepares the houses to build.
        :return: None
        """
        buildArea = self.editor.getBuildArea()
        self.x = buildArea.begin.x + 1
        self.z = buildArea.begin.z + 1
        self.endX = buildArea.end.x
        self.endZ = buildArea.end.z
        self.houseMap = np.zeros((buildArea.size.x, buildArea.size.z))
        
        for _ in range(self.houseNumber):
            self.add_house()

    def get_house(self) -> House:
        """
        Prepares a house with given properties.
        :return: A new house
        """
        return House(
            editor=self.editor,
            x=(x := randint(self.x, self.endX)),
            z=(z := randint(self.z, self.endZ)),
            y=self.heightmap[x - self.x, z - self.z] - 1,
            height=self.height(),
            depth=self.depth(),
            width=self.width(),
            rotation=self.rotation(),
            floorPalette=self.floorPalette,
            wallPalette=self.wallPalette,
            roofPalette=self.roofPalette,
        )
    
    def build(self) -> None:
        """
        Builds the village
        :return: None
        """
        for house in self.houses:
            house.build()
    
    def plot(self) -> None:
        """
        Plots the terrain and the village footprint
        :return: None
        """
        fig, ax = plt.subplots()

        self.editor.loadWorldSlice(cache=True)
        heightmap = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

        im = ax.imshow(
            heightmap.T,
            cmap="inferno",
            origin="lower",
            extent=(self.x, self.endX, self.z, self.endZ))
        plt.colorbar(im, label='Y')

        for house in self.houses:
            house.plot(ax)

        ax.invert_xaxis()

        plt.title("Build Area")
        plt.xlabel("X")
        plt.ylabel("Z")

    def get_house_footprint(self, house: House) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        Get a given house's footprint i.e. where it is placed in the terrain
        :param house: 
        :return: A tuple of base and end coordinates
        """
        # Base coordinates
        baseX = house.x - self.x
        baseZ = house.z - self.z
        
        # Can be different depending on the rotation of the house
        match house.rotation:
            case 1:
                baseX = house.x - self.x - house.depth
            case 2:
                baseX = house.x - self.x - house.width
                baseZ = house.z - self.z - house.depth
            case 3:
                baseZ = house.z - self.z - house.width
        
        # Coordinates of the opposite corner
        endX = baseX + 3 + (house.width if house.rotation % 2 == 0 else house.depth)
        endZ = baseZ + 3 + (house.depth if house.rotation % 2 == 0 else house.width)
        
        # Make sure the region is in the matrix
        return (
            (max(baseX, 0), min(endX, self.houseMap.shape[0])),
            (max(baseZ, 0), min(endZ, self.houseMap.shape[1]))
        )

    def can_place_house(self, footprint: tuple[tuple[int, int], tuple[int, int]]) -> bool:
        """
        Returns whether a house can be placed at a given place
        :param footprint: The place to define whether the house can be placed
        :return: A boolean
        """
        (min_x, max_x), (min_z, max_z) = footprint

        if min_x >= max_x or min_z >= max_z: # off limits
            return False

        PADDING = 5
        
        return not np.any(self.houseMap[min_x-PADDING:max_x+PADDING, min_z-PADDING:max_z+PADDING]) # Nothing in the zone?

    def add_house(self) -> None:
        """
        Adds a house to the village
        :return: 
        """
        for _ in range(100_000): # Limit to 100 iterations
            house = self.get_house()
            footprint = self.get_house_footprint(house)
            (min_x, max_x), (min_z, max_z) = footprint
            
            if self.can_place_house(footprint):
                self.houseMap[min_x:max_x, min_z:max_z] = 1
                self.houses.append(house)
                break
        else:
            raise HouseOverlapError("Impossible to place house")
        
    def plot_houseMap(self):
        fig, ax = plt.subplots()

        im = plt.imshow(
            self.houseMap.T,
            cmap="inferno",
            origin="lower",
            extent=(self.x, self.endX, self.z, self.endZ)
        )

        for house in self.houses:
            house.plot(ax)

        plt.colorbar(im, label='Built')
        ax.invert_xaxis()

        plt.title("Build Area")
        plt.xlabel("X")
        plt.ylabel("Z")
        
        
class HouseOverlapError(Exception):
    def __init__(self, message):
        super().__init__(message)