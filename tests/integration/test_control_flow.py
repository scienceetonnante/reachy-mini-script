"""Integration tests for control flow (repeat, wait, compound movements)."""

import pytest

from rmscript import compile_script
from rmscript.constants import DEFAULT_DURATION, DURATION_KEYWORDS
from rmscript.ir import IRAction, IRWaitAction


class TestCompoundMovements:
    """Test 'and' keyword for combining movements."""

    def test_keyword_reuse_with_and(self):
        """Test 'and' keyword reuse: 'look left and up'."""
        source = """"test"
look left and up"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 1

        from scipy.spatial.transform import Rotation as R
        from rmscript.constants import DEFAULT_ANGLE

        action = result.ir[0]
        rotation = R.from_matrix(action.head_pose[:3, :3])
        roll, pitch, yaw = rotation.as_euler("xyz", degrees=True)

        assert yaw == pytest.approx(DEFAULT_ANGLE, abs=0.1)  # left
        assert pitch == pytest.approx(-DEFAULT_ANGLE, abs=0.1)  # up

    def test_and_picture_error(self):
        """Test that 'look left and picture' produces error."""
        source = """"test"
look left and picture"""
        result = compile_script(source)

        assert not result.success
        assert len(result.errors) >= 1
        assert any("cannot combine" in err.message.lower() for err in result.errors)
        assert any("picture" in err.message.lower() for err in result.errors)

    def test_and_play_error(self):
        """Test that 'turn left and play sound' produces error."""
        source = """"test"
turn left and play mysound"""
        result = compile_script(source)

        assert not result.success
        assert any("play" in err.message.lower() for err in result.errors)

    def test_and_loop_error(self):
        """Test that 'look up and loop sound' produces error."""
        source = """"test"
look up and loop mysound"""
        result = compile_script(source)

        assert not result.success
        assert any("loop" in err.message.lower() for err in result.errors)

    def test_and_wait_error(self):
        """Test that 'antenna both up and wait 1s' produces error."""
        source = """"test"
antenna both up and wait 1s"""
        result = compile_script(source)

        assert not result.success
        assert any("wait" in err.message.lower() for err in result.errors)


class TestDurationControl:
    """Test timing and duration."""

    def test_default_duration(self):
        """Test that default duration is applied."""
        source = """"test"
look left"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == DEFAULT_DURATION

    def test_explicit_duration(self):
        """Test explicit duration with 's' suffix."""
        source = """"test"
look up 2s"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == 2.0

    def test_decimal_duration(self):
        """Test decimal duration values."""
        source = """"test"
wait 1.5s"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == 1.5

    def test_duration_keyword_fast(self):
        """Test 'fast' duration keyword."""
        source = """"test"
look left fast"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == DURATION_KEYWORDS["fast"]

    def test_duration_keyword_slow(self):
        """Test 'slow' duration keyword."""
        source = """"test"
look left slow"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == DURATION_KEYWORDS["slow"]

    @pytest.mark.parametrize(
        "keyword,expected_duration",
        [("slow", DURATION_KEYWORDS["slow"]), ("slowly", DURATION_KEYWORDS["slowly"])],
    )
    def test_slowly_synonym(self, keyword, expected_duration):
        """Test that 'slowly' works as synonym for 'slow'."""
        source = f""""test"
look left {keyword}"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == expected_duration

    def test_wait_requires_s_suffix(self):
        """Test that wait without 's' suffix produces an error."""
        source = """"test"
wait 2"""
        result = compile_script(source)

        assert not result.success
        assert any("s" in err.message.lower() for err in result.errors)


class TestRepeatBlocks:
    """Test repeat/end blocks."""

    def test_repeat_block_basic(self):
        """Test basic repeat block expansion."""
        source = """"test"
