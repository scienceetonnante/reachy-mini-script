"""Optimizer for ReachyMiniScript - further optimize IR for execution."""

# Note: probably overkill for now, but useful if we want to add more optimizations later.

import numpy as np

from rmscript.ir import IRAction, IRWaitAction
from rmscript.types import IRList


def _rot_z(yaw: float) -> np.ndarray:
    """4x4 homogeneous rotation about the Z (yaw) axis, angle in radians."""
    c, s = np.cos(yaw), np.sin(yaw)
    return np.array(
        [
            [c, -s, 0.0, 0.0],
            [s, c, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )


class Optimizer:
    """Optimizes intermediate representation."""

    def optimize(self, ir: IRList) -> IRList:
        """Optimize IR.

        Current optimizations:
        - Merge consecutive wait actions
        - Remove no-op actions
        - Make head poses body-relative (compose with the running body yaw)

        Future optimizations:
        - Combine compatible actions with same duration
        - Minimize movement time
        """
        ir = self._make_head_poses_body_relative(ir)

        optimized: IRList = []

        i = 0
        while i < len(ir):
            action = ir[i]

            # Merge consecutive waits
            if isinstance(action, IRWaitAction):
                total_wait = action.duration
                j = i + 1
                while j < len(ir):
                    next_action = ir[j]
                    if isinstance(next_action, IRWaitAction):
                        total_wait += next_action.duration
                        j += 1
                    else:
                        break

                optimized.append(
                    IRWaitAction(
                        duration=total_wait,
                        source_line=action.source_line,
                        original_text=f"wait {total_wait}s",
                    )
                )
                i = j
                continue

            # Remove no-op actions (no actual movement)
            if isinstance(action, IRAction):
                if action.head_pose is None and action.antennas is None and action.body_yaw is None:
                    # Skip this action - it does nothing
                    i += 1
                    continue

            optimized.append(action)
            i += 1

        return optimized

    def _make_head_poses_body_relative(self, ir: IRList) -> IRList:
        """Express each head pose relative to the current body yaw axis.

        ``look`` (and ``tilt``/``head``) build their head pose from neutral,
        relative to the body axis (body_yaw = 0). ``body`` only sets the body
        yaw. To express both in the world frame - and to keep the head's look
        offset across body moves while never letting ``look`` drive the body
        motor - we walk the IR in order and carry two pieces of running state:

        - ``body_yaw``: the current body yaw, updated by ``body`` lines.
        - ``rel_head``: the head pose relative to the body axis (its look / tilt
          / translation offset), updated by head lines.

        Each line that moves the carriage (body and/or head) re-emits the head
        pose composed into the world frame and pins the body yaw::

            world_pose = Rz(body_yaw) @ rel_head

        This makes the two interactions symmetric:

        - ``look`` after ``body`` keeps the body yaw and offsets the head
          relative to it.
        - ``body`` after ``look`` keeps the head's look offset and rotates it
          with the new body yaw (this is the case that used to reset the look).

        Head commands stay absolute per line: a head line replaces ``rel_head``
        (rebuilt from neutral), so ``look up`` after ``look left`` does not keep
        the previous yaw. The composition is exact because yaw is the outermost
        rotation in ``create_head_pose`` (Rz . Ry . Rx), so it adds to the head
        yaw while correctly rotating pitch/roll/translation. State is statically
        known here because ``repeat`` blocks are fully expanded before
        optimization and the language has no conditionals or randomness.
        """
        body_yaw = 0.0  # running body yaw, in radians (matches IR units)
        rel_head = np.eye(4)  # running head pose relative to the body axis

        for action in ir:
            if not isinstance(action, IRAction):
                continue

            moved_carriage = False

            if action.body_yaw is not None:
                # A `body` move: update the tracked body yaw, keep the look offset.
                body_yaw = action.body_yaw
                moved_carriage = True

            if action.head_pose is not None:
                # A head move (`look`/`tilt`/`head`): its pose is body-relative
                # and rebuilt from neutral, so it replaces the running offset.
                rel_head = action.head_pose
                moved_carriage = True

            if moved_carriage:
                # Re-emit in the world frame and pin the body so the kinematics
                # solve the intended head/body differential. Antenna-only (and
                # non-movement) actions don't move the carriage and are untouched.
                action.head_pose = _rot_z(body_yaw) @ rel_head
                action.body_yaw = body_yaw

        return ir
