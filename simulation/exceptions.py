from typing import Optional

from .enums import ActionChoice


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
                    message = f"Cannot set a target for {action_choice.value} action."

            # Target was passed but it's not one of the intended types
            elif action_choice is not None:
                target_string = (
                    " or ".join(t.__name__ for t in intended_target)
                    if isinstance(intended_target, tuple)
                    else str(intended_target)
                )
                message = (
                    f"Target must be {target_string} for {action_choice.value} action."
                )

        super().__init__(message)
