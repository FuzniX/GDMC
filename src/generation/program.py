import time

from gdpc.block import Block

from ..simulation.simulation import Simulation
from ..utils import AllowedTimeExceededError, CustomEditor
from .village import Village

ALLOWED_TIME = 40  # seconds


def main():
    village = Village(
        editor=editor,
        simulation=Simulation.generate(
            nb_villagers=10,
            nb_merchants=10,
            nb_pirates=10,
        ),
    )

    village.build()
    editor.flushBuffer()

    from matplotlib import pyplot as plt

    village.plot_houseMap()
    # village.plot()
    plt.show()


if __name__ == "__main__":
    editor = CustomEditor(buffering=True)
    buildArea = editor.getBuildArea()
    editor.transform = buildArea.begin.x, 0, buildArea.begin.z

    # Load world slice of the build area
    editor.loadWorldSlice(cache=True)
    assert editor.worldSlice is not None

    buildRect = buildArea.toRect()
    heightmaps = editor.worldSlice.heightmaps["MOTION_BLOCKING_NO_LEAVES"]

    # Loop through the perimeter of the build area
    for point in buildRect.outline:
        localPoint = point - buildRect.offset
        height = heightmaps[tuple(localPoint)] - 1
        editor.placeBlock((localPoint[0], height, localPoint[1]), Block("red_concrete"))

    try:
        start_time = time.perf_counter()

        main()

        # Check elapsed time after main() finishes
        elapsed_time = time.perf_counter() - start_time
        if elapsed_time > ALLOWED_TIME:
            raise AllowedTimeExceededError(
                f"Allowed time exceeded! ({elapsed_time:.2f}s)"
            )
        else:
            editor.ingame_print(f"Done in {elapsed_time:.2f}s!")
    except Exception as e:
        editor.ingame_exception(e)
