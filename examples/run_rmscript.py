"""Execute a rmscript file on the Reachy Mini robot."""

import argparse
import logging
import sys
import time
from pathlib import Path

from reachy_mini import ReachyMini

from rmscript import compile_file
from rmscript.ir import IRAction, IRPictureAction, IRPlaySoundAction, IRWaitAction

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def execute_ir_on_robot(ir_actions: list, robot: ReachyMini, script_path: Path) -> None:
    """Execute IR actions directly on the robot."""
    logger.info(f"Executing {len(ir_actions)} actions on robot...")

    # Get script directory
    script_dir = script_path.parent

    for i, action in enumerate(ir_actions, 1):
        logger.info(f"Action {i}/{len(ir_actions)}: {action}")

        # (1) Movement action
        if isinstance(action, IRAction):
            head_pose = action.head_pose
            antennas = action.antennas
            body_yaw = action.body_yaw
            duration = action.duration

            robot.goto_target(
                head=head_pose,
                antennas=antennas,
                duration=duration,
                body_yaw=body_yaw,
            )
            logger.info(f"  → Movement completed (duration={duration:.2f}s)")

        # (2) Wait action
        elif isinstance(action, IRWaitAction):
            # Handle wait action
            duration = action.duration
            logger.info(f"  → Waiting {duration:.2f}s...")
            time.sleep(duration)

        # (3) Play sound action
        elif isinstance(action, IRPlaySoundAction):
            # Handle sound playback
            sound_name = action.sound_name
            logger.info(f"  → Playing sound: {sound_name}")

            # Search for sound file relative to the script, with various extensions
            search_locations = [script_dir / f"{sound_name}.{ext}" for ext in ["wav", "mp3", "ogg"]]
            sound_path = None
            for location in search_locations:
                if location.exists():
                    sound_path = location
                    break
            if sound_path is None:
                logger.warning(f"  → Sound file not found: {sound_name}")
                continue

            robot.media.play_sound(str(sound_path))

            # If blocking, wait for the sound to finish
            if action.blocking and action.duration:
                time.sleep(action.duration)

        # (4) Picture action
        elif isinstance(action, IRPictureAction):
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
    parser = argparse.ArgumentParser(description="Execute a rmscript file on the Reachy Mini robot")
    parser.add_argument("script_file", type=str, help="Path to the rmscript file to execute")
    parser.add_argument(
        "--host",
        type=str,
        default=None,
        help="Hostname or IP of the daemon for a networked (e.g. wireless) robot. "
        "If omitted, connects to a daemon running on this machine (localhost).",
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

    # Connect to robot.
    # - No --host: daemon runs on this machine. "localhost_only" lets the SDK
    #   use the LOCAL media backend (robot's own speaker/camera via IPC).
    # - With --host: networked/wireless robot, stream media over WebRTC.
    logger.info("Connecting to Reachy Mini robot...")
    if args.host:
        conn_kwargs = {"host": args.host, "connection_mode": "network"}
    else:
        conn_kwargs = {"connection_mode": "localhost_only"}
    try:
        # Prefer full media (robot speaker/camera); fall back to no_media so
        # movement still works if the media backend can't initialize.
        try:
            robot = ReachyMini(media_backend="default", **conn_kwargs)
            logger.info("Connected to robot (media enabled)")
        except Exception as media_err:
            logger.warning(f"Media backend unavailable ({media_err}); connecting without media")
            logger.warning("Sound and picture actions will be skipped")
            robot = ReachyMini(media_backend="no_media", **conn_kwargs)
            logger.info("Connected to robot (no media)")
    except Exception as e:
        logger.error(f"Failed to connect to robot: {e}")
        logger.error("Make sure the reachy_mini daemon is running")
        return 1

    # `look` (and other head movements) carry an explicit body_yaw in the IR and
    # must not spill into the body yaw motor. Disable automatic body yaw so the
    # kinematics use the per-action body_yaw we provide instead of redistributing
    # head yaw into the body.
    robot.set_automatic_body_yaw(False)

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
