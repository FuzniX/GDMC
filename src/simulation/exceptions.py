from typing import TYPE_CHECKING, Optional

from log.config import get_sim_logger

from .enums import ActionChoice

if TYPE_CHECKING:
    from .player import Player

logger = get_sim_logger()


class WrongTargetError(Exception):
    def __init__(
        self,
        action_choice: Optional[ActionChoice] = None,
        intended_target: Optional[type] | tuple[type, ...] = None,
        message: Optional[str] = None,
    ) -> None:

        # If no message was provided, generate one based on the target and action choice
        if message is None:
            # No target were to be passed
            if intended_target is None:
                if action_choice is None:
                    message = "Cannot set a target when no action is chosen."
                else:
                    message = f"Cannot set a target for {action_choice.name} action."

            # Target was passed but it's not one of the intended types
            elif action_choice is not None:
                target_string = (
                    " or ".join(t.__name__ for t in intended_target)
                    if isinstance(intended_target, tuple)
                    else str(intended_target)
                )
                message = (
                    f"Target must be {target_string} for {action_choice.name} action."
                )

        super().__init__(message)


class ImpossibleActionError(Exception):
    def __init__(
        self,
        player: Player,
        reason: Optional[str] = None,
    ) -> None:
        assert player.action_choice is not None
        full_message = f"{player} cannot perform {player.action_choice.name} action."
        full_message += f" Reason: {reason}" if reason else ""

        logger.action_failure(full_message)
        super().__init__(full_message)
