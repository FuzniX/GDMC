import random
from dataclasses import dataclass, field
from random import randint
from typing import Callable, Generator, Optional

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
STREET_ROTATIONS = {
    STREET_NORTH: 0,
    STREET_EAST: 1,
    STREET_SOUTH: 2,
    STREET_WEST: 3,
}


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
        self.buildArea = self.editor.getBuildArea()
        self.houseMap = np.zeros((self.buildArea.size.x, self.buildArea.size.z))

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

        # Expand zone until required size is reached
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

    def generate_horizontal_streets(self, nb: int = 5, width: int = 3) -> None:
        """
        Generates horizontal streets with a specific width and a surrounding padding.
        Uses a 1D array to ensure parallel streets do not overlap.
        """
        size_x, size_z = self.houseMap.shape
        occupied_z = np.zeros(size_z, dtype=int)
        placed = 0

        radius = width // 2
        padding = radius + 1

        for _ in range(100_000):  # Attempts to find a free spot
            z_center = randint(padding, size_z - (padding + 1))

            # Prevent parallel streets from overlapping
            if np.any(occupied_z[z_center - padding : z_center + padding + 1] == 1):
                continue

            # Random horizontal span
            start_x = randint(1, size_x // 2)
            end_x = randint(size_x // 2, size_x - 2)

            # Mark street as occupied for subsequent vertical streets
            occupied_z[z_center - padding : z_center + padding + 1] = 1

            # Full area
            x_slice = slice(max(0, start_x - 1), min(size_x, end_x + 2))
            z_slice = slice(
                max(0, z_center - padding),
                min(size_z, z_center + padding + 1),
            )

            # Apply padding with mask
            padding_mask = self.houseMap[x_slice, z_slice] == FREE_BLOCK
            self.houseMap[x_slice, z_slice][padding_mask] = PADDING_BLOCK

            # Overwrite the street core
            core_x_slice = slice(start_x, end_x + 1)
            core_z_slice = slice(z_center - radius, z_center + radius + 1)
            street_mask = self.houseMap[core_x_slice, core_z_slice] != PIRATE_BLOCK
            self.houseMap[core_x_slice, core_z_slice][street_mask] = STREET_BLOCK

            placed += 1
            if placed == nb:
                return

    def generate_vertical_streets(self, nb: int = 5, width: int = 3) -> None:
        """
        Generates vertical streets with a specific width and a surrounding padding.
        Uses a 1D array to ensure parallel streets do not overlap.
        """
        size_x, size_z = self.houseMap.shape
        occupied_x = np.zeros(size_x, dtype=int)
        placed = 0

        radius = width // 2
        padding = radius + 1

        for _ in range(100_000):  # Attempts to find a free spot
            x_center = randint(padding, size_x - (padding + 1))

            # Prevent parallel streets from overlapping
            if np.any(occupied_x[x_center - padding : x_center + padding + 1] == 1):
                continue

            # Random horizontal span
            start_z = randint(1, size_z // 2)
            end_z = randint(size_z // 2, size_z - 2)

            # Mark street as occupied for subsequent vertical streets
            occupied_x[x_center - padding : x_center + padding + 1] = 1

            # Full area
            x_slice = slice(
                max(0, x_center - padding), min(size_x, x_center + padding + 1)
            )
            z_slice = slice(max(0, start_z - 1), min(size_z, end_z + 2))

            # Apply padding with mask
            padding_mask = self.houseMap[x_slice, z_slice] == FREE_BLOCK
            self.houseMap[x_slice, z_slice][padding_mask] = PADDING_BLOCK

            # Overwrite street core
            core_x_slice = slice(x_center - radius, x_center + radius + 1)
            core_z_slice = slice(start_z, end_z + 1)
            street_mask = self.houseMap[core_x_slice, core_z_slice] != PIRATE_BLOCK
            self.houseMap[core_x_slice, core_z_slice][street_mask] = STREET_BLOCK

            placed += 1
            if placed == nb:
                return

    def place_street_positions(self) -> None:
        max_dist = 5

        for get_street_slice, get_target_slice, direction in zip(
            [  # Street slices
                lambda d: (slice(None), slice(d, None)),  # South
                lambda d: (slice(d, None), slice(None)),  # East
                lambda d: (slice(None), slice(None, -d)),  # North
                lambda d: (slice(None, -d), slice(None)),  # West
            ],
            [  # Target slices
                lambda d: (slice(None), slice(None, -d)),  # South
                lambda d: (slice(None, -d), slice(None)),  # East
                lambda d: (slice(None), slice(d, None)),  # North
                lambda d: (slice(d, None), slice(None)),  # West
            ],
            STREET_DIRECTIONS,
        ):
            for d in range(1, max_dist + 1):
                s_slice = get_street_slice(d)
                t_slice = get_target_slice(d)

                # Identify where streets are in the view
                street_found = self.houseMap[s_slice] == STREET_BLOCK
                target_view = self.houseMap[t_slice]

                # Apply direction only to free blocks
                mask = (target_view == FREE_BLOCK) & street_found
                target_view[mask] = direction

    def generate_streets(
        self, nb_horizontal: int = 5, nb_vertical: int = 5, width: int = 3
    ) -> None:
        """
        Generates streets, their padding, and marks buildable zones based on street proximity.
        """
        self.generate_horizontal_streets(nb_horizontal, width)
        self.generate_vertical_streets(nb_vertical, width)
        self.place_street_positions()

    @property
    def heightmaps(self) -> np.ndarray:
        assert self.editor.worldSlice is not None
        return self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    @property
    def houses(self) -> Generator[House, None, list[House]]:
        if self._houses is not None:
            return self._houses

        self._houses = []

        for player in self.simulation.players:
            house = self.get_house(player)
            self._houses.append(house)

            # Mark house as placed
            (min_x, max_x), (min_z, max_z) = self.get_house_footprint(house)
            self.houseMap[min_x:max_x, min_z:max_z] = 1

            yield house

        return self._houses

    def get_house(self, player: Player) -> House:
        for _ in range(100_000):
            house = player.house(
                editor=self.editor,
                x=(x := randint(0, self.buildArea.size.x - 1)),
                z=(z := randint(0, self.buildArea.size.z - 1)),
                y=self.heightmaps[x, z] - 1,
                # height=self.height(),
                # depth=self.depth(),
                # width=self.width(),
                # rotation=self.rotation(x, z),
                rotation=randint(0, 3),
            )

            if self.can_place_house(house):
                break
        else:
            raise HouseOverlapError("Impossible to place house")

        return house

    def rotation(self, x: int, z: int) -> int:
        return STREET_ROTATIONS[self.houseMap[x, z]]

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
        Physically places blocks in Minecraft using NumPy masks and coordinate iteration.
        """
        # Pirates
        for x, z in np.argwhere(self.houseMap == PIRATE_BLOCK):
            self.editor.placeBlock(
                (x, self.heightmaps[x, z] - 1, z), Block("black_concrete")
            )

        # Streets
        for x, z in np.argwhere(self.houseMap == STREET_BLOCK):
            self.editor.placeBlock(
                (x, self.heightmaps[x, z] - 1, z), Block("dirt_path")
            )

    def get_house_footprint(
        self, house: House
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        """
        Get a given house's footprint i.e. where it is placed in the terrain
        :param house:
        :return: A tuple of base and end coordinates
        """
        baseX, endX, baseZ, endZ = house.get_footprint()

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
            extent=(
                self.buildArea.begin.x,
                self.buildArea.end.x,
                self.buildArea.begin.z,
                self.buildArea.end.z,
            ),
        )
        plt.colorbar(im, label="Y")

        assert self._houses is not None
        for house in self._houses:
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
            extent=(
                self.buildArea.begin.x,
                self.buildArea.end.x,
                self.buildArea.begin.z,
                self.buildArea.end.z,
            ),
        )

        assert self._houses is not None
        for house in self._houses:
            house.plot(ax)

        plt.colorbar(im, label="Built")
        ax.invert_xaxis()

        plt.title("Build Area")
        plt.xlabel("X")
        plt.ylabel("Z")


class HouseOverlapError(Exception):
    def __init__(self, message):
        super().__init__(message)
