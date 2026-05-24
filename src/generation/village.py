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
from ..simulation.pirate import Pirate
from .houses.house import House
from .houses.pirate_house import PirateHouse

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
    Dataclass représentant un village construit dans Minecraft.
    Gère le placement strict et exclusif des habitations de pirates dans leur zone.
    """

    editor: Editor
    simulation: Simulation

    height: Callable[[], int] = lambda: randint(3, 7)
    depth: Callable[[], int] = lambda: randint(3, 10)
    width: Callable[[], int] = lambda: randint(2, 5) * 2

    _houses: Optional[list[House]] = field(init=False, default=None)

    def __post_init__(self) -> None:
        self.buildArea = self.editor.getBuildArea()
        self.houseMap = np.zeros((self.buildArea.size.x, self.buildArea.size.z))

        self.generate_pirate_zone()
        self.generate_streets()

    def generate_pirate_zone(self) -> None:
        total_players = len(self.simulation.players)
        if total_players == 0:
            return

        nb_pirates = len(self.simulation.pirates)
        pirate_ratio = nb_pirates / total_players
        blocks_to_place = int(self.houseMap.size * pirate_ratio)

        if blocks_to_place <= 0:
            return

        size_x, size_z = self.houseMap.shape
        start_x = randint(5, size_x - 6)
        start_z = randint(5, size_z - 6)

        self.houseMap[start_x, start_z] = PIRATE_BLOCK
        blocks_to_place -= 1

        frontier = set()

        def add_neighbors(x: int, z: int) -> None:
            neighbors = [(x - 1, z), (x + 1, z), (x, z - 1), (x, z + 1)]
            for nx, nz in neighbors:
                if 2 <= nx < size_x - 2 and 2 <= nz < size_z - 2:
                    if self.houseMap[nx, nz] == FREE_BLOCK:
                        frontier.add((nx, nz))

        add_neighbors(start_x, start_z)

        while blocks_to_place > 0 and frontier:
            next_cell = random.choice(list(frontier))
            frontier.remove(next_cell)
            cx, cz = next_cell

            if self.houseMap[cx, cz] == FREE_BLOCK:
                self.houseMap[cx, cz] = PIRATE_BLOCK
                blocks_to_place -= 1
                add_neighbors(cx, cz)

    def generate_horizontal_streets(self, nb: int = 5, width: int = 3) -> None:
        size_x, size_z = self.houseMap.shape
        occupied_z = np.zeros(size_z, dtype=int)
        placed = 0
        radius = width // 2
        padding = radius + 1

        for _ in range(100_000):
            z_center = randint(padding + 2, size_z - (padding + 3))
            if np.any(occupied_z[z_center - padding : z_center + padding + 1] == 1):
                continue

            start_x = randint(2, size_x // 2)
            end_x = randint(size_x // 2, size_x - 3)
            occupied_z[z_center - padding : z_center + padding + 1] = 1

            x_slice = slice(max(0, start_x - 1), min(size_x, end_x + 2))
            z_slice = slice(max(0, z_center - padding), min(size_z, z_center + padding + 1))

            padding_mask = self.houseMap[x_slice, z_slice] == FREE_BLOCK
            self.houseMap[x_slice, z_slice][padding_mask] = PADDING_BLOCK

            core_x_slice = slice(start_x, end_x + 1)
            core_z_slice = slice(z_center - radius, z_center + radius + 1)
            street_mask = self.houseMap[core_x_slice, core_z_slice] != PIRATE_BLOCK
            self.houseMap[core_x_slice, core_z_slice][street_mask] = STREET_BLOCK

            placed += 1
            if placed == nb: return

    def generate_vertical_streets(self, nb: int = 5, width: int = 3) -> None:
        size_x, size_z = self.houseMap.shape
        occupied_x = np.zeros(size_x, dtype=int)
        placed = 0
        radius = width // 2
        padding = radius + 1

        for _ in range(100_000):
            x_center = randint(padding + 2, size_x - (padding + 3))
            if np.any(occupied_x[x_center - padding : x_center + padding + 1] == 1):
                continue

            start_z = randint(2, size_z // 2)
            end_z = randint(size_z // 2, size_z - 3)
            occupied_x[x_center - padding : x_center + padding + 1] = 1

            x_slice = slice(max(0, x_center - padding), min(size_x, x_center + padding + 1))
            z_slice = slice(max(0, start_z - 1), min(size_z, end_z + 2))

            padding_mask = self.houseMap[x_slice, z_slice] == FREE_BLOCK
            self.houseMap[x_slice, z_slice][padding_mask] = PADDING_BLOCK

            core_x_slice = slice(x_center - radius, x_center + radius + 1)
            core_z_slice = slice(start_z, end_z + 1)
            street_mask = self.houseMap[core_x_slice, core_z_slice] != PIRATE_BLOCK
            self.houseMap[core_x_slice, core_z_slice][street_mask] = STREET_BLOCK

            placed += 1
            if placed == nb: return

    def place_street_positions(self) -> None:
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

    def generate_streets(self, nb_horizontal: int = 5, nb_vertical: int = 5, width: int = 3) -> None:
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
        
        if self.simulation.alive_pirates:
            manor = self.get_manor()
            self._houses.append(manor)
            (min_x, max_x), (min_z, max_z) = self.get_house_footprint(manor)
            self.houseMap[min_x:max_x, min_z:max_z] = HOUSE_BLOCK
            yield manor
        for player in self.simulation.players:
            house = self.get_house(player)
            self._houses.append(house)
            (min_x, max_x), (min_z, max_z) = self.get_house_footprint(house)
            self.houseMap[min_x:max_x, min_z:max_z] = HOUSE_BLOCK
            yield house

        return self._houses

    def get_manor(self) -> House:
        pirate_pixels = np.argwhere(self.houseMap == PIRATE_BLOCK)
        if len(pirate_pixels) == 0:
            pirate_pixels = np.argwhere(self.houseMap == FREE_BLOCK)

        for _ in range(200_000):
            chosen_pixel = random.choice(pirate_pixels)
            x, z = int(chosen_pixel[0]), int(chosen_pixel[1])
            manor = Pirate.build_manor(
                pirates=self.simulation.alive_pirates,
                editor=self.editor,
                x=x,
                z=z,
                y=int(self.heightmaps[x, z]) - 1,
                rotation=randint(0, 3)
            )
            if self.can_place_manor(manor):
                return manor
        else:
            size_x, size_z = self.houseMap.shape
            x, z = size_x // 2, size_z // 2
            return Pirate.build_manor(
                pirates=self.simulation.alive_pirates,
                editor=self.editor,
                x=x, z=z, y=int(self.heightmaps[x, z]) - 1, rotation=0
            )

    def get_house(self, player: Player) -> House:
        if isinstance(player, Pirate):
            pirate_pixels = np.argwhere(self.houseMap == PIRATE_BLOCK)
            if len(pirate_pixels) == 0:
                pirate_pixels = np.argwhere(self.houseMap == FREE_BLOCK)
        else:
            pirate_pixels = None

        for _ in range(100_000):
            if isinstance(player, Pirate):
                chosen_pixel = random.choice(pirate_pixels)
                x, z = int(chosen_pixel[0]), int(chosen_pixel[1])
            else:
                x = randint(8, self.buildArea.size.x - 9)
                z = randint(8, self.buildArea.size.z - 9)

            house = player.house(
                editor=self.editor,
                x=x,
                z=z,
                y=int(self.heightmaps[x, z]) - 1,
                rotation=randint(0, 3)
            )

            if self.can_place_house(house, player):
                break
        else:
            raise HouseOverlapError("Impossible to place house")

        return house

    def rotation(self, x: int, z: int) -> int:
        return STREET_ROTATIONS[self.houseMap[x, z]]

    def build(self) -> None:
        self.build_zones()
        for house in self.houses:
            house.build()

    def build_zones(self) -> None:
        for x, z in np.argwhere(self.houseMap == PIRATE_BLOCK):
            self.editor.placeBlock((x, self.heightmaps[x, z] - 1, z), Block("coarse_dirt"))

        for x, z in np.argwhere(self.houseMap == STREET_BLOCK):
            self.editor.placeBlock((x, self.heightmaps[x, z] - 1, z), Block("dirt_path"))

    def get_house_footprint(self, house: House) -> tuple[tuple[int, int], tuple[int, int]]:
        baseX, endX, baseZ, endZ = house.get_footprint()
        return (
            (max(baseX, 0), min(endX, self.houseMap.shape[0])),
            (max(baseZ, 0), min(endZ, self.houseMap.shape[1])),
        )

    def can_place_manor(self, manor: House) -> bool:
        """Vérifie si le manoir peut se poser sans écraser d'autres maisons déjà construites."""
        (min_x, max_x), (min_z, max_z) = self.get_house_footprint(manor)
        
        if min_x <= 1 or max_x >= self.houseMap.shape[0] - 1 or min_z <= 1 or max_z >= self.houseMap.shape[1] - 1:
            return False
        
        house_zone = self.houseMap[min_x:max_x, min_z:max_z]
        if np.any(house_zone == HOUSE_BLOCK) or np.any(house_zone == STREET_BLOCK):
            return False
        return True

    def can_place_house(self, house: House, player: Player) -> bool:
        (min_x, max_x), (min_z, max_z) = self.get_house_footprint(house)
        
        if min_x <= 1 or max_x >= self.houseMap.shape[0] - 1 or min_z <= 1 or max_z >= self.houseMap.shape[1] - 1:
            return False
        if min_x >= max_x or min_z >= max_z:
            return False

        house_zone = self.houseMap[min_x:max_x, min_z:max_z]
        if np.any(house_zone == HOUSE_BLOCK):
            return False

        if isinstance(player, Pirate):
            ratio_pirate = np.sum(house_zone == PIRATE_BLOCK) / house_zone.size
            return ratio_pirate >= 0.60
        
        else:
            if np.any(house_zone == PIRATE_BLOCK):
                return False
            
            allowed_normal_blocks = [FREE_BLOCK, *STREET_DIRECTIONS]
            if not np.all(np.isin(house_zone, allowed_normal_blocks)):
                return False

            mask_street = np.isin(house_zone, STREET_DIRECTIONS)
            street_indices = np.argwhere(mask_street)
            if len(street_indices) == 0:
                return False

            for local_x, local_z in street_indices:
                abs_x = min_x + local_x
                abs_z = min_z + local_z
                if self.rotation(abs_x, abs_z) == house.rotation:
                    return True

            return False

    def plot(self) -> None:
        fig, ax = plt.subplots()
        self.editor.loadWorldSlice(cache=True)
        im = ax.imshow(
            self.heightmaps.T, cmap="inferno", origin="lower",
            extent=(self.buildArea.begin.x, self.buildArea.end.x, self.buildArea.begin.z, self.buildArea.end.z),
        )
        plt.colorbar(im, label="Y")
        assert self._houses is not None
        for house in self._houses: house.plot(ax)
        ax.invert_xaxis()
        plt.title("Build Area")
        plt.xlabel("X")
        plt.ylabel("Z")

    def plot_houseMap(self):
        fig, ax = plt.subplots()
        im = plt.imshow(
            self.houseMap.T, cmap="inferno", origin="lower",
            extent=(self.buildArea.begin.x, self.buildArea.end.x, self.buildArea.begin.z, self.buildArea.end.z),
        )
        assert self._houses is not None
        for house in self._houses: house.plot(ax)
        plt.colorbar(im, label="Built")
        ax.invert_xaxis()
        plt.title("Build Area")
        plt.xlabel("X")
        plt.ylabel("Z")


class HouseOverlapError(Exception):
    def __init__(self, message):
        super().__init__(message)