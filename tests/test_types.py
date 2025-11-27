"""Tests for rmscript type definitions."""

import pytest

from rmscript.types import IRActionType, IRList
from rmscript.ir import IRAction, IRWaitAction, IRPictureAction, IRPlaySoundAction


class TestTypeDefinitions:
    """Test type aliases and definitions."""

    def test_ir_action_type_accepts_all_types(self):
        """Test IRActionType accepts all IR action types."""
        action: IRActionType = IRAction()
        wait: IRActionType = IRWaitAction(duration=1.0)
        picture: IRActionType = IRPictureAction()
        sound: IRActionType = IRPlaySoundAction(sound_name="test")

        # All should type-check without errors
        assert isinstance(action, IRAction)
        assert isinstance(wait, IRWaitAction)
        assert isinstance(picture, IRPictureAction)
        assert isinstance(sound, IRPlaySoundAction)

    def test_ir_list_type_alias(self):
        """Test IRList type alias works correctly."""
        ir_list: IRList = [
            IRAction(),
            IRWaitAction(duration=1.0),
            IRPictureAction(),
            IRPlaySoundAction(sound_name="test"),
        ]

        assert len(ir_list) == 4
        assert isinstance(ir_list[0], IRAction)
        assert isinstance(ir_list[1], IRWaitAction)
        assert isinstance(ir_list[2], IRPictureAction)
        assert isinstance(ir_list[3], IRPlaySoundAction)

    def test_empty_ir_list(self):
        """Test empty IRList."""
        ir_list: IRList = []

        assert len(ir_list) == 0
        assert isinstance(ir_list, list)

    def test_ir_list_homogeneous(self):
        """Test IRList with single type."""
        ir_list: IRList = [
            IRWaitAction(duration=1.0),
            IRWaitAction(duration=2.0),
            IRWaitAction(duration=3.0),
        ]

        assert len(ir_list) == 3
        assert all(isinstance(action, IRWaitAction) for action in ir_list)

    def test_ir_list_mixed(self):
        """Test IRList with mixed types."""
        ir_list: IRList = [
            IRAction(duration=1.0),
            IRWaitAction(duration=1.0),
            IRAction(duration=1.0),
            IRPictureAction(),
        ]

        assert len(ir_list) == 4
        # Can iterate and check types
        for action in ir_list:
            assert isinstance(
                action, (IRAction, IRWaitAction, IRPictureAction, IRPlaySoundAction)
            )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
