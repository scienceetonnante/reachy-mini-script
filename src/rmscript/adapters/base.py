"""Base adapter protocol for executing rmscript IR."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Protocol

from rmscript.ir import IRAction, IRPictureAction, IRPlaySoundAction, IRWaitAction


@dataclass
class ExecutionContext:
    """Base context for all adapters."""

    script_name: str
    script_description: str
    source_file_path: Optional[str] = None


class ExecutionAdapter(Protocol):
    """Protocol for execution adapters.

    Adapters consume IR and execute it in adapter-specific ways.
    Examples:
    - QueueExecutionAdapter: Converts IR to movement queue for robot execution
    - WebSocketExecutionAdapter: Streams pose parameters over WebSocket
    - SimulationAdapter: Runs IR in a simulation environment
    """

    def execute(
        self,
        ir: List[IRAction | IRWaitAction | IRPictureAction | IRPlaySoundAction],
        context: ExecutionContext,
    ) -> Dict[str, Any]:
        """Execute IR in adapter-specific way.

        Args:
            ir: List of IR actions to execute
            context: Execution context with metadata

        Returns:
            Dictionary with execution results (adapter-specific format)
        """
        ...
