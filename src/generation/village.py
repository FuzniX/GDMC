import random
import time
from dataclasses import dataclass, field
from random import choice, randint
from typing import Callable, Generator, Optional

import matplotlib.pyplot as plt
import numpy as np
from gdpc.block import Block

from src.utils import CustomEditor, get_palette_for_biome

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

# Organic Block Spiral
# Forces paths to wrap around the center before splitting, leaving large open blocks for houses.
LSYSTEM_AXIOME_SPIRAL = "F+F+F+F"
LSYSTEM_RULES_SPIRAL = {
    "F": [
        "F[+F]FF",  # Long straight path with a right branch
        "F[-F]FF",  # Long straight path with a left branch
        "FF",  # Pure extension to push intersections away
    ]
}

# Major Trunk Dividers
# Acts like a tree outline that splits into huge secondary sectors right from the start.
LSYSTEM_AXIOME_DIVIDER = "[F][+F][-F][++F]"
LSYSTEM_RULES_DIVIDER = {
    # "F": ["FF[+F][-F]F"]
    "F": [
        "F+F[-F]",
        "F-F[+F]",
        "FF",
    ]
}


@dataclass
class Village:
    """
    Dataclass representing a village that is built in Minecraft
    """

    editor: CustomEditor

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
        assert self.editor.worldSlice is not None
        self.heightmaps = self.editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]
        self.buildArea = self.editor.getBuildArea()
        self.houseMap = np.zeros((self.buildArea.size.x, self.buildArea.size.z))

        self._sanitize_heightmap_vegetation()
        self._generate_pirate_zone()
        self._generate_streets()

    def _generate_pirate_zone(self) -> None:
        """
        Defines a fully connected zone for pirates in the houseMap before placing houses.
        The zone size is proportional to the ratio of pirates among all players.
        """
        total_players = len(self.simulation.players)
        if total_players == 0:
            return

        # Number of blocks needed for the pirate zone
        nb_pirates = len(self.simulation.pirates)
        pirate_ratio = nb_pirates / total_players / 2
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
        frontier = []
        visited = set()

        def add_neighbors(x: int, z: int) -> None:
            # Neighbors (up, down, left, right)
            neighbors = [(x - 1, z), (x + 1, z), (x, z - 1), (x, z + 1)]
            for nx, nz in neighbors:
                # Check bounds and ensure the cell is empty (0)
                if 0 <= nx < size_x and 0 <= nz < size_z:
                    if self.houseMap[nx, nz] == FREE_BLOCK and (nx, nz) not in visited:
                        frontier.append((nx, nz))
                        visited.add((nx, nz))  # Marked as seen

        # Initialize the frontier around the starting point
        visited.add((start_x, start_z))
        add_neighbors(start_x, start_z)

        # Expand zone until required size is reached
        while blocks_to_place > 0 and frontier:
            # Select a random cell from the current frontier
            idx = randint(0, len(frontier) - 1)
            cx, cz = frontier[idx]
            frontier[idx] = frontier[-1]  # Remplace par le dernier
            frontier.pop()  # Supprime le dernier

            # Double-check that it hasn't been filled by a parallel choice
            if self.houseMap[cx, cz] == FREE_BLOCK:
                self.houseMap[cx, cz] = PIRATE_BLOCK
                blocks_to_place -= 1
                # Expand the frontier with the new cell's neighbors
                add_neighbors(cx, cz)

    def _expand_lsystem(self, iterations: int) -> str:
        """Expand axiom rules into a command sequence using choices."""
        commands = LSYSTEM_AXIOME_DIVIDER
        for _ in range(iterations):
            next_seq = ""
            for char in commands:
                if char in LSYSTEM_RULES_DIVIDER:
                    next_seq += choice(LSYSTEM_RULES_DIVIDER[char])
                else:
                    next_seq += char
            commands = next_seq
        return commands

    def _paint_street_block(self, cx: int, cz: int, r: int, p: int) -> None:
        """Apply core street and padding slices onto the houseMap matrix."""
        sx, sz = self.houseMap.shape

        # Draw surrounding road padding blocks
        x_pad = slice(max(0, cx - p), min(sx, cx + p + 1))
        z_pad = slice(max(0, cz - p), min(sz, cz + p + 1))
        pad_mask = self.houseMap[x_pad, z_pad] == FREE_BLOCK
        self.houseMap[x_pad, z_pad][pad_mask] = PADDING_BLOCK

        # Draw solid central street blocks
        x_core = slice(max(0, cx - r), min(sx, cx + r + 1))
        z_core = slice(max(0, cz - r), min(sz, cz + r + 1))
        str_mask = self.houseMap[x_core, z_core] != PIRATE_BLOCK
        self.houseMap[x_core, z_core][str_mask] = STREET_BLOCK

    def _trace_forward(
        self, state: list, move: tuple, step: int, limit: int, r: int, p: int
    ) -> list:
        """Move the turtle forward, tracking slopes and drawing the street."""
        cx, cz, angle = state
        dx, dz = move
        sx, sz = self.houseMap.shape

        for _ in range(step):
            nx, nz = cx + dx, cz + dz

            # Map boundaries guard check
            if not (0 <= nx < sx and 0 <= nz < sz):
                break

            # Height slope guard check
            if abs(self.heightmaps[nx, nz] - self.heightmaps[cx, cz]) > limit:
                break

            cx, cz = nx, nz
            self._paint_street_block(cx, cz, r, p)

        return [cx, cz, angle]

    def _generate_streets(
        self,
        iterations: int = 3,
        step_length: int = 24,
        width: int = 3,
        max_slope: int = 2,
    ) -> None:
        """Generate a structured connected orthogonal street matrix network."""
        sx, sz = self.houseMap.shape
        commands = self._expand_lsystem(iterations)

        # Execution parameters
        prob = 0.75
        radius, padding = width // 2, (width // 2) + 1
        directions = {0: (0, -1), 90: (1, 0), 180: (0, 1), 270: (-1, 0)}

        # Structural states tracking
        state = [sx // 2, sz // 2, 0]  # cx, cz, angle_deg
        stack = []
        skip_depth = 0

        for cmd in commands:
            # Handle skipped branch depth nesting
            if skip_depth > 0:
                if cmd == "[":
                    skip_depth += 1
                elif cmd == "]":
                    skip_depth -= 1
                continue

            if cmd == "F":
                move_vec = directions[state[2]]
                state = self._trace_forward(
                    state, move_vec, step_length, max_slope, radius, padding
                )
            elif cmd == "+":
                state[2] = (state[2] + 90) % 360
            elif cmd == "-":
                state[2] = (state[2] - 90) % 360
            elif cmd == "[":
                # Drop branch execution based on probability constraint
                if random.random() > prob:
                    skip_depth = 1
                else:
                    stack.append(tuple(state))
            elif cmd == "]" and stack:
                state = list(stack.pop())

        self._clean_street_vegetation()

        # Build building borders layout
        self._place_street_positions()

    def _place_street_positions(self) -> None:
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

    @property
    def houses(self) -> Generator[House, None, list[House]]:
        if self._houses is not None:
            return self._houses

        self._houses = []

        random.shuffle(self.simulation.players)

        for player in self.simulation.players:
            try:
                house = self.get_house(player)
                self._houses.append(house)

                # Mark house as placed
                (min_x, max_x), (min_z, max_z) = self.get_house_footprint(house)
                self.houseMap[min_x:max_x, min_z:max_z] = 1

                yield house

            except HouseOverlapError:
                pass

        return self._houses

    def get_house(self, player: Player) -> House:
        """
        Finds a valid placement for a player's house by targeting
        existing streets to maximize performance.
        """
        # Locate coordinates of all directional street tiles
        street_mask = np.isin(self.houseMap, STREET_DIRECTIONS)
        street_coords = np.argwhere(street_mask)

        if street_coords.size == 0:
            raise HouseOverlapError("No streets found to place a house.")

        # Convert matrix matches into a list and shuffle positions
        candidates = [tuple(coord) for coord in street_coords]
        random.shuffle(candidates)

        # Iterate through shuffled path tiles to find a valid layout match
        for x, z in candidates:
            ground_y = self.heightmaps[x, z]

            # Randomize orientation choices for structural diversity
            rotations = [0, 1, 2, 3]
            random.shuffle(rotations)

            for rot in rotations:
                house = player.house(
                    editor=self.editor,
                    x=x,
                    z=z,
                    y=ground_y,
                    rotation=rot,
                )

                if self.can_place_house(house):
                    return house

        # Raise an exception if the grid space is completely saturated
        raise HouseOverlapError("Impossible to place house after scanning paths.")

    def _get_true_ground_y(self, x: int, z: int, raw_y: int) -> int:
        """
        Scans downwards from the raw heightmap Y to find the actual solid
        ground, skipping logs.
        """
        current_y = raw_y
        # Blocks we want to ignore when looking for the ground
        ignored_keywords = [
            "leaves",
            "log",
            "wood",
            "air",
            "plant",
            "flower",
            "snow",
            "fern",
            "_grass",
            "bamboo",
            "leaf_litter",
        ]

        while current_y > -64:
            block = self.editor.getBlock((x, current_y, z))
            assert block.id is not None

            # Check if the block is an tree/vegetation element
            is_vegetation = any(key in block.id for key in ignored_keywords)

            if not is_vegetation:
                # We found real ground (grass_block, dirt, sand, stone, etc.)
                return current_y

            current_y -= 1

        return raw_y

    def _sanitize_heightmap_vegetation(self) -> None:
        """Filter the entire heightmap matrix to remove tree height bumps."""
        size_x, size_z = self.houseMap.shape
        for x in range(size_x):
            for z in range(size_z):
                raw_y = self.heightmaps[x, z]
                # Overwrite with the filtered flat ground elevation
                self.heightmaps[x, z] = self._get_true_ground_y(x, z, raw_y)

    def _clean_street_vegetation(self, max_check_height: int = 15) -> None:
        """Scan all drawn streets and trigger wood/leaves vaporization."""
        street_coords = np.argwhere(self.houseMap == STREET_BLOCK)

        for x, z in street_coords:
            ground_y = self.heightmaps[x, z]
            # Look for tree parts on or floating directly above the street
            for y in range(ground_y + 1, ground_y + max_check_height):
                block = self.editor.getBlock((x, y, z))
                assert block.id is not None
                if self.editor.is_tree_block(block.id):
                    self.editor.destroy_tree_flood_fill((x, y, z))

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
                (x, self.heightmaps[x, z], z), Block("black_concrete")
            )

        # Streets
        for x, z in np.argwhere(self.houseMap == STREET_BLOCK):
            biome_string = self.editor.getBiome((x, int(self.heightmaps[x, z]), z))
            palette = get_palette_for_biome(biome_string)
            self.editor.placeBlock((x, self.heightmaps[x, z], z), palette["street"])

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

        mask_street = np.isin(house_zone, STREET_DIRECTIONS)
        mask_free = house_zone == FREE_BLOCK

        # Whether the zone is clear or is in a street-adjacent zone
        if not np.all(mask_free | mask_street):
            return False

        # Find local coordinates of street blocks
        street_indices = np.argwhere(mask_street)

        if street_indices.size == 0:
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
