"""Basic usage example for rmscript package."""

from rmscript import compile_script, compile_file, verify_script

# Example 1: Compile inline script
print("Example 1: Compile inline script")
print("=" * 50)

source = """
DESCRIPTION Wave hello
look left
antenna both up
wait 1s
look right
"""

result = compile_script(source)

print(f"Success: {result.success}")
print(f"Name: {result.name}")
print(f"Description: {result.description}")
print(f"IR actions: {len(result.ir)}")

if result.success:
    for i, action in enumerate(result.ir):
        print(f"  {i+1}. {type(action).__name__}")
else:
    for error in result.errors:
        print(f"  {error}")

print()

# Example 2: Verify script (quick syntax check)
print("Example 2: Verify script syntax")
print("=" * 50)

is_valid, errors = verify_script("look left\nwait 1s\nlook right")
print(f"Valid: {is_valid}")
if errors:
    for error in errors:
        print(f"  {error}")

print()

# Example 3: Compile with errors
print("Example 3: Compile script with errors")
print("=" * 50)

bad_source = """
DESCRIPTION Test errors
antenna
turn left 999
"""

result = compile_script(bad_source)
print(f"Success: {result.success}")
print(f"Errors: {len(result.errors)}")
print(f"Warnings: {len(result.warnings)}")

for error in result.errors:
    print(f"  {error}")

for warning in result.warnings:
    print(f"  {warning}")

print()

# Example 4: Understanding IR structure
print("Example 4: Understanding IR structure")
print("=" * 50)

source = """
DESCRIPTION Complex movement
turn left 45
look up and tilt left
wait 2s
"""

result = compile_script(source)

if result.success:
    from rmscript.ir import IRAction, IRWaitAction

    for action in result.ir:
        if isinstance(action, IRAction):
            print(f"Action:")
            if action.head_pose is not None:
                print(f"  - Head pose: 4x4 matrix")
            if action.antennas is not None:
                print(f"  - Antennas: {action.antennas}")
            if action.body_yaw is not None:
                print(f"  - Body yaw: {action.body_yaw:.3f} rad")
            print(f"  - Duration: {action.duration}s")
        elif isinstance(action, IRWaitAction):
            print(f"Wait: {action.duration}s")

print()

# Example 5: Adapter pattern (demonstration)
print("Example 5: Adapter pattern demonstration")
print("=" * 50)

print("The rmscript package provides IR output only.")
print("To execute, create an adapter that implements ExecutionAdapter protocol:")
print()
print("from rmscript import ExecutionAdapter, ExecutionContext")
print("from dataclasses import dataclass")
print()
print("@dataclass")
print("class MyContext(ExecutionContext):")
print("    robot: Any  # Your robot instance")
print()
print("class MyAdapter:")
print("    def execute(self, ir, context: MyContext):")
print("        for action in ir:")
print("            # Execute each IR action on your robot")
print("            context.robot.move(action)")
print("        return {'status': 'complete'}")
print()
print("# Usage:")
print("result = compile_script('look left')")
print("adapter = MyAdapter()")
print("context = MyContext(script_name=result.name, script_description=result.description, robot=my_robot)")
print("adapter.execute(result.ir, context)")
