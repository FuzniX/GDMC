import logging
import os
from typing import TYPE_CHECKING

from typing_extensions import Optional

if TYPE_CHECKING:
    from src.simulation.player import Player
    from src.simulation.simulation import Simulation


class SimulationDayFilter(logging.Filter):
    """Filter that injects current simulation day in each log."""

    def __init__(self, simulation: Simulation):
        super().__init__()
        self.simulation = simulation

    def filter(self, record: logging.LogRecord):
        record.day = getattr(self.simulation, "day", 0)
        return True


class StatsFilter(logging.Filter):
    """Filter that only accepts 'STATS' logs."""

    def filter(self, record):
        return getattr(record, "theme", None) == "STATS"


class GameFilter(logging.Filter):
    """Filter that excludes 'STATS' logs."""

    def filter(self, record):
        return getattr(record, "theme", None) != "STATS"


class SimulationLoggerAdapter(logging.LoggerAdapter):
    """
    Adapter that allows theme to be passed as a direct argument.
    Also supplies helpful methods for more natural logging.
    """

    def process(self, msg, kwargs):
        """
        Injects theme into 'extra' for each log.
        """
        theme = kwargs.pop("theme", "INFO")

        extra = kwargs.get("extra", {})
        extra["theme"] = theme
        kwargs["extra"] = extra

        return msg, kwargs

    def infection(self, player: Player, *args, **kwargs):
        self.info(
            f"{player} is now {player.infection_status.name}.",
            *args,
            theme="INFECTION",
            **kwargs,
        )

    def action(self, msg, *args, **kwargs):
        self.info(msg, *args, theme="ACTION", **kwargs)

    def action_failure(self, msg, *args, **kwargs):
        self.info(msg, *args, theme="ACTION_FAILURE", **kwargs)

    def stats(self, msg, *args, **kwargs):
        self.info(msg, *args, theme="STATS", **kwargs)


def get_sim_logger(name: Optional[str] = None):
    """Function to retrieve adapted logger."""
    return SimulationLoggerAdapter(logging.getLogger(name), {})


def setup_logging(simulation: Simulation):
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers = []  # Cleaning

    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Simulation events config
    game_handler = logging.FileHandler(
        os.path.join(current_dir, "simulation.log"), mode="w"
    )
    game_handler.setFormatter(
        logging.Formatter("[Day %(day)s] - [%(theme)s] %(message)s")
    )
    game_handler.addFilter(GameFilter())  # Only game events
    root_logger.addHandler(game_handler)

    # Statistics config
    stats_handler = logging.FileHandler(
        os.path.join(current_dir, "statistics.log"), mode="w"
    )
    stats_handler.setFormatter(logging.Formatter("%(message)s"))
    stats_handler.addFilter(StatsFilter())  # Only statistics
    root_logger.addHandler(stats_handler)

    # add simulation day filter
    root_logger.addFilter(SimulationDayFilter(simulation))
