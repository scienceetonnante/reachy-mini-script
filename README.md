# rmscript

A kid-friendly robot programming language for Reachy Mini.

## Overview

rmscript is a simple, Python-like domain-specific language (DSL) designed to make robot programming accessible to children and beginners. 
It compiles to an intermediate representation (IR) that can be executed by different adapters (queue-based execution, WebSocket streaming, etc.).
Adapters have to be implemented separately to run the compiled behaviors on physical robots or simulations.

## Installation

```bash
uv sync
```


## Quick Start

```python
from rmscript import compile_script

# Compile rmscript source
result = compile_script('''
"Wave hello"
look left
antenna both up
wait 1s
look right
''')

if result.success:
    print(f"Compiled {len(result.ir)} actions")
    for action in result.ir:
        print(f"  - {type(action).__name__}")
else:
    for error in result.errors:
        print(f"Error: {error}")
```

## Language Features

- **Intuitive syntax**: `look left`, `turn right`, `antenna up`
- **Time control**: `wait 2s`, `slow`, `fast`
- **Qualitative strengths**: `little`, `medium`, `lot`, `maximum`
- **Compound movements**: `look left and up`
- **Loops**: `repeat 3` blocks
- **Sound & pictures**: `play sound`, `picture`

See the [Language Reference](docs/language_reference.md) for complete syntax.

## Compiler Architecture

### High-Level Design

rmscript follows a clean separation between **compilation** and **execution**:

```
┌─────────────────────────────────────────────────────────────┐
│                    rmscript Source Code                      │
│                 ("look left", "antenna up")                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      COMPILER PIPELINE                       │
│  ┌──────┐   ┌──────┐   ┌──────────┐   ┌──────────┐        │
│  │Lexer │ → │Parser│ → │ Semantic │ → │Optimizer │         │
│  │      │   │      │   │ Analyzer │   │          │         │
│  └──────┘   └──────┘   └──────────┘   └──────────┘         │
│   Tokens      AST      Validation/      Optimized           │
│                        Defaults          Actions             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           Intermediate Representation (IR)                   │
│  • IRAction (movements: head_pose, antennas, body_yaw)      │
│  • IRWaitAction (pauses)                                     │
│  • IRPictureAction (camera capture)                          │
│  • IRPlaySoundAction (audio playback)                        │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    EXECUTION ADAPTERS                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │Queue-Based   │  │WebSocket     │  │Simulation    │     │
│  │Executor      │  │Streamer      │  │Engine        │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                  │                  │              │
└─────────┼──────────────────┼──────────────────┼──────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
    Robot Hardware      Network Client    Virtual Robot
```

**Key Design Principles:**
- **IR is the boundary**: Compiler produces IR, adapters consume it
- **Decoupled execution**: Same IR can drive hardware, simulation, or network streaming
- **No code generation**: rmscript outputs data structures, not Python code
- **Adapter flexibility**: Create custom adapters for different execution contexts

### Compilation Pipeline

The compiler transforms source code through 4 stages:

**Stage 1: Lexer** - Tokenizes source text with Python-like indentation tracking (INDENT/DEDENT tokens), case-insensitive keyword matching, and position tracking for error messages.

**Stage 2: Parser** - Builds an Abstract Syntax Tree (AST) from tokens, validates syntax, handles keyword reuse with `and` chains, and manages repeat block nesting.

**Stage 3: Semantic Analyzer** - Applies default values (30° angles, 1s duration), converts qualitative keywords to quantitative values, validates physical limits, and generates IR actions. Merges multiple single actions into optimized compound movements.

**Stage 4: Optimizer** - Optimizes IR by merging consecutive waits and removing no-op actions.

### IR Action Types

The compiler outputs four IR action types:

- **IRAction**: Movement commands containing optional `head_pose` (4x4 transformation matrix), `antennas` ([left, right] angles), `body_yaw`, `duration`, and `interpolation` method
- **IRWaitAction**: Pause for specified duration
- **IRPictureAction**: Camera capture command
- **IRPlaySoundAction**: Audio playback with optional looping and blocking

### Adapter Pattern

Adapters consume IR and execute it in context-specific ways. The `ExecutionAdapter` protocol defines:

```python
def execute(self, ir: List[IRAction | ...], context: ExecutionContext) -> Dict[str, Any]
```

