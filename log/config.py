import logging
import os
from typing import TYPE_CHECKING

from typing_extensions import Optional

if TYPE_CHECKING:
    from src.simulation.player import Player
    from src.simulation.simulation import Simulation


class SimulationContextFilter(logging.Filter):
    """Filter that injects current simulation day in each log."""

    def __init__(self, simulation: Simulation):
        super().__init__()
        self.simulation = simulation

    def filter(self, record: logging.LogRecord):
        record.day = getattr(self.simulation, "day", 0)
        return True


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


def get_sim_logger(name: Optional[str] = None):
    """Function to retrieve adapted logger."""
    return SimulationLoggerAdapter(logging.getLogger(name), {})


def setup_logging(simulation: Simulation):
    # File path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(current_dir, "simulation.log")

    logging.getLogger().handlers = []

    log_format = "[Day %(day)s] - [%(theme)s] %(message)s"

    logging.basicConfig(
        filename=log_path,
        filemode="w",
        level=logging.INFO,
        format=log_format,
        force=True,
    )

    # Add filter to root logger
    root_logger = logging.getLogger()
    root_logger.addFilter(SimulationContextFilter(simulation))
