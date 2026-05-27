import heapq
import math
import random
from dataclasses import dataclass, field
from random import choice, randint
from typing import Callable, Generator, Optional

import matplotlib.pyplot as plt
import numpy as np
from gdpc.block import Block

from src.generation.houses.pirate_house import PirateHouse
from src.generation.houses.pirate_manor import PirateManor
from src.utils import CustomEditor, get_palette_for_biome

from ..simulation.pirate import Pirate
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
PIRATE_PATH_BLOCK = 9

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

MAX_ELEVATION = 50


@dataclass
class Village:
    """
    Dataclass representing a village that is built in Minecraft
    """

    editor: CustomEditor

    simulation: Simulation

    height: Callable[[], int] = lambda: randint(3, 7)
    depth: Callable[[], int] = lambda: randint(3, 10)
    width: Callable[[], int] = lambda: randint(2, 5) * 2

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

        nb_pirates = len(self.simulation.pirates)
        pirate_ratio = nb_pirates / total_players / 2
        blocks_to_place = int(self.houseMap.size * pirate_ratio)

        if blocks_to_place <= 0:
            return

        size_x, size_z = self.houseMap.shape
        start_x = randint(5, size_x - 6)
        start_z = randint(5, size_z - 6)

        self.houseMap[start_x, start_z] = PIRATE_BLOCK
        blocks_to_place -= 1

        # Set to track candidate frontier blocks
        frontier = []
        visited = set()

        def add_neighbors(x: int, z: int) -> None:
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

        while blocks_to_place > 0 and frontier:
            # Select a random cell from the current frontier
            idx = randint(0, len(frontier) - 1)
            cx, cz = frontier[idx]
            frontier[idx] = frontier[-1]
            frontier.pop()

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

    def _paint_pirate_path_block(self, cx: int, cz: int) -> None:
        """Apply a 3-block wide brush for organic pirate paths."""
        sx, sz = self.houseMap.shape
        # radius = 1 means 1 block around the center -> 3 blocks total width
        r = 1

        x_path = slice(max(0, cx - r), min(sx, cx + r + 1))
        z_path = slice(max(0, cz - r), min(sz, cz + r + 1))

        # Target only free or existing pirate blocks to avoid overwriting houses
        zone = self.houseMap[x_path, z_path]
        mask = (zone == FREE_BLOCK) | (zone == PIRATE_BLOCK)
        zone[mask] = PIRATE_PATH_BLOCK

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
        min_required_streets: int = 400,  # Minimum street pixels required
    ) -> None:
        """
        Generate streets using a dynamic seeding fallback loop to ensure
        the L-system generates enough paths on amplified terrains.
        """
        sx, sz = self.houseMap.shape
        radius, padding = width // 2, (width // 2) + 1
        directions = {0: (0, -1), 90: (1, 0), 180: (0, 1), 270: (-1, 0)}
        prob = 0.75

        # Try up to 5 times at different flat locations if streets fail
        for attempt in range(5):
            # Reset street blocks if this is a retry attempt
            if attempt > 0:
                mask = np.isin(self.houseMap, [STREET_BLOCK, PADDING_BLOCK])
                self.houseMap[mask] = FREE_BLOCK

            # Find the best seed. On retry, we artificially shift the search chunk
            start_x, start_z = self._find_flattest_seed(chunk_size=32 + (attempt * 12))

            commands = self._expand_lsystem(iterations)
            state = [start_x, start_z, 0]  # cx, cz, angle_deg
            stack = []
            skip_depth = 0

            # Execute the L-system turtle commands
            for cmd in commands:
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
                    if random.random() > prob:
                        skip_depth = 1
                    else:
                        stack.append(tuple(state))
                elif cmd == "]" and stack:
                    state = list(stack.pop())

            # Count how many street blocks were successfully placed
            street_count = np.sum(self.houseMap == STREET_BLOCK)

            # If we generated enough streets, we can safely exit the retry loop
            if street_count >= min_required_streets:
                break
        else:
            print(
                f"[Warning] Failed to reach {min_required_streets} streets "
                f"after 5 attempts. Proceeding with {street_count} blocks."
            )

        self._clean_path_vegetation(STREET_BLOCK)
        self._place_street_positions()

    def _place_street_positions(self) -> None:
        max_dist = 5
        for get_street_slice, get_target_slice, direction in zip(
            [
                lambda d: (slice(None), slice(d, None)),
                lambda d: (slice(d, None), slice(None)),
                lambda d: (slice(None), slice(None, -d)),
                lambda d: (slice(None, -d), slice(None)),
            ],
            [
                lambda d: (slice(None), slice(None, -d)),
                lambda d: (slice(None, -d), slice(None)),
                lambda d: (slice(None), slice(d, None)),
                lambda d: (slice(d, None), slice(None)),
            ],
            STREET_DIRECTIONS,
        ):
            for d in range(1, max_dist + 1):
                s_slice = get_street_slice(d)
                t_slice = get_target_slice(d)
                street_found = self.houseMap[s_slice] == STREET_BLOCK
                target_view = self.houseMap[t_slice]
                mask = (target_view == FREE_BLOCK) & street_found
                target_view[mask] = direction

    @property
    def houses(self) -> Generator[House, None, list[House]]:
        if self._houses is not None:
            return self._houses

        self._houses = []

        # Place the pirate manor first if applicable
        if self.simulation.alive_pirates:
            try:
                manor = self.get_manor()
                self._houses.append(manor)
                (mx, Mx), (mz, Mz) = self.get_house_footprint(manor)
                self.houseMap[mx:Mx, mz:Mz] = HOUSE_BLOCK
                yield manor
            except HouseOverlapError:
                pass

        # Shuffle and place all other players
        random.shuffle(self.simulation.players)
        for player in self.simulation.players:
            try:
                house = self.get_house(player)
                self._houses.append(house)
                (mx, Mx), (mz, Mz) = self.get_house_footprint(house)
                self.houseMap[mx:Mx, mz:Mz] = HOUSE_BLOCK
                yield house
            except HouseOverlapError:
                pass

        return self._houses

    def get_manor(self) -> House:
        """Finds a valid placement for the Pirate Manor using matrix masks."""
        mask = self.houseMap == PIRATE_BLOCK
        coords = np.argwhere(mask)

        # Fallback to free blocks if the pirate zone generation failed
        if coords.size == 0:
            coords = np.argwhere(self.houseMap == FREE_BLOCK)

        candidates = [tuple(c) for c in coords]
        random.shuffle(candidates)
        rotations = [0, 1, 2, 3]

        for x, z in candidates:
            ground_y = int(self.heightmaps[x, z])
            random.shuffle(rotations)

            for rot in rotations:
                manor = Pirate.build_manor(
                    pirates=self.simulation.alive_pirates,
                    editor=self.editor,
                    x=x,
                    z=z,
                    y=ground_y - 1,
                    rotation=rot,
                )

                (min_x, max_x), (min_z, max_z) = self.get_house_footprint(manor)
                height_zone = self.heightmaps[min_x:max_x, min_z:max_z]
                manor.y = int(np.mean(height_zone))

                if self.can_place_manor(manor):
                    return manor

        # Absolute fallback to map center if no spots were valid
        sx, sz = self.houseMap.shape
        cx, cz = sx // 2, sz // 2
        return Pirate.build_manor(
            pirates=self.simulation.alive_pirates,
            editor=self.editor,
            x=cx,
            z=cz,
            y=int(self.heightmaps[cx, cz]) - 1,
            rotation=0,
        )

    def get_house(self, player: Player) -> House:
        """Finds a valid layout targeting specific zones based on player role."""
        is_pirate = isinstance(player, Pirate)

        # Direct targets based on faction
        if is_pirate:
            coords = np.argwhere(self.houseMap == PIRATE_BLOCK)
            if coords.size == 0:
                coords = np.argwhere(self.houseMap == FREE_BLOCK)
        else:
            mask = np.isin(self.houseMap, STREET_DIRECTIONS)
            coords = np.argwhere(mask)

        if coords.size == 0:
            raise HouseOverlapError("No valid blocks found for placement.")

        candidates = [tuple(c) for c in coords]
        random.shuffle(candidates)
        rotations = [0, 1, 2, 3]

        for x, z in candidates:
            ground_y = int(self.heightmaps[x, z])
            random.shuffle(rotations)

            for rot in rotations:
                house = player.house(
                    editor=self.editor,
                    x=x,
                    z=z,
                    y=ground_y,
                    rotation=rot,
                )

                (min_x, max_x), (min_z, max_z) = self.get_house_footprint(house)
                height_zone = self.heightmaps[min_x:max_x, min_z:max_z]
                house.y = int(np.mean(height_zone))

                if self.can_place_house(house, player):
                    return house

        raise HouseOverlapError("Impossible to place house.")

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

    def _clean_path_vegetation(
        self, target_block: int, max_check_height: int = 15
    ) -> None:
        """Scan specified path tiles and trigger wood/leaves vaporization."""
        # Find coordinates matching the requested path type (street or pirate)
        path_coords = np.argwhere(self.houseMap == target_block)

        for x, z in path_coords:
            ground_y = self.heightmaps[x, z]
            # Look upward from the path level to look for remaining limbs
            for y in range(ground_y + 1, ground_y + max_check_height):
                block = self.editor.getBlock((x, y, z))
                assert block.id is not None
                if self.editor.is_tree_block(block.id):
                    self.editor.destroy_tree_flood_fill((x, y, z))

    def rotation(self, x: int, z: int) -> int:
        return STREET_ROTATIONS[self.houseMap[x, z]]

    def build(self) -> None:
        self.build_pirate_zone()
        self.build_street_paths()

        houses_list = list(self.houses)
        self._generate_pirate_paths(houses_list)
        self.build_pirate_paths()

        for house in houses_list:
            house.build()

    def build_pirate_zone(self) -> None:
        for x, z in np.argwhere(self.houseMap == PIRATE_BLOCK):
            self.editor.placeBlock((x, self.heightmaps[x, z], z), Block("coarse_dirt"))

    def build_street_paths(self) -> None:
        for x, z in np.argwhere(self.houseMap == STREET_BLOCK):
            biome_string = self.editor.getBiome((x, int(self.heightmaps[x, z]), z))
            palette = get_palette_for_biome(biome_string)
            self.editor.placeBlock((x, self.heightmaps[x, z], z), palette["street"])

    def build_pirate_paths(self) -> None:
        for x, z in np.argwhere(self.houseMap == PIRATE_PATH_BLOCK):
            block = choice([Block("dirt_path"), Block("podzol")])
            self.editor.placeBlock((x, self.heightmaps[x, z], z), block)

    def get_house_footprint(
        self, house: House
    ) -> tuple[tuple[int, int], tuple[int, int]]:
        baseX, endX, baseZ, endZ = house.get_footprint()
        return (
            (max(baseX, 0), min(endX, self.houseMap.shape[0])),
            (max(baseZ, 0), min(endZ, self.houseMap.shape[1])),
        )

    def can_place_manor(self, manor: House) -> bool:
        """Validates that the manor is within bounds and occupies only valid blocks."""
        (min_x, max_x), (min_z, max_z) = self.get_house_footprint(manor)
        sx, sz = self.houseMap.shape

        # Check strict boundaries against buildArea matrix size
        if min_x < 0 or min_z < 0 or max_x > sx or max_z > sz:
            return False

        # Safety check for invalid footprint dimensions
        if min_x >= max_x or min_z >= max_z:
            return False

        # Refuse placement if the terrain drops or rises by more than 10 blocks
        height_zone = self.heightmaps[min_x:max_x, min_z:max_z]
        if np.max(height_zone) - np.min(height_zone) > MAX_ELEVATION:
            return False

        # Validate that the zone is exclusively PIRATE_BLOCK or FREE_BLOCK
        zone = self.houseMap[min_x:max_x, min_z:max_z]
        return bool(np.all(np.isin(zone, [PIRATE_BLOCK, FREE_BLOCK])))

    def can_place_house(self, house: House, player: Player) -> bool:
        """
        Returns True if the house can be placed:
        1. Area is clear of obstacles.
        2. At least one block is a street-adjacent zone.
        3. The house rotation matches the direction of the street.
        """
        (min_x, max_x), (min_z, max_z) = self.get_house_footprint(house)

        if min_x >= max_x or min_z >= max_z:
            return False

        height_zone = self.heightmaps[min_x:max_x, min_z:max_z]
        if np.max(height_zone) - np.min(height_zone) > MAX_ELEVATION:
            return False

        zone = self.houseMap[min_x:max_x, min_z:max_z]

        if isinstance(player, Pirate):
            return bool(np.all(np.isin(zone, [PIRATE_BLOCK, FREE_BLOCK])))

        mask_street = np.isin(zone, STREET_DIRECTIONS)
        mask_free = zone == FREE_BLOCK

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
        fig, ax = plt.subplots()
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

    def _find_flattest_seed(self, chunk_size: int = 32) -> tuple[int, int]:
        """
        Scans the heightmap by chunks and returns the center coordinates
        of the flattest region to start the L-system safely.
        """
        sx, sz = self.houseMap.shape
        best_x, best_z = sx // 2, sz // 2  # Default fallback to center
        min_delta = float("inf")

        # Scan the map by stepping through chunks
        for x in range(0, sx - chunk_size, chunk_size // 2):
            for z in range(0, sz - chunk_size, chunk_size // 2):
                height_chunk = self.heightmaps[x : x + chunk_size, z : z + chunk_size]

                # Calculate the elevation delta in this specific sector
                delta = int(np.max(height_chunk) - np.min(height_chunk))

                # We want a flat zone, but we also avoid absolute map borders
                if delta < min_delta and x > 16 and z > 16:
                    min_delta = delta
                    best_x = x + chunk_size // 2
                    best_z = z + chunk_size // 2

        return best_x, best_z

    def _find_street_pirate_intersections(self) -> list[tuple[int, int]]:
        """Detect points where 3-wide urban streets touch the pirate zone."""
        sx, sz = self.houseMap.shape
        contact_points = []

        # Find all STREET_BLOCKs adjacent to a PIRATE_BLOCK
        for x in range(1, sx - 1):
            for z in range(1, sz - 1):
                if self.houseMap[x, z] == STREET_BLOCK:
                    # Check 8 surrounding neighbors for contact
                    for dx, dz in [
                        (-1, 0),
                        (1, 0),
                        (0, -1),
                        (0, 1),
                        (-1, -1),
                        (-1, 1),
                        (1, -1),
                        (1, 1),
                    ]:
                        if self.houseMap[x + dx, z + dz] == PIRATE_BLOCK:
                            contact_points.append((x, z))
                            break  # Stop checking neighbors for this block

        # only keep clusters of at least 2 points (3-wide streets)
        intersections = []
        visited = set()

        for px, pz in contact_points:
            if (px, pz) in visited:
                continue

            # Group adjacent contact points within a small radius
            cluster = []
            for cx, cz in contact_points:
                if abs(cx - px) <= 2 and abs(cz - pz) <= 2:
                    cluster.append((cx, cz))

            # A real street is 3 blocks wide, so we expect >= 2 contact points
            if len(cluster) >= 2:
                # Find the center pixel of the street end
                avg_x = sum(c[0] for c in cluster) // len(cluster)
                avg_z = sum(c[1] for c in cluster) // len(cluster)
                intersections.append((avg_x, avg_z))

                # Mark entire cluster as processed to avoid duplicates
                for c in cluster:
                    visited.add(c)

        return intersections

    def _generate_pirate_paths(self, houses_list: list[House]) -> None:
        """Connects pirate houses and urban street ends using an organic network."""
        pirate_houses = [h for h in houses_list if isinstance(h.player, Pirate)]
        sx, sz = self.houseMap.shape

        # Collect all targets to connect (House doors)
        targets = []
        for h in pirate_houses:
            if isinstance(h, (PirateHouse, PirateManor)):
                dx, dz = h.get_door_pos()
                if 0 <= dx < sx and 0 <= dz < sz:
                    targets.append((dx, dz))

        # Add the clean street intersections to the network targets
        targets.extend(self._find_street_pirate_intersections())

        # If we have nothing to connect, exit
        if not targets:
            return

        # Build the Minimum Spanning Tree using A*
        connected = {targets[0]}

        for tgt in targets[1:]:
            path = self._find_path_astar(tgt, connected)
            for px, pz in path:
                connected.add((px, pz))
                # Paint the 3-wide path only if outside urban streets
                if self.houseMap[px, pz] not in (STREET_BLOCK, PADDING_BLOCK):
                    self._paint_pirate_path_block(px, pz)

        self._clean_path_vegetation(PIRATE_PATH_BLOCK)

    def _find_path_astar(
        self, start: tuple[int, int], targets: set[tuple[int, int]]
    ) -> list[tuple[int, int]]:
        """A* pathfinding to connect to the nearest existing path."""
        if start in targets:
            return []

        def dist(t):
            return (t[0] - start[0]) ** 2 + (t[1] - start[1]) ** 2

        nearest_tgt = min(targets, key=dist)

        queue = [(0, 0, start)]
        came_from = {}
        g_score = {start: 0}
        sx, sz = self.houseMap.shape

        while queue:
            _, current_g, current = heapq.heappop(queue)

            if current in targets:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                return path

            if current_g > g_score.get(current, float("inf")):
                continue

            cx, cz = current
            moves = [
                (-1, 0),
                (1, 0),
                (0, -1),
                (0, 1),
                (-1, -1),
                (-1, 1),
                (1, -1),
                (1, 1),
            ]

            for dx, dz in moves:
                nx, nz = cx + dx, cz + dz

                if 0 <= nx < sx and 0 <= nz < sz:
                    b_type = self.houseMap[nx, nz]

                    if b_type in (STREET_BLOCK, PADDING_BLOCK):
                        continue

                    cur_h = self.heightmaps[cx, cz]
                    nxt_h = self.heightmaps[nx, nz]
                    if abs(int(nxt_h) - int(cur_h)) > 2:
                        continue

                    cost = 1.414 if dx != 0 and dz != 0 else 1.0

                    if b_type == FREE_BLOCK:
                        cost += 3.0
                    elif b_type == PIRATE_PATH_BLOCK:
                        cost = 0.1
                    elif b_type == HOUSE_BLOCK:
                        cost += 20.0

                    tentative_g = current_g + cost

                    if tentative_g < g_score.get((nx, nz), float("inf")):
                        came_from[(nx, nz)] = current
                        g_score[(nx, nz)] = tentative_g
                        h = math.sqrt(
                            (nx - nearest_tgt[0]) ** 2 + (nz - nearest_tgt[1]) ** 2
                        )
                        heapq.heappush(queue, (tentative_g + h, tentative_g, (nx, nz)))

        return []


class HouseOverlapError(Exception):
    def __init__(self, message):
        super().__init__(message)
