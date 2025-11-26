"""Intermediate representation and compilation result types for ReachyMiniScript."""

from typing import List, Literal, Optional
from dataclasses import field, dataclass

import numpy as np
import numpy.typing as npt


@dataclass
class CompilationError:
    """Represents a compilation error or warning."""

    line: int
    column: int = 0
    message: str = ""
    severity: Literal["error", "warning"] = "error"

    def __str__(self) -> str:
        """Format error message for display."""
        icon = "❌" if self.severity == "error" else "⚠️ "
        return f"{icon} Line {self.line}: {self.message}"


@dataclass
class IRAction:
    """Resolved action - all defaults applied, ready to execute."""

    head_pose: Optional[npt.NDArray[np.float64]] = None  # 4x4 matrix
    antennas: Optional[List[float]] = None  # [right, left] in radians
    body_yaw: Optional[float] = None  # radians
    duration: float = 1.0
    interpolation: str = "minjerk"

    # Metadata for debugging
    source_line: int = 0
    original_text: str = ""


@dataclass
class IRWaitAction:
    """Wait/pause action."""

    duration: float
    source_line: int = 0
    original_text: str = ""


@dataclass
class IRPictureAction:
    """Take a picture action."""

    source_line: int = 0
    original_text: str = ""


@dataclass
class IRPlaySoundAction:
    """Play a sound action."""

    sound_name: str  # Name of the sound file (without extension)
    blocking: bool = False  # True = wait for sound to finish, False = play in background
    loop: bool = False  # True = loop the sound
    duration: Optional[float] = None  # Duration for looping or limited playback
    source_line: int = 0
    original_text: str = ""


@dataclass
class CompilationResult:
    """Result of ReachyMiniScript compilation."""

    # Tool metadata
    name: str
    description: str

    # Compilation results
    success: bool = False
    errors: List[CompilationError] = field(default_factory=list)
    warnings: List[CompilationError] = field(default_factory=list)

    # Source code
    source_code: str = ""
    source_file_path: Optional[str] = None

    # Intermediate representation (IR output)
    ir: List[IRAction | IRWaitAction | IRPictureAction | IRPlaySoundAction] = field(
        default_factory=list
    )
