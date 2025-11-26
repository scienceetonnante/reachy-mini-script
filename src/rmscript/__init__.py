"""rmscript: A kid-friendly robot programming language for Reachy Mini."""

from rmscript.compiler import RMScriptCompiler, compile_script, compile_file, verify_script
from rmscript.ir import (
    CompilationResult,
    CompilationError,
    IRAction,
    IRWaitAction,
    IRPictureAction,
    IRPlaySoundAction,
)
from rmscript.adapters import ExecutionAdapter, ExecutionContext

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
    # Adapter protocol
    "ExecutionAdapter",
    "ExecutionContext",
]
