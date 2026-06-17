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
        implicitly assuming the body faces forward (body_yaw = 0). But the body
        may have been rotated by a previous ``body``. To make a head movement
        relative to *that* axis - and to keep ``look`` from ever driving the
        body yaw motor - we walk the IR in order, track the running body yaw,
        and compose each body-less head pose with it:

            world_pose = Rz(body_yaw) @ relative_pose

        We also pin ``body_yaw`` on those actions to the current value so the
        kinematics solve the intended head/body differential without moving the
        body. This composition is exact because yaw is the outermost rotation in
        ``create_head_pose`` (Rz . Ry . Rx), so it simply adds to the head yaw
        while correctly rotating pitch/roll/translation.

        ``body`` actions already write their yaw into the head pose (head follows
        body), so their head pose is already world-frame and is left untouched;
        they only update the tracked body yaw. Body yaw is statically known here
        because ``repeat`` blocks are fully expanded before optimization and the
        language has no conditionals or randomness.
        """
        body_yaw = 0.0  # running body yaw, in radians (matches IR units)

        for action in ir:
            if not isinstance(action, IRAction):
                continue

            if action.body_yaw is not None:
                # A `body` (possibly combined with `look` on the same line).
                # Its head pose is already world-frame; just track the body yaw.
                body_yaw = action.body_yaw
            elif action.head_pose is not None:
                # A body-less head movement: compose with the current body yaw
                # and pin the body so `look` never spills into the body motor.
                action.head_pose = _rot_z(body_yaw) @ action.head_pose
                action.body_yaw = body_yaw

        return ir
