# rmscript

A kid-friendly robot programming language for Reachy Mini.

## Overview

rmscript is a simple, Python-like domain-specific language (DSL) designed to make robot programming accessible to children and beginners. It compiles to an intermediate representation (IR) that can be executed by different adapters (queue-based execution, WebSocket streaming, etc.).

## Installation

```bash
pip install rmscript
```

With optional dependencies:
```bash
pip install rmscript[reachy]  # For reachy_mini integration
pip install rmscript[scipy]   # For advanced transformations
```

## Quick Start

```python
from rmscript import compile_script

# Compile rmscript source
result = compile_script("""
DESCRIPTION Wave hello
look left
antenna both up
wait 1s
look right
""")

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

## Architecture

rmscript uses a 5-stage compilation pipeline:

```
Source → Lexer → Parser → Semantic Analyzer → Optimizer → IR
```

The compiler outputs **Intermediate Representation (IR)**, not executable code. Execution is handled by **adapters** that consume IR in different contexts.

## For Developers

### Adapters

Adapters execute IR in specific contexts. Example:

```python
from rmscript import compile_file, ExecutionAdapter, ExecutionContext
from dataclasses import dataclass

@dataclass
class MyContext(ExecutionContext):
    robot: Any

class MyAdapter:
    def execute(self, ir, context: MyContext) -> dict:
        for action in ir:
            # Execute each IR action
            if isinstance(action, IRAction):
                context.robot.move(action.head_pose)
        return {"status": "complete"}
```