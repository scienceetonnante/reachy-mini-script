"""rmscript: A kid-friendly robot programming language for Reachy Mini."""

from rmscript.adapters import ExecutionAdapter, ExecutionContext
from rmscript.compiler import RMScriptCompiler, compile_file, compile_script, verify_script
from rmscript.ir import (
    CompilationError,
    CompilationResult,
    IRAction,
    IRPictureAction,
    IRPlaySoundAction,
    IRWaitAction,
)
from rmscript.types import IRActionType, IRList

__version__ = "0.1.0"

__all__ = [
    # Compiler
    "RMScriptCompiler",
    "compile_script",
    "compile_file",
    "verify_script",
    # IR types
    "CompilationResult",
    "CompilationError",
    "IRAction",
    "IRWaitAction",
    "IRPictureAction",
    "IRPlaySoundAction",
    # Type aliases
    "IRActionType",
    "IRList",
    # Adapter protocol
    "ExecutionAdapter",
    "ExecutionContext",
]
