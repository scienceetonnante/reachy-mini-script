"""Example: Custom execution adapter for rmscript.

This example shows how to create a custom adapter that executes rmscript IR
on a Reachy Mini robot using the movement queue system.
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import time

from rmscript import compile_script, compile_file, ExecutionContext
from rmscript.ir import IRAction, IRWaitAction, IRPictureAction, IRPlaySoundAction
from rmscript.types import IRList


@dataclass
class RobotExecutionContext(ExecutionContext):
    """Execution context that includes robot instance."""

    robot: Any  # reachy_mini.ReachyMini instance
    verbose: bool = False


class QueueExecutionAdapter:
    """Adapter that executes rmscript IR using robot's movement queue.

    This adapter converts IR actions into robot movements by:
    1. Queuing movements to the robot's movement system
    2. Handling waits/pauses
    3. Capturing pictures when requested
    4. Playing sounds with proper timing
    """

    def execute(self, ir: IRList, context: RobotExecutionContext) -> Dict[str, Any]:
        """Execute IR actions on the robot.

        Args:
            ir: List of IR actions to execute
            context: Execution context with robot instance

        Returns:
            Dictionary with execution results:
            - success: bool
            - actions_executed: int
            - pictures: list of captured images (if any)
            - errors: list of error messages (if any)
        """
        result = {
            "success": True,
            "actions_executed": 0,
            "pictures": [],
            "errors": [],
        }

        robot = context.robot

        if context.verbose:
            print(f"Executing: {context.script_name}")
            print(f"Description: {context.script_description}")
            print(f"IR actions: {len(ir)}")

        try:
            for action in ir:
                if isinstance(action, IRAction):
                    # Execute movement action
                    self._execute_movement(action, robot, context.verbose)
                    result["actions_executed"] += 1

                elif isinstance(action, IRWaitAction):
                    # Execute wait
                    if context.verbose:
                        print(f"  Wait: {action.duration}s")
                    time.sleep(action.duration)
                    result["actions_executed"] += 1

                elif isinstance(action, IRPictureAction):
                    # Capture picture
                    if context.verbose:
                        print("  Picture: capturing...")
                    picture = self._capture_picture(robot)
                    result["pictures"].append(picture)
                    result["actions_executed"] += 1

                elif isinstance(action, IRPlaySoundAction):
                    # Play sound
                    if context.verbose:
                        mode = "blocking" if action.blocking else "background"
                        print(f"  Sound: {action.sound_name} ({mode})")
                    self._play_sound(action, context)
                    result["actions_executed"] += 1

        except Exception as e:
            result["success"] = False
            result["errors"].append(str(e))
            if context.verbose:
                print(f"  Error: {e}")

        return result

    def _execute_movement(
        self, action: IRAction, robot: Any, verbose: bool
    ) -> None:
        """Execute a movement action on the robot."""
        if verbose:
            parts = []
            if action.head_pose is not None:
                parts.append("head_pose")
            if action.antennas is not None:
                parts.append("antennas")
            if action.body_yaw is not None:
                parts.append(f"body_yaw={action.body_yaw:.2f}")
            print(f"  Move: {', '.join(parts)} (duration={action.duration}s)")

        # Queue movement to robot
        # This is where you'd call the actual robot API, e.g.:
        # robot.goto_target(
        #     head_pose=action.head_pose,
        #     antennas=action.antennas,
        #     body_yaw=action.body_yaw,
        #     duration=action.duration,
        #     interpolation_mode=action.interpolation
        # )

        # For this example, we just simulate the movement
        time.sleep(action.duration)

    def _capture_picture(self, robot: Any) -> Optional[bytes]:
        """Capture a picture from the robot's camera."""
        # This is where you'd call the actual robot camera API, e.g.:
        # return robot.camera.capture()

        # For this example, return None
        return None

    def _play_sound(
        self, action: IRPlaySoundAction, context: RobotExecutionContext
    ) -> None:
        """Play a sound file."""
        # This is where you'd call the actual audio playback system
        # Handle blocking vs non-blocking playback based on action.blocking

        if action.blocking and action.duration:
            time.sleep(action.duration)


