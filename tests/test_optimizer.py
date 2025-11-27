"""Unit tests for rmscript IR optimizer."""

import numpy as np
import pytest

from rmscript.ir import IRAction, IRPictureAction, IRPlaySoundAction, IRWaitAction
from rmscript.optimizer import Optimizer


@pytest.fixture
def optimizer():
    """Reusable optimizer instance."""
    return Optimizer()


class TestOptimizer:
    """Test IR optimization."""

    def test_merge_consecutive_waits(self, optimizer):
        """Test that consecutive wait actions are merged."""
        ir = [
            IRWaitAction(duration=1.0, source_line=1),
            IRWaitAction(duration=2.0, source_line=2),
            IRWaitAction(duration=1.5, source_line=3),
        ]

        optimized = optimizer.optimize(ir)

        assert len(optimized) == 1
        assert isinstance(optimized[0], IRWaitAction)
        assert optimized[0].duration == 4.5

    def test_remove_noop_actions(self, optimizer):
        """Test that no-op actions are removed."""
        ir = [
            IRAction(head_pose=None, antennas=None, body_yaw=None, duration=1.0),
            IRAction(head_pose=np.eye(4), antennas=None, body_yaw=None, duration=1.0),
        ]

        optimized = optimizer.optimize(ir)

        # First action is no-op (all None), second has head_pose
        assert len(optimized) == 1
        assert optimized[0].head_pose is not None

    def test_preserve_non_mergeable_actions(self, optimizer):
        """Test that non-wait actions are preserved and not merged."""
        head_pose = np.eye(4)
        ir = [
            IRAction(head_pose=head_pose, duration=1.0),
            IRWaitAction(duration=1.0),
            IRAction(body_yaw=0.5, duration=1.0),
        ]

        optimized = optimizer.optimize(ir)

        # All three should be preserved (different types)
        assert len(optimized) == 3
        assert isinstance(optimized[0], IRAction)
        assert isinstance(optimized[1], IRWaitAction)
        assert isinstance(optimized[2], IRAction)

    def test_preserve_picture_and_sound_actions(self, optimizer):
        """Test that picture and sound actions are preserved."""
        ir = [
            IRPictureAction(source_line=1),
            IRPlaySoundAction(sound_name="test", source_line=2),
            IRWaitAction(duration=1.0, source_line=3),
        ]

        optimized = optimizer.optimize(ir)

        assert len(optimized) == 3
        assert isinstance(optimized[0], IRPictureAction)
        assert isinstance(optimized[1], IRPlaySoundAction)
        assert isinstance(optimized[2], IRWaitAction)

    def test_optimize_empty_ir(self, optimizer):
        """Test that optimizing empty IR returns empty list."""
        ir = []

        optimized = optimizer.optimize(ir)

        assert len(optimized) == 0

    def test_optimize_single_action_unchanged(self, optimizer):
        """Test that single actions pass through unchanged."""
        head_pose = np.eye(4)
        ir = [IRAction(head_pose=head_pose, duration=1.0, source_line=1)]

        optimized = optimizer.optimize(ir)

        assert len(optimized) == 1
        assert optimized[0] is ir[0]  # Same object

    def test_waits_not_merged_across_movements(self, optimizer):
        """Test waits separated by movements aren't merged."""
        ir = [
            IRWaitAction(duration=1.0),
            IRAction(head_pose=np.eye(4)),
            IRWaitAction(duration=1.0),
        ]

        optimized = optimizer.optimize(ir)

        # Should have 3 actions (waits not merged across movement)
        assert len(optimized) == 3
        assert isinstance(optimized[0], IRWaitAction)
        assert isinstance(optimized[1], IRAction)
        assert isinstance(optimized[2], IRWaitAction)

    def test_optimizer_with_mixed_noop_and_wait(self, optimizer):
        """Test optimizer handles no-op + wait correctly."""
        ir = [
            IRAction(),  # no-op
            IRWaitAction(duration=1.0),
            IRAction(),  # no-op
        ]

        optimized = optimizer.optimize(ir)

        # Both no-ops removed, wait preserved
        assert len(optimized) == 1
        assert isinstance(optimized[0], IRWaitAction)

    def test_consecutive_waits_preserve_first_metadata(self, optimizer):
        """Test that merged waits preserve metadata from first wait."""
        ir = [
            IRWaitAction(duration=1.0, source_line=10, original_text="wait 1s"),
            IRWaitAction(duration=2.0, source_line=11, original_text="wait 2s"),
        ]

        optimized = optimizer.optimize(ir)

        assert len(optimized) == 1
        # Should preserve first wait's line number
        assert optimized[0].source_line == 10

    def test_optimizer_preserves_action_order(self, optimizer):
        """Test that optimizer preserves relative order of actions."""
        ir = [
            IRAction(body_yaw=0.1, duration=1.0),
            IRWaitAction(duration=0.5),
            IRAction(head_pose=np.eye(4), duration=1.0),
            IRWaitAction(duration=0.5),
            IRPictureAction(),
        ]

        optimized = optimizer.optimize(ir)

        # Order should be: Action, Wait, Action, Wait, Picture
        assert isinstance(optimized[0], IRAction)
        assert isinstance(optimized[1], IRWaitAction)
        assert isinstance(optimized[2], IRAction)
        assert isinstance(optimized[3], IRWaitAction)
        assert isinstance(optimized[4], IRPictureAction)

    def test_zero_duration_waits_merged(self, optimizer):
        """Test that zero-duration waits are still merged."""
        ir = [
            IRWaitAction(duration=0.0),
            IRWaitAction(duration=1.0),
        ]

        optimized = optimizer.optimize(ir)

        assert len(optimized) == 1
        assert optimized[0].duration == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