**Example adapter types:**
- Queue-based: Converts IR to robot movement queue
- WebSocket: Streams pose parameters over network
- Simulation: Drives virtual robot model

See [examples/adapter_example.py](examples/adapter_example.py) for implementation details.

## Language Reference

**For users writing rmscript programs**, see the complete language reference:
📘 **[rmscript Language Reference](rmscript_reference_doc.md)**

Covers syntax, commands, examples, and best practices for writing robot behaviors.

## For Developers

## Error Handling

### Compilation Errors vs Warnings

rmscript distinguishes between **errors** (prevent compilation) and **warnings** (allow compilation but signal potential issues):

**Errors:**
- Syntax errors (unknown keywords, invalid directions)
- Structural errors (missing indentation, mismatched blocks)
- Semantic errors (combining incompatible commands with `and`)

**Warnings:**
- Values exceeding safe ranges (clamped to limits)
- Physical limit violations (handled by robot hardware)

### Handling Errors Programmatically

```python
from rmscript import compile_script

result = compile_script(source)

if not result.success:
    print("❌ Compilation failed!")
    for error in result.errors:
        print(f"  Line {error.line}: {error.message}")
    exit(1)

if result.warnings:
    print("⚠️  Compilation succeeded with warnings:")
    for warning in result.warnings:
        print(f"  Line {warning.line}: {warning.message}")

# Safe to use result.ir
print(f"✓ Compiled successfully: {len(result.ir)} actions")
```

### Quick Syntax Validation

Use `verify_script()` for fast syntax checking without generating IR:

```python
from rmscript import verify_script

is_valid, messages = verify_script(source_code)

if not is_valid:
    print("Syntax errors:")
    for msg in messages:
        print(f"  {msg}")
else:
    print("✓ Syntax is valid")
```

### Common Error Patterns

**Combining incompatible commands:**
```python
# ❌ Error
"look left and picture"  # Cannot combine movement with control command

# ✅ Correct
"look left\nwait 0.5s\npicture"
```

**Invalid directions:**
```python
# ❌ Error
"turn up"  # 'up' not valid for 'turn' (only left/right/center)

# ✅ Correct
"look up"  # 'up' valid for 'look'
```

**Missing indentation:**
```python
# ❌ Error
"repeat 3\nlook left"  # Missing indentation

# ✅ Correct
"repeat 3\n    look left"
```

## API Reference

### RMScriptCompiler

Main compiler class.

```python
from rmscript import RMScriptCompiler

compiler = RMScriptCompiler(log_level="INFO")
tool = compiler.compile(source_code)
```

**Parameters:**
- `log_level` (str): Logging level - "DEBUG", "INFO", "WARNING", "ERROR"

**Returns:**
- `CompiledTool`: Compilation result object

### verify_rmscript

Verification function that checks if rmscript code compiles without generating executable code.

```python
from rmscript import verify_script

is_valid, errors = verify_script(source_code)
if not is_valid:
    for error in errors:
        print(error)
```

**Parameters:**
- `source_code` (str): rmscript source code to verify

**Returns:**
- `tuple[bool, list[str]]`: Tuple of (is_valid, error_messages)
    - `is_valid`: True if compilation succeeds, False otherwise
    - `error_messages`: List of error and warning messages (empty if valid)

**Example:**

```python
script = '''
"Test script"
look left and picture
'''

is_valid, errors = verify_script(script)
# is_valid = False
# errors = ["❌ Line 3: Cannot combine movement with 'picture' using 'and'. Use separate lines instead."]
```

### CompiledTool

Result of compilation.

```python
class CompiledTool:
    name: str                        # Tool name
    description: str                      # Tool description
    executable: Callable             # Function to execute on robot
    success: bool                    # Compilation succeeded?
    errors: List[CompilationError]   # Compilation errors
    warnings: List[CompilationError] # Compilation warnings
    source_code: str                 # Original source
    ir: List[Action | WaitAction]    # Intermediate representation

    def execute(self, mini: ReachyMini) -> None:
        """Execute the compiled behavior on the robot."""

    def to_python_code(self) -> str:
        """Generate readable Python code."""
```

**Usage:**

```python
if tool.success:
    # Execute on robot
    with ReachyMini() as mini:
        tool.execute(mini)

    # Or get Python code
    print(tool.to_python_code())
else:
    # Handle errors
    for error in tool.errors:
        print(f"{error.severity} Line {error.line}: {error.message}")
```

