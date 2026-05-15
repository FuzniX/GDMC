from gdpc.block import Block
from gdpc.editor import Editor
from matplotlib import pyplot as plt

from ..simulation.simulation import Simulation
from ..utils import ingame_exception, ingame_print
from .village import Village


def simulation_village():
    village = Village(
        editor=editor,
        simulation=Simulation.generate(
            nb_villagers=50,
            nb_merchants=0,
            nb_pirates=10,
        ),
    )

    village.build()
    editor.flushBuffer()


def main():
    simulation_village()


if __name__ == "__main__":
    editor = Editor(buffering=True)
    buildArea = editor.getBuildArea()

    # Load world slice of the build area
    editor.loadWorldSlice(cache=True)
    assert editor.worldSlice is not None

    buildRect = buildArea.toRect()
    heightmaps = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    # Loop through the perimeter of the build area
    for point in buildRect.outline:
        localPoint = point - buildRect.offset

        height = heightmaps[tuple(localPoint)] - 1
        editor.placeBlock((point[0], height, point[1]), Block("red_concrete"))

    try:
        main()
        ingame_print(editor, "Done!")
    except Exception as e:
        ingame_exception(editor, e)