# ============================================================================
# Example Usage
# ============================================================================


def example_compile_and_execute():
    """Example: Compile and execute rmscript code."""
    print("=" * 70)
    print("Example 1: Compile inline script and execute")
    print("=" * 70)

    source = """
DESCRIPTION Wave hello to the user
look left
antenna both up
wait 1s
look right
antenna both down
wait 0.5s
look center
"""

    # Compile the script
    result = compile_script(source)

    if not result.success:
        print("Compilation failed!")
        for error in result.errors:
            print(f"  {error}")
        return

    print(f"✓ Compiled successfully: {result.name}")
    print(f"  IR actions: {len(result.ir)}")

    # Create adapter and context
    adapter = QueueExecutionAdapter()

    # Note: In real usage, you'd create a ReachyMini instance:
    # from reachy_mini import ReachyMini
    # with ReachyMini() as mini:
    #     context = RobotExecutionContext(
    #         script_name=result.name,
    #         script_description=result.description,
    #         robot=mini,
    #         verbose=True
    #     )
    #     exec_result = adapter.execute(result.ir, context)

    # For this example, we use a mock robot
    mock_robot = None
    context = RobotExecutionContext(
        script_name=result.name,
        script_description=result.description,
        robot=mock_robot,
        verbose=True,
    )

    # Execute
    print("\nExecuting IR:")
    exec_result = adapter.execute(result.ir, context)

    print(f"\n✓ Execution complete")
    print(f"  Actions executed: {exec_result['actions_executed']}")
    print(f"  Success: {exec_result['success']}")


def example_compile_file():
    """Example: Compile rmscript file and execute."""
    print("\n")
    print("=" * 70)
    print("Example 2: Compile from file")
    print("=" * 70)

    # Compile from file
    result = compile_file("examples/example.rmscript")

    if not result.success:
        print("Compilation failed!")
        for error in result.errors:
            print(f"  {error}")
        return

    print(f"✓ Compiled successfully: {result.name}")
    print(f"  Source file: {result.source_file_path}")
    print(f"  IR actions: {len(result.ir)}")

    # Execute (same as example 1)
    adapter = QueueExecutionAdapter()
    context = RobotExecutionContext(
        script_name=result.name,
        script_description=result.description,
        robot=None,  # Mock robot
        verbose=True,
    )

    print("\nExecuting IR:")
    exec_result = adapter.execute(result.ir, context)

    print(f"\n✓ Execution complete")
    print(f"  Actions executed: {exec_result['actions_executed']}")


def example_custom_adapter():
    """Example: Create a custom adapter for a different execution model."""
    print("\n")
    print("=" * 70)
    print("Example 3: Custom adapter (WebSocket streaming)")
    print("=" * 70)

    class WebSocketStreamingAdapter:
        """Adapter that streams IR over WebSocket instead of executing locally."""

        def __init__(self, websocket_url: str):
            self.websocket_url = websocket_url

        def execute(self, ir: IRList, context: ExecutionContext) -> Dict[str, Any]:
            """Stream IR actions over WebSocket."""
            print(f"Streaming to: {self.websocket_url}")
            print(f"Script: {context.script_name}")

            for i, action in enumerate(ir):
                # In real implementation, send action over WebSocket
                print(f"  [{i+1}/{len(ir)}] Streaming {type(action).__name__}")

            return {"success": True, "streamed_actions": len(ir)}

    # Usage
    source = "DESCRIPTION Test\nlook left\nwait 1s\nlook right"
    result = compile_script(source)

    if result.success:
        adapter = WebSocketStreamingAdapter("ws://localhost:8080/robot")
        context = ExecutionContext(
            script_name=result.name, script_description=result.description
        )
        exec_result = adapter.execute(result.ir, context)
        print(f"✓ Streamed {exec_result['streamed_actions']} actions")


if __name__ == "__main__":
    example_compile_and_execute()
    example_compile_file()
    example_custom_adapter()