### CompilationError

Error or warning from compilation.

```python
@dataclass
class CompilationError:
    line: int          # Line number (1-indexed)
    column: int        # Column number (1-indexed)
    message: str       # Error/warning message
    severity: str      # "ERROR" or "WARNING"
```

### Action (IR)

Intermediate representation of a movement.

```python
@dataclass
class Action:
    head_pose: Optional[np.ndarray]  # 4x4 transformation matrix
    antennas: Optional[np.ndarray]   # [left, right] angles in radians
    body_yaw: Optional[float]        # Body rotation in radians
    duration: float                  # Movement duration in seconds
    interpolation: str               # "minjerk", "linear", "ease", "cartoon"
```

### WaitAction (IR)

Intermediate representation of a wait/pause.

```python
@dataclass
class WaitAction:
    duration: float  # Wait duration in seconds
```


### CompilationResult

Complete compilation result with IR and metadata:

```python
@dataclass
class CompilationResult:
    name: str                        # Script name
    description: str                 # Script description
    success: bool                    # Compilation succeeded?
    errors: List[CompilationError]   # Compilation errors
    warnings: List[CompilationError] # Compilation warnings
    source_code: str                 # Original source
    source_file_path: Optional[str]  # Source file path (if from file)
    ir: List[IRAction | ...]         # Intermediate representation
```

## Developing Custom Adapters

Adapters are the execution layer for rmscript. They consume IR and execute it in context-specific ways.

### Adapter Protocol

All adapters must implement the `ExecutionAdapter` protocol:

```python
from typing import Protocol, Dict, Any
from rmscript import ExecutionContext
from rmscript.types import IRList

class ExecutionAdapter(Protocol):
    def execute(self, ir: IRList, context: ExecutionContext) -> Dict[str, Any]:
        """Execute IR and return results."""
        ...
```

### Creating an Execution Context

Extend `ExecutionContext` with your adapter-specific data:

```python
from dataclasses import dataclass
from rmscript import ExecutionContext

@dataclass
class RobotContext(ExecutionContext):
    """Context for robot execution."""
    robot: Any  # Your robot instance
    verbose: bool = False
```

### Implementing an Adapter

**Queue-based execution example:**

```python
from rmscript import compile_script
from rmscript.ir import IRAction, IRWaitAction, IRPictureAction
import time

class QueueExecutionAdapter:
    """Executes IR using robot's movement queue."""

    def execute(self, ir, context: RobotContext) -> Dict[str, Any]:
        result = {"success": True, "actions": 0}

        for action in ir:
            if isinstance(action, IRAction):
                # Queue movement
                context.robot.goto_target(
                    head_pose=action.head_pose,
                    antennas=action.antennas,
                    body_yaw=action.body_yaw,
                    duration=action.duration
                )
                result["actions"] += 1

            elif isinstance(action, IRWaitAction):
                time.sleep(action.duration)
                result["actions"] += 1

        return result

# Usage
result = compile_script("look left\nwait 1s")
adapter = QueueExecutionAdapter()
context = RobotContext(script_name=result.name,
                       script_description=result.description,
                       robot=my_robot)
adapter.execute(result.ir, context)
```

### Common Adapter Patterns

**1. Queue-based (synchronous):**
- Converts IR to robot movement queue
- Blocks until each action completes
- Best for: Physical robots, direct control

**2. WebSocket streaming (asynchronous):**
- Streams pose parameters over network
- Non-blocking, event-driven
- Best for: Remote robots, web interfaces

**3. Simulation (virtual):**
- Drives virtual robot model
- Fast, no hardware required
- Best for: Testing, development, visualization

**4. Recording (data collection):**
- Saves IR as timeline/animation data
- No execution, just data storage
- Best for: Offline processing, analysis

### Complete Example

See [examples/adapter_example.py](examples/adapter_example.py) for a complete, documented adapter implementation including:
- Error handling
- Picture capture
- Sound playback
- Multiple adapter patterns

## Contributing

To extend rmscript:

1. **Add new keywords**: Update `lexer.py`, `parser.py`, and `semantic.py`
2. **Add new features**: Modify the appropriate compiler stage
3. **Add tests**: Create integration tests in `tests/test_rmscript/`
4. **Update docs**: Keep this README and examples current