repeat 3
    look left
    look right"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 6  # 3 repetitions × 2 actions

    def test_repeat_block_with_wait(self):
        """Test repeat block with wait commands."""
        source = """"test"
repeat 2
    look left
    wait 1s"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 4  # 2 repetitions × 2 actions

    def test_repeat_with_mixed_actions(self):
        """Test repeat block with mixed action types."""
        source = """"test"
repeat 2
    turn left
    antenna both up
    wait 0.5s"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 6  # 2 × 3

    def test_nested_repeat_blocks(self):
        """Test nested repeat blocks expand correctly."""
        source = """"test"
repeat 2
    antenna both up
    repeat 3
        look left
        look right
    antenna both down"""
        result = compile_script(source)

        assert result.success
        # 2 * (1 antenna + 3*(2 looks) + 1 antenna) = 2 * 8 = 16
        assert len(result.ir) == 16

    def test_triple_nested_repeat(self):
        """Test deeply nested repeats."""
        source = """"test"
repeat 2
    repeat 2
        repeat 2
            look left"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 8  # 2 * 2 * 2

    def test_nested_repeat_preserves_order(self):
        """Test nested repeats preserve correct execution order."""
        source = """"test"
repeat 2
    look left
    repeat 2
        look right"""
        result = compile_script(source)

        assert result.success
        # Order: left, right, right, left, right, right
        assert len(result.ir) == 6

        # Verify all are IRAction (movements)
        assert all(isinstance(action, IRAction) for action in result.ir)


class TestCaseInsensitivity:
    """Test case insensitivity of keywords."""

    @pytest.mark.parametrize(
        "command",
        ["LOOK left", "Look Left", "loOk lEfT", "TURN right", "Turn Right", "tUrN rIgHt"],
    )
    def test_case_insensitive_movement_keywords(self, command):
        """Test that movement keywords work with any case."""
        source = f""""test"
{command}"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 1
        assert isinstance(result.ir[0], IRAction)

    @pytest.mark.parametrize(
        "command",
        [
            "ANTENNA both up",
            "Antenna Both Up",
            "antenna BOTH UP",
            "HEAD forward 10",
            "head FORWARD 10",
        ],
    )
    def test_case_insensitive_complex_commands(self, command):
        """Test case insensitivity for complex commands."""
        source = f""""test"
{command}"""
        result = compile_script(source)

        assert result.success

    def test_case_sensitive_sound_names(self):
        """Test sound names are case-sensitive."""
        result1 = compile_script('"test"\nplay MySound')
        result2 = compile_script('"test"\nplay mysound')

        from rmscript.ir import IRPlaySoundAction

        assert result1.ir[0].sound_name == "MySound"
        assert result2.ir[0].sound_name == "mysound"
        assert result1.ir[0].sound_name != result2.ir[0].sound_name

    def test_case_insensitive_repeat(self):
        """Test REPEAT keyword case insensitivity."""
        source = """"test"
REPEAT 2
    LOOK left"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 2

    def test_case_insensitive_wait(self):
        """Test WAIT keyword case insensitivity."""
        result = compile_script('"test"\nWAIT 1s')

        assert result.success
        assert isinstance(result.ir[0], IRWaitAction)


class TestInterpolationMode:
    """Test interpolation parameter."""

    def test_interpolation_default_minjerk(self):
        """Test default interpolation is minjerk."""
        result = compile_script('"test"\nlook left')

        assert result.success
        assert result.ir[0].interpolation == "minjerk"

    def test_interpolation_preserved_through_pipeline(self):
        """Test interpolation value survives optimization."""
        result = compile_script('"test"\nlook left\nlook right')

        assert all(action.interpolation == "minjerk" for action in result.ir)

    def test_interpolation_on_all_movement_types(self):
        """Test all movement types have interpolation."""
        source = """"test"
turn left
look up
head forward 10
tilt left
antenna both up"""
        result = compile_script(source)

        assert result.success
        # All should be IRAction with interpolation
        for action in result.ir:
            assert isinstance(action, IRAction)
            assert action.interpolation == "minjerk"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
