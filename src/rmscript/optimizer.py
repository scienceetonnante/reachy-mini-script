"""Optimizer for ReachyMiniScript - further optimize IR for execution."""

from rmscript.ir import IRAction, IRWaitAction
from rmscript.types import IRList


class Optimizer:
    """Optimizes intermediate representation."""

    def optimize(self, ir: IRList) -> IRList:
        """Optimize IR.

        Current optimizations:
        - Merge consecutive wait actions
        - Remove no-op actions

        Future optimizations:
        - Combine compatible actions with same duration
        - Minimize movement time
        """
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
                if (
                    action.head_pose is None
                    and action.antennas is None
                    and action.body_yaw is None
                ):
                    # Skip this action - it does nothing
                    i += 1
                    continue

            optimized.append(action)
            i += 1

        return optimized
