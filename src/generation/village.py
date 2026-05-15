import random
from dataclasses import dataclass, field
from random import randint
from typing import Callable, Optional

import matplotlib.pyplot as plt
import numpy as np
from gdpc.block import Block
from gdpc.editor import Editor

from ..simulation.player import Player
from ..simulation.simulation import Simulation
from .houses.house import House

FREE_BLOCK = 0
HOUSE_BLOCK = 1
PIRATE_BLOCK = 2
STREET_BLOCK = 3
PADDING_BLOCK = 4

STREET_SOUTH: int = 5
STREET_EAST: int = 6
STREET_NORTH: int = 7
STREET_WEST: int = 8
STREET_DIRECTIONS = [STREET_SOUTH, STREET_EAST, STREET_NORTH, STREET_WEST]


@dataclass
class Village:
    """
    Dataclass representing a village that is built in Minecraft
    """

    editor: Editor

    simulation: Simulation

    height: Callable[[], int] = lambda: randint(3, 7)
    depth: Callable[[], int] = lambda: randint(3, 10)
    width: Callable[[], int] = lambda: randint(2, 5) * 2  # Odd for a centered door
    # rotation: Callable[[], int] = lambda: randint(0, 3)

    _houses: Optional[list[House]] = field(init=False, default=None)

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

        self.generate_pirate_zone()
        self.generate_streets()

    def generate_pirate_zone(self) -> None:
        """
        Defines a fully connected zone for pirates in the houseMap before placing houses.
        The zone size is proportional to the ratio of pirates among all players.
        """
        total_players = len(self.simulation.players)
        if total_players == 0:
            return

        # Number of blocks needed for the pirate zone
        nb_pirates = len(self.simulation.pirates)
        pirate_ratio = nb_pirates / total_players
        blocks_to_place = int(self.houseMap.size * pirate_ratio)

        if blocks_to_place <= 0:
            return

        # Choose a random starting point
        size_x, size_z = self.houseMap.shape
        start_x = randint(0, size_x - 1)
        start_z = randint(0, size_z - 1)

        # Place the first pirate block
        self.houseMap[start_x, start_z] = PIRATE_BLOCK
        blocks_to_place -= 1

        # Set to track candidate frontier blocks
        frontier = set()

        def add_neighbors(x: int, z: int) -> None:
            # Neighbors (up, down, left, right)
            neighbors = [(x - 1, z), (x + 1, z), (x, z - 1), (x, z + 1)]
            for nx, nz in neighbors:
                # Check bounds and ensure the cell is empty (0)
                if 0 <= nx < size_x and 0 <= nz < size_z:
                    if self.houseMap[nx, nz] == FREE_BLOCK:
                        frontier.add((nx, nz))

        # Initialize the frontier around the starting point
        add_neighbors(start_x, start_z)

        # 3. Expand zone until required size is reached
        while blocks_to_place > 0 and frontier:
            # Select a random cell from the current frontier
            next_cell = random.choice(list(frontier))
            frontier.remove(next_cell)

            cx, cz = next_cell

            # Double-check that it hasn't been filled by a parallel choice
            if self.houseMap[cx, cz] == FREE_BLOCK:
                self.houseMap[cx, cz] = PIRATE_BLOCK
                blocks_to_place -= 1

                # Expand the frontier with the new cell's neighbors
                add_neighbors(cx, cz)

    def generate_horizontal_streets(
        self, nb_horizontal: int = 5, street_width: int = 3
    ) -> None:
        """
        Generates horizontal streets with a specific width and a surrounding padding.
        Uses a 1D array to ensure parallel streets do not overlap.
        """
        size_x, size_z = self.houseMap.shape
        occupied_z = np.zeros(size_z, dtype=int)

        radius = street_width // 2
        padding_radius = radius + 1

        for _ in range(nb_horizontal):
            for _ in range(100):  # Attempts to find a free spot
                z_center = randint(padding_radius, size_z - (padding_radius + 1))

                # Prevent parallel streets from overlapping
                if np.any(
                    occupied_z[
                        z_center - padding_radius : z_center + padding_radius + 1
                    ]
                    == 1
                ):
                    continue

                # Random horizontal span
                start_x = randint(1, size_x // 2)
                end_x = randint(size_x // 2, size_x - 2)

                # Mark street as occupied for subsequent vertical streets
                occupied_z[
                    z_center - padding_radius : z_center + padding_radius + 1
                ] = 1

                # Draw on houseMap
                for x in range(start_x - 1, end_x + 2):
                    for offset in range(-padding_radius, padding_radius + 1):
                        z = z_center + offset
                        if 0 <= x < size_x and 0 <= z < size_z:
                            # Define if we are in the street core or the padding area
                            if (start_x <= x <= end_x) and (
                                -radius <= offset <= radius
                            ):
                                # Streets can overwrite free space or existing padding (for intersections)
                                if self.houseMap[x, z] in [FREE_BLOCK, PADDING_BLOCK]:
                                    self.houseMap[x, z] = STREET_BLOCK
                            elif self.houseMap[x, z] == FREE_BLOCK:
                                # Padding only marks empty space
                                self.houseMap[x, z] = PADDING_BLOCK
                break

    def generate_vertical_streets(
        self, nb_vertical: int = 5, street_width: int = 3
    ) -> None:
        """
        Generates vertical streets with a specific width and a surrounding padding.
        Uses a 1D array to ensure parallel streets do not overlap.
        """
        size_x, size_z = self.houseMap.shape
        occupied_x = np.zeros(size_x, dtype=int)

        radius = street_width // 2
        padding_radius = radius + 1

        for _ in range(nb_vertical):
            for _ in range(100):  # Attempts to find a free spot
                x_center = randint(padding_radius, size_x - (padding_radius + 1))

                # Prevent parallel streets from overlapping
                if np.any(
                    occupied_x[
                        x_center - padding_radius : x_center + padding_radius + 1
                    ]
                    == 1
                ):
                    continue

                # Random horizontal span
                start_z = randint(1, size_z // 2)
                end_z = randint(size_z // 2, size_z - 2)

                # Mark street as occupied for subsequent vertical streets
                occupied_x[
                    x_center - padding_radius : x_center + padding_radius + 1
                ] = 1

                for z in range(start_z - 1, end_z + 2):
                    for offset in range(-padding_radius, padding_radius + 1):
                        x = x_center + offset
                        if 0 <= x < size_x and 0 <= z < size_z:
                            # Define if we are in the street core or the padding area
                            if (start_z <= z <= end_z) and (
                                -radius <= offset <= radius
                            ):
                                # Streets can overwrite free space or existing padding (for intersections)
                                if self.houseMap[x, z] in [FREE_BLOCK, PADDING_BLOCK]:
                                    self.houseMap[x, z] = STREET_BLOCK
                            elif self.houseMap[x, z] == FREE_BLOCK:
                                # Padding only marks empty space
                                self.houseMap[x, z] = PADDING_BLOCK
                break

    def place_street_direction(self, x: int, z: int) -> None:
        size_x, size_z = self.houseMap.shape
        max_dist = 5

        # South
        if np.any(
            self.houseMap[x, z + 1 : min(size_z, z + max_dist + 1)] == STREET_BLOCK
        ):
            self.houseMap[x, z] = STREET_SOUTH

        # East
        elif np.any(
            self.houseMap[x + 1 : min(size_x, x + max_dist + 1), z] == STREET_BLOCK
        ):
            self.houseMap[x, z] = STREET_EAST

        # North
        elif np.any(self.houseMap[x, max(0, z - max_dist) : z] == STREET_BLOCK):
            self.houseMap[x, z] = STREET_NORTH

        # West
        elif np.any(self.houseMap[max(0, x - max_dist) : x, z] == STREET_BLOCK):
            self.houseMap[x, z] = STREET_WEST

    def generate_streets(
        self, nb_horizontal: int = 5, nb_vertical: int = 5, street_width: int = 3
    ) -> None:
        """
        Generates streets, their padding, and marks buildable zones based on street proximity.
        """
        self.generate_horizontal_streets(nb_horizontal, street_width)
        self.generate_vertical_streets(nb_vertical, street_width)

        size_x, size_z = self.houseMap.shape

        for x in range(size_x):
            for z in range(size_z):
                if self.houseMap[x, z] == FREE_BLOCK:
                    self.place_street_direction(x, z)

    @property
    def heightmaps(self) -> np.ndarray:
        assert self.editor.worldSlice is not None
        return self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    @property
    def houses(self) -> list[House]:
        if self._houses is not None:
            return self._houses

        self._houses = []

        for player in self.simulation.players:
            house = self.get_house(player)
            self._houses.append(house)

            # Mark house as placed
            (min_x, max_x), (min_z, max_z) = self.get_house_footprint(house)
            self.houseMap[min_x:max_x, min_z:max_z] = 1

        return self._houses

    def rotation(self, x: int, z: int) -> int:
        value = self.houseMap[x, z]

        if value == STREET_SOUTH:
            return 2
        elif value == STREET_NORTH:
            return 0
        elif value == STREET_WEST:
            return 3
        elif value == STREET_EAST:
            return 1
        else:
            return 0

    def get_house(self, player: Player) -> House:
        for _ in range(100_000):
            house = player.house(
                editor=self.editor,
                x=(x := randint(self.x, self.endX)),
                z=(z := randint(self.z, self.endZ)),
                y=self.heightmaps[x - self.x, z - self.z] - 1,
                # height=self.height(),
                # depth=self.depth(),
                # width=self.width(),
                # rotation=self.rotation(x - self.x, z - self.z),
                rotation=randint(0, 3),
            )

            if self.can_place_house(house):
                break
        else:
            raise HouseOverlapError("Impossible to place house")

        return house

    def build(self) -> None:
        """
        Builds the village
        :return: None
        """
        self.build_zones()

        for house in self.houses:
            house.build()

    def build_zones(self) -> None:
        """
        Physically places blocks in Minecraft based on the houseMap values.
        - Value 2 (Pirates) -> black_concrete
        - Value 3 (Streets) -> dirt_path
        """
        size_x, size_z = self.houseMap.shape

        for x_map in range(size_x):
            for z_map in range(size_z):
                val = self.houseMap[x_map, z_map]

                world_x = self.x + x_map - 1
                world_z = self.z + z_map - 1
                world_y = self.heightmaps[x_map, z_map] - 1

                if val == 2:  # Pirate Zone
                    self.editor.placeBlock(
                        (world_x, world_y, world_z), Block("black_concrete")
                    )

                elif val == 3:  # Street Zone
                    self.editor.placeBlock(
                        (world_x, world_y, world_z), Block("dirt_path")
                    )

    def get_house_footprint(
        self, house: House
    ) -> tuple[tuple[int, int], tuple[int, int]]:
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
            (max(baseZ, 0), min(endZ, self.houseMap.shape[1])),
        )

    def can_place_house(self, house: House) -> bool:
        """
        Returns True if the house can be placed:
        1. Area is clear of obstacles.
        2. At least one block is a street-adjacent zone.
        3. The house rotation matches the direction of the street.
        """
        (min_x, max_x), (min_z, max_z) = self.get_house_footprint(house)

        if min_x >= max_x or min_z >= max_z:
            return False

        house_zone = self.houseMap[min_x:max_x, min_z:max_z]

        # Whether the zone is clear
        is_clear = np.all(np.isin(house_zone, [FREE_BLOCK, *STREET_DIRECTIONS]))
        if not is_clear:
            return False

        # Find local coordinates of street blocks
        mask_street = np.isin(house_zone, STREET_DIRECTIONS)
        street_indices = np.argwhere(mask_street)

        if len(street_indices) == 0:
            return False  # No nearby street blocks

        # Check rotation compatibility
        for local_x, local_z in street_indices:
            # Convert local coordinates to absolute map coordinates
            abs_x = min_x + local_x
            abs_z = min_z + local_z

            # Check if the street block rotation matches the house rotation
            if self.rotation(abs_x, abs_z) == house.rotation:
                return True  # Found at least one street block that matches the house rotation

        return False  # No street block matches the house rotation

    def plot(self) -> None:
        """
        Plots the terrain and the village footprint
        :return: None
        """
        fig, ax = plt.subplots()

        # Load world slice again so it's the version after build
        self.editor.loadWorldSlice(cache=True)

        im = ax.imshow(
            self.heightmaps.T,
            cmap="inferno",
            origin="lower",
            extent=(self.x, self.endX, self.z, self.endZ),
        )
        plt.colorbar(im, label="Y")

        for house in self.houses:
            house.plot(ax)

        ax.invert_xaxis()

        plt.title("Build Area")
        plt.xlabel("X")
        plt.ylabel("Z")

    def plot_houseMap(self):
        fig, ax = plt.subplots()

        im = plt.imshow(
            self.houseMap.T,
            cmap="inferno",
            origin="lower",
            extent=(self.x, self.endX, self.z, self.endZ),
        )

        for house in self.houses:
            house.plot(ax)

        plt.colorbar(im, label="Built")
        ax.invert_xaxis()

        plt.title("Build Area")
        plt.xlabel("X")
        plt.ylabel("Z")


class HouseOverlapError(Exception):
    def __init__(self, message):
        super().__init__(message)
