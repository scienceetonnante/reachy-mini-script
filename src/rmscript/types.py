"""Shared type definitions for rmscript."""

from typing import List, Union

from rmscript.ir import IRAction, IRPictureAction, IRPlaySoundAction, IRWaitAction

# Union type for all IR action types
IRActionType = Union[IRAction, IRWaitAction, IRPictureAction, IRPlaySoundAction]

# Type alias for IR list
IRList = List[IRActionType]
