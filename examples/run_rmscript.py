#!/usr/bin/env python3
"""Execute a rmscript file on the Reachy Mini robot.

Takes an argument that is a RMScript file and runs it.
It assumes the reachy_mini robot daemon is running and accessible.

Usage:
    python run_rmscript.py <script.rmscript>
    python run_rmscript.py example.rmscript
"""

import argparse
import logging
import sys
import time
from pathlib import Path

from reachy_mini import ReachyMini

from rmscript import compile_file
from rmscript.ir import IRAction, IRPictureAction, IRPlaySoundAction, IRWaitAction

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def execute_ir_on_robot(ir_actions: list, robot: ReachyMini, script_path: Path) -> None:
    """Execute IR actions directly on the robot."""
    logger.info(f"Executing {len(ir_actions)} actions on robot...")

    # Get script directory for relative sound file paths
    script_dir = script_path.parent

    for i, action in enumerate(ir_actions, 1):
        logger.info(f"Action {i}/{len(ir_actions)}: {action}")

        if isinstance(action, IRAction):
            # Handle movement action
            head_pose = action.head_pose
            antennas = action.antennas
            body_yaw = action.body_yaw
            duration = action.duration

            # goto_target requires at least one of head, antennas, or body_yaw
            if head_pose is not None or antennas is not None or body_yaw is not None:
                robot.goto_target(
                    head=head_pose,
                    antennas=antennas,
                    duration=duration,
                    body_yaw=body_yaw,
                )
                logger.info(f"  → Movement completed (duration={duration:.2f}s)")
            else:
                logger.warning("  → Skipping action with no movement")

        elif isinstance(action, IRWaitAction):
            # Handle wait action
            duration = action.duration
            logger.info(f"  → Waiting {duration:.2f}s...")
            time.sleep(duration)

        elif isinstance(action, IRPlaySoundAction):
            # Handle sound playback
            sound_name = action.sound_name
            logger.info(f"  → Playing sound: {sound_name}")

            # Search for sound file in multiple locations (priority order)
            search_locations = [
                # 1. Relative to script directory
                script_dir / sound_name,
                script_dir / f"{sound_name}.wav",
                # 2. Absolute path or relative to cwd
                Path(sound_name),
                Path(sound_name).with_suffix(".wav"),
                # 3. In sounds/ subdirectory relative to script
                script_dir / "sounds" / sound_name,
                script_dir / "sounds" / f"{sound_name}.wav",
                # 4. In sounds/ subdirectory relative to cwd
                Path("sounds") / sound_name,
                Path("sounds") / f"{sound_name}.wav",
            ]

            sound_path = None
            for location in search_locations:
                if location.exists():
                    sound_path = location
                    break

            if sound_path is None:
                logger.warning(f"  → Sound file not found: {sound_name}")
                logger.warning(f"     Searched in: {script_dir}, {Path.cwd()}, sounds/")
                continue

            logger.info(f"  → Found sound at: {sound_path}")
            robot.media.play_sound(str(sound_path))

            # If blocking, wait for the sound to finish
            if action.blocking and action.duration:
                time.sleep(action.duration)

        elif isinstance(action, IRPictureAction):
            # Handle picture capture
            logger.info("  → Capturing picture...")
            frame = robot.media.get_frame()

            if frame is not None:
                import cv2
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_path = f"/tmp/rmscript_picture_{timestamp}.jpg"
                cv2.imwrite(output_path, frame)
                logger.info(f"  → Picture saved to: {output_path}")
            else:
                logger.warning("  → Failed to capture picture (no frame available)")

    logger.info("Execution complete!")


def main() -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Execute a rmscript file on the Reachy Mini robot"
    )
    parser.add_argument(
        "script_file",
        type=str,
        help="Path to the rmscript file to execute"
    )
    parser.add_argument(
        "--localhost",
        action="store_true",
        default=True,
        help="Connect to localhost only (default: True)"
    )

    args = parser.parse_args()

    # Check if the script file exists
    script_path = Path(args.script_file)
    if not script_path.exists():
        logger.error(f"Script file not found: {script_path}")
        return 1

    logger.info(f"Compiling rmscript file: {script_path}")

    # Compile the rmscript file
    result = compile_file(str(script_path))

    if not result.success:
        logger.error("Compilation failed!")
        for error in result.errors:
            logger.error(f"  {error}")
        return 1

    if result.warnings:
        logger.warning("Compilation warnings:")
        for warning in result.warnings:
            logger.warning(f"  {warning}")

    logger.info(f"Compilation successful! Generated {len(result.ir)} IR actions")

    # Connect to robot
    logger.info("Connecting to Reachy Mini robot...")
    try:
        # Try to use gstreamer backend for robot speaker, fall back to default if not available
        try:
            robot = ReachyMini(localhost_only=args.localhost, media_backend="gstreamer")
            logger.info("Connected to robot with GStreamer backend (robot speaker)")
        except (ImportError, ModuleNotFoundError) as e:
            logger.warning(f"GStreamer backend not available: {e}")
            logger.warning("Falling back to default backend (computer speaker)")
            logger.warning("To use robot speaker, install: uv add 'reachy_mini[gstreamer]'")
            robot = ReachyMini(localhost_only=args.localhost, media_backend="default")
            logger.info("Connected to robot with default backend (computer speaker)")
    except Exception as e:
        logger.error(f"Failed to connect to robot: {e}")
        logger.error("Make sure the reachy_mini daemon is running")
        return 1

    # Execute the IR on the robot
    try:
        execute_ir_on_robot(result.ir, robot, script_path)
        return 0
    except KeyboardInterrupt:
        logger.info("\nExecution interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Execution failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
