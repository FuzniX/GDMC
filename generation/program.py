from random import randint

from gdpc import Editor, Block, geometry
from matplotlib import pyplot as plt

from house import House
from utils import ingame_exception
from village import Village


def house():
    House(
        editor=editor,

        x=buildArea.offset.x + 1,
        y=editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"][3, 1] - 1,
        z=buildArea.offset.z + 1,

        height=randint(3, 7),
        depth=randint(3, 10),
        width=randint(2, 5) * 2,
        rotation=randint(0, 3),

        floorPalette=[
            Block("stone_bricks"),
            Block("cracked_stone_bricks"),
            Block("cobblestone"),
        ],
        wallPalette=[
            Block("oak_planks"),
            Block("spruce_planks"),
            Block("white_terracotta"),
            Block("green_terracotta"),
        ],
        roofPalette=[
            [Block("oak_stairs"), Block("oak_planks")],
            [Block("spruce_stairs"), Block("spruce_planks")],
            [Block("birch_stairs"), Block("birch_planks")],
            [Block("dark_oak_stairs"), Block("dark_oak_planks")],
            [Block("cobblestone_stairs"), Block("cobblestone")],
        ],
    ).build()


def village():
    village = Village(
        editor=editor,
        heightmap=editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"],
        floorPalette=[
            Block("stone_bricks"),
            Block("cracked_stone_bricks"),
            Block("cobblestone"),
        ],
        wallPalette=[
            Block("oak_planks"),
            Block("spruce_planks"),
            Block("white_terracotta"),
            Block("green_terracotta"),
        ],
        roofPalette=[
            [Block("oak_stairs"), Block("oak_planks")],
            [Block("spruce_stairs"), Block("spruce_planks")],
            [Block("birch_stairs"), Block("birch_planks")],
            [Block("dark_oak_stairs"), Block("dark_oak_planks")],
            [Block("cobblestone_stairs"), Block("cobblestone")],
        ],
        houseNumber=25
    )

    village.build()

    village.plot()
    plt.show()

    village.plot_houseMap()
    plt.show()


def main():
    village()


if __name__ == '__main__':
    editor = Editor(buffering=True)
    buildArea = editor.getBuildArea()

    # Load world slice of the build area
    editor.loadWorldSlice(cache=True)

    buildRect = buildArea.toRect()
    heightmap = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    # Loop through the perimeter of the build area
    for point in buildRect.outline:
        localPoint = point - buildRect.offset

        height = heightmap[tuple(localPoint)] - 1
        editor.placeBlock((point[0], height, point[1]), Block("red_concrete"))

    try:
        main()
    except Exception as e:
        ingame_exception(editor, e)
