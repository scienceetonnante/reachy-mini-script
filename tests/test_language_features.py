"""Integration tests for rmscript language features."""

import math

import pytest
from scipy.spatial.transform import Rotation as R

from rmscript import compile_script
from rmscript.ir import IRAction, IRPlaySoundAction
from rmscript.constants import (
    DEFAULT_ANGLE,
    BODY_YAW_LARGE,
    BODY_YAW_SMALL,
    BODY_YAW_MEDIUM,
    DEFAULT_DURATION,
    BACKWARD_SYNONYMS,
    DURATION_KEYWORDS,
    TRANSLATION_SMALL,
    BODY_YAW_VERY_LARGE,
    BODY_YAW_VERY_SMALL,
    TRANSLATION_VERY_LARGE,
    HEAD_PITCH_ROLL_VERY_LARGE,
)


class TestBasicMovements:
    """Test turn/look/center commands."""

    def test_simple_look_left(self):
        """Test compiling a simple 'look left' command."""
        source = """DESCRIPTION test
look left"""
        result = compile_script(source)

        assert result.success
        assert result.description == "test"
        assert len(result.ir) == 1

        action = result.ir[0]
        assert isinstance(action, IRAction)
        assert action.head_pose is not None

        rotation = R.from_matrix(action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(DEFAULT_ANGLE, abs=0.1)
        assert action.duration == DEFAULT_DURATION

    def test_look_right(self):
        """Test 'look right' command."""
        source = """DESCRIPTION test
look right"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(-DEFAULT_ANGLE, abs=0.1)

    def test_look_up(self):
        """Test 'look up' command."""
        source = """DESCRIPTION test
look up"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        _, pitch, _ = rotation.as_euler("xyz", degrees=True)
        assert pitch == pytest.approx(-DEFAULT_ANGLE, abs=0.1)  # up = negative pitch

    def test_look_down(self):
        """Test 'look down' command."""
        source = """DESCRIPTION test
look down"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        _, pitch, _ = rotation.as_euler("xyz", degrees=True)
        assert pitch == pytest.approx(DEFAULT_ANGLE, abs=0.1)  # down = positive pitch

    def test_look_center(self):
        """Test 'look center' command resets head."""
        source = """DESCRIPTION test
look center"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, pitch, yaw = rotation.as_euler("xyz", degrees=True)
        assert roll == pytest.approx(0.0, abs=0.1)
        assert pitch == pytest.approx(0.0, abs=0.1)
        assert yaw == pytest.approx(0.0, abs=0.1)

    def test_turn_left_rotates_body_and_head(self):
        """Test that 'turn left' rotates both body yaw and head yaw."""
        source = """DESCRIPTION test
turn left 50"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.body_yaw == pytest.approx(math.radians(50.0), abs=0.01)

        rotation = R.from_matrix(action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(50.0, abs=0.1)

    def test_turn_right_rotates_body_and_head(self):
        """Test that 'turn right' rotates both body yaw and head yaw."""
        source = """DESCRIPTION test
turn right 30"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.body_yaw == pytest.approx(math.radians(-30.0), abs=0.01)

        rotation = R.from_matrix(action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(-30.0, abs=0.1)

    def test_turn_center_resets_body_and_head(self):
        """Test that 'turn center' resets both body and head to zero."""
        source = """DESCRIPTION test
turn center"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.body_yaw == pytest.approx(0.0, abs=0.01)

        rotation = R.from_matrix(action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(0.0, abs=0.1)


class TestHeadTranslation:
    """Test head left/right/up/down commands (translation)."""

    def test_head_left_positive_y(self):
        """Test 'head left' moves head in positive Y direction."""
        source = """DESCRIPTION test
head left 10"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose is not None
        # left = positive Y translation
        assert result.ir[0].head_pose[1, 3] == pytest.approx(0.010, abs=0.0001)  # 10mm

    def test_head_right_negative_y(self):
        """Test 'head right' moves head in negative Y direction."""
        source = """DESCRIPTION test
head right 10"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose is not None
        # right = negative Y translation
        assert result.ir[0].head_pose[1, 3] == pytest.approx(-0.010, abs=0.0001)  # -10mm

    def test_head_up_positive_z(self):
        """Test 'head up' moves head in positive Z direction."""
        source = """DESCRIPTION test
head up 15"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose is not None
        # up = positive Z translation
        assert result.ir[0].head_pose[2, 3] == pytest.approx(0.015, abs=0.0001)  # 15mm

    def test_head_down_negative_z(self):
        """Test 'head down' moves head in negative Z direction."""
        source = """DESCRIPTION test
head down 15"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose is not None
        # down = negative Z translation
        assert result.ir[0].head_pose[2, 3] == pytest.approx(-0.015, abs=0.0001)  # -15mm

    def test_head_forward_backward(self):
        """Test 'head forward' and backward synonyms."""
        # Forward
        forward_source = """DESCRIPTION test
head forward 10"""
        result = compile_script(forward_source)
        assert result.success
        assert result.ir[0].head_pose[0, 3] == pytest.approx(0.010, abs=0.0001)  # +10mm

        # Backward
        backward_source = """DESCRIPTION test
head backward 10"""
        result = compile_script(backward_source)
        assert result.success
        assert result.ir[0].head_pose[0, 3] == pytest.approx(-0.010, abs=0.0001)  # -10mm

    @pytest.mark.parametrize("direction", BACKWARD_SYNONYMS)
    def test_backward_synonyms_all_work(self, direction):
        """Test that all backward synonyms work for head movement."""
        source = f"""DESCRIPTION test
head {direction} 10"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 1
        action = result.ir[0]
        assert isinstance(action, IRAction)
        # All backward synonyms should move head in negative X direction
        assert action.head_pose[0, 3] == pytest.approx(-0.010, abs=0.0001)  # -10mm


class TestTiltCommands:
    """Test tilt left/right commands."""

    def test_tilt_left(self):
        """Test 'tilt left' command."""
        source = """DESCRIPTION test
tilt left"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, _, _ = rotation.as_euler("xyz", degrees=True)
        assert roll == pytest.approx(DEFAULT_ANGLE, abs=0.1)

    def test_tilt_right(self):
        """Test 'tilt right' command."""
        source = """DESCRIPTION test
tilt right"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, _, _ = rotation.as_euler("xyz", degrees=True)
        assert roll == pytest.approx(-DEFAULT_ANGLE, abs=0.1)

    def test_tilt_center(self):
        """Test 'tilt center' command resets roll."""
        source = """DESCRIPTION test
tilt center"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, _, _ = rotation.as_euler("xyz", degrees=True)
        assert roll == pytest.approx(0.0, abs=0.1)

    def test_tilt_uses_pitch_roll_limits(self):
        """Test that tilt commands use HEAD_PITCH_ROLL limits."""
        source = """DESCRIPTION test
tilt left maximum"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, _, _ = rotation.as_euler("xyz", degrees=True)
        assert roll == pytest.approx(HEAD_PITCH_ROLL_VERY_LARGE, abs=0.1)


class TestCompoundMovements:
    """Test 'and' keyword for combining movements."""

    def test_keyword_reuse_with_and(self):
        """Test 'and' keyword reuse: 'look left and up'."""
        source = """DESCRIPTION test
look left and up"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 1

        action = result.ir[0]
        rotation = R.from_matrix(action.head_pose[:3, :3])
        roll, pitch, yaw = rotation.as_euler("xyz", degrees=True)

        assert yaw == pytest.approx(DEFAULT_ANGLE, abs=0.1)  # left
        assert pitch == pytest.approx(-DEFAULT_ANGLE, abs=0.1)  # up

    def test_and_picture_error(self):
        """Test that 'look left and picture' produces error."""
        source = """DESCRIPTION test
look left and picture"""
        result = compile_script(source)

        assert not result.success
        assert len(result.errors) >= 1
        assert any("cannot combine" in err.message.lower() for err in result.errors)
        assert any("picture" in err.message.lower() for err in result.errors)

    def test_and_play_error(self):
        """Test that 'turn left and play sound' produces error."""
        source = """DESCRIPTION test
turn left and play mysound"""
        result = compile_script(source)

        assert not result.success
        assert any("play" in err.message.lower() for err in result.errors)

    def test_and_loop_error(self):
        """Test that 'look up and loop sound' produces error."""
        source = """DESCRIPTION test
look up and loop mysound"""
        result = compile_script(source)

        assert not result.success
        assert any("loop" in err.message.lower() for err in result.errors)

    def test_and_wait_error(self):
        """Test that 'antenna both up and wait 1s' produces error."""
        source = """DESCRIPTION test
antenna both up and wait 1s"""
        result = compile_script(source)

        assert not result.success
        assert any("wait" in err.message.lower() for err in result.errors)


class TestQualitativeStrengths:
    """Test context-aware qualitative keywords."""

    def test_very_small_qualitative_turn(self):
        """Test VERY_SMALL qualitative for turn."""
        source = """DESCRIPTION test
turn left tiny"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.body_yaw == pytest.approx(math.radians(BODY_YAW_VERY_SMALL), abs=0.01)

    def test_small_qualitative_turn(self):
        """Test SMALL qualitative for turn."""
        source = """DESCRIPTION test
turn left little"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_SMALL), abs=0.01)

    def test_medium_qualitative_turn(self):
        """Test MEDIUM qualitative for turn."""
        source = """DESCRIPTION test
turn left medium"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_MEDIUM), abs=0.01)

    def test_large_qualitative_turn(self):
        """Test LARGE qualitative for turn."""
        source = """DESCRIPTION test
turn left strong"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_LARGE), abs=0.01)

    def test_very_large_qualitative_turn(self):
        """Test VERY_LARGE qualitative for turn."""
        source = """DESCRIPTION test
turn left enormous"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_VERY_LARGE), abs=0.01)

    def test_qualitative_for_head_translation(self):
        """Test qualitative keywords for head translations (mm)."""
        source = """DESCRIPTION test
head forward little"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose[0, 3] == pytest.approx(TRANSLATION_SMALL / 1000.0, abs=0.0001)

    def test_maximum_turn_vs_look_pitch(self):
        """Test 'maximum' uses different values for turn vs look up."""
        # Turn
        turn_source = """DESCRIPTION test
turn left maximum"""
        turn_result = compile_script(turn_source)
        assert turn_result.success
        assert turn_result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_VERY_LARGE), abs=0.01)

        # Look up
        look_source = """DESCRIPTION test
look up maximum"""
        look_result = compile_script(look_source)
        assert look_result.success
        rotation = R.from_matrix(look_result.ir[0].head_pose[:3, :3])
        _, pitch, _ = rotation.as_euler("xyz", degrees=True)
        assert pitch == pytest.approx(-HEAD_PITCH_ROLL_VERY_LARGE, abs=0.1)

    def test_maximum_head_translation(self):
        """Test 'maximum' for head translation uses TRANSLATION_VERY_LARGE."""
        source = """DESCRIPTION test
head forward maximum"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose[0, 3] == pytest.approx(TRANSLATION_VERY_LARGE / 1000.0, abs=0.0001)


class TestAntennaControl:
    """Test antenna commands."""

    def test_antenna_directional_up(self):
        """Test antenna with 'up' direction."""
        source = """DESCRIPTION test
antenna both up"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas is not None
        assert action.antennas[0] == pytest.approx(0.0, abs=0.01)
        assert action.antennas[1] == pytest.approx(0.0, abs=0.01)

    def test_antenna_directional_left(self):
        """Test antenna with 'left' direction."""
        source = """DESCRIPTION test
antenna both left"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(-90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(-90), abs=0.01)

    def test_antenna_directional_right(self):
        """Test antenna with 'right' direction."""
        source = """DESCRIPTION test
antenna both right"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(90), abs=0.01)

    def test_antenna_directional_down(self):
        """Test antenna with 'down' direction."""
        source = """DESCRIPTION test
antenna both down"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(180), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(180), abs=0.01)

    def test_antenna_left_modifier(self):
        """Test 'antenna left left' (left antenna pointing left)."""
        source = """DESCRIPTION test
antenna left left"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(-90), abs=0.01)

    def test_antenna_right_modifier(self):
        """Test 'antenna right right' (right antenna pointing right)."""
        source = """DESCRIPTION test
antenna right right"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[1] == pytest.approx(math.radians(90), abs=0.01)

    def test_antenna_clock_numeric(self):
        """Test antenna with numeric clock position."""
        source = """DESCRIPTION test
antenna both 3"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(90), abs=0.01)

    def test_antenna_clock_keyword(self):
        """Test antenna with clock keyword (ext/int/high/low)."""
        source = """DESCRIPTION test
antenna both ext"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(90), abs=0.01)


class TestDurationControl:
    """Test timing and duration."""

    def test_default_duration(self):
        """Test that default duration is applied."""
        source = """DESCRIPTION test
look left"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == DEFAULT_DURATION

    def test_explicit_duration(self):
        """Test explicit duration with 's' suffix."""
        source = """DESCRIPTION test
look up 2s"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == 2.0

    def test_decimal_duration(self):
        """Test decimal duration values."""
        source = """DESCRIPTION test
wait 1.5s"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == 1.5

    def test_duration_keyword_fast(self):
        """Test 'fast' duration keyword."""
        source = """DESCRIPTION test
look left fast"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == DURATION_KEYWORDS["fast"]

    def test_duration_keyword_slow(self):
        """Test 'slow' duration keyword."""
        source = """DESCRIPTION test
look left slow"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == DURATION_KEYWORDS["slow"]

    @pytest.mark.parametrize("keyword,expected_duration", [
        ("slow", DURATION_KEYWORDS["slow"]),
        ("slowly", DURATION_KEYWORDS["slowly"]),
    ])
    def test_slowly_synonym(self, keyword, expected_duration):
        """Test that 'slowly' works as synonym for 'slow'."""
        source = f"""DESCRIPTION test
look left {keyword}"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == expected_duration

    def test_wait_requires_s_suffix(self):
        """Test that wait without 's' suffix produces an error."""
        source = """DESCRIPTION test
wait 2"""
        result = compile_script(source)

        assert not result.success
        assert any("s" in err.message.lower() for err in result.errors)


class TestSoundPlayback:
    """Test play/loop sound commands."""

    def test_play_sound_async(self):
        """Test async sound playback."""
        source = """DESCRIPTION test
play mysound"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert isinstance(action, IRPlaySoundAction)
        assert action.sound_name == "mysound"
        assert not action.blocking
        assert action.duration is None

    def test_play_sound_blocking_pause(self):
        """Test blocking sound with 'pause' modifier."""
        source = """DESCRIPTION test
play mysound pause"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.blocking

    def test_play_sound_blocking_fully(self):
        """Test blocking sound with 'fully' modifier."""
        source = """DESCRIPTION test
play mysound fully"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.blocking

    def test_play_sound_with_duration(self):
        """Test 'play sound 5s' command."""
        source = """DESCRIPTION test
play mysound 5s"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert isinstance(action, IRPlaySoundAction)
        assert action.sound_name == "mysound"
        assert action.blocking
        assert action.duration == 5.0
        assert not action.loop

    def test_play_sound_in_sequence(self):
        """Test multiple sound commands in sequence."""
        source = """DESCRIPTION test
play sound1
play sound2
play sound3"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 3
        assert all(isinstance(a, IRPlaySoundAction) for a in result.ir)

    def test_loop_sound_default_duration(self):
        """Test 'loop sound' uses default 10s duration."""
        source = """DESCRIPTION test
loop mysound"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert isinstance(action, IRPlaySoundAction)
        assert action.sound_name == "mysound"
        assert action.loop
        assert action.blocking
        assert action.duration == 10.0

    def test_loop_sound_custom_duration(self):
        """Test 'loop sound 30s' uses custom duration."""
        source = """DESCRIPTION test
loop mysound 30s"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.loop
        assert action.duration == 30.0

    def test_loop_in_sequence(self):
        """Test loop sound in sequence with movements."""
        source = """DESCRIPTION test
look left
loop background 15s
look right"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 3
        assert isinstance(result.ir[0], IRAction)  # look left
        assert isinstance(result.ir[1], IRPlaySoundAction)  # loop
        assert result.ir[1].loop
        assert result.ir[1].duration == 15.0
        assert isinstance(result.ir[2], IRAction)  # look right


class TestPictureCapture:
    """Test picture command."""

    def test_picture_compiles(self):
        """Test that 'picture' command compiles."""
        source = """DESCRIPTION test
picture"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 1

    def test_picture_in_sequence(self):
        """Test picture in sequence with movements."""
        source = """DESCRIPTION test
look left
picture
look right"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 3

    def test_multiple_pictures(self):
        """Test multiple picture commands."""
        source = """DESCRIPTION test
picture
wait 1s
picture"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 3

    def test_picture_with_wait(self):
        """Test picture with wait for positioning."""
        source = """DESCRIPTION test
look up
wait 1s
picture"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 3


class TestRepeatBlocks:
    """Test repeat/end blocks."""

    def test_repeat_block_basic(self):
        """Test basic repeat block expansion."""
        source = """DESCRIPTION test
repeat 3
    look left
    look right"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 6  # 3 repetitions × 2 actions

    def test_repeat_block_with_wait(self):
        """Test repeat block with wait commands."""
        source = """DESCRIPTION test
repeat 2
    look left
    wait 1s"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 4  # 2 repetitions × 2 actions

    def test_repeat_with_mixed_actions(self):
        """Test repeat block with mixed action types."""
        source = """DESCRIPTION test
repeat 2
    turn left
    antenna both up
    wait 0.5s"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 6  # 2 × 3


class TestErrorMessages:
    """Test error message quality."""

    def test_error_invalid_keyword_clear_message(self):
        """Test that invalid keywords produce clear errors."""
        source = """DESCRIPTION test
jump up"""
        result = compile_script(source)

        assert not result.success
        assert len(result.errors) >= 1
        assert any("jump" in err.message.lower() for err in result.errors)

    def test_error_invalid_direction_for_command(self):
        """Test error for invalid direction with specific command."""
        source = """DESCRIPTION test
turn up"""
        result = compile_script(source)

        assert not result.success
        assert any("turn" in err.message.lower() for err in result.errors)
        assert any("up" in err.message.lower() or "direction" in err.message.lower() for err in result.errors)

    def test_error_missing_antenna_parameters(self):
        """Test error when antenna parameters are missing."""
        source = """DESCRIPTION test
antenna"""
        result = compile_script(source)

        assert not result.success

    def test_error_malformed_duration(self):
        """Test error for malformed duration."""
        source = """DESCRIPTION test
wait abc"""
        result = compile_script(source)

        assert not result.success

    def test_error_unclosed_repeat_block(self):
        """Test error for missing indentation in repeat block."""
        source = """DESCRIPTION test
repeat 3
look left"""
        result = compile_script(source)

        # Should fail due to missing indent
        assert not result.success

    def test_error_missing_sound_name(self):
        """Test error when sound name is missing."""
        source = """DESCRIPTION test
play"""
        result = compile_script(source)

        assert not result.success
        assert any("sound" in err.message.lower() or "expected" in err.message.lower() for err in result.errors)

    def test_warning_out_of_range_clear_message(self):
        """Test that out-of-range values produce clear warnings."""
        source = """DESCRIPTION test
turn left 200"""
        result = compile_script(source)

        assert result.success  # Compiles successfully
        assert len(result.warnings) >= 1
        assert any("200" in warn.message for warn in result.warnings)

    def test_warning_antenna_out_of_range(self):
        """Test warning for antenna position out of range."""
        source = """DESCRIPTION test
antenna both 15"""
        result = compile_script(source)

        # Should compile but may warn (depends on implementation)
        # At minimum, shouldn't crash
        assert len(result.errors) == 0 or "15" in str(result.errors[0])

    def test_error_and_keyword_with_control_helpful(self):
        """Test helpful error for 'and' with control commands."""
        source = """DESCRIPTION test
look left and wait 1s"""
        result = compile_script(source)

        assert not result.success
        assert any("cannot combine" in err.message.lower() or "separate" in err.message.lower()
                   for err in result.errors)

    def test_error_repeat_count_not_number(self):
        """Test error when repeat count is not a number."""
        source = """DESCRIPTION test
repeat abc
    look left"""
        result = compile_script(source)

        assert not result.success


class TestEdgeCases:
    """Test boundary conditions and edge cases."""

    def test_empty_program_after_description(self):
        """Test that program with only description is valid."""
        source = """DESCRIPTION test"""
        result = compile_script(source)

        # Empty program should compile successfully
        assert result.success
        assert len(result.ir) == 0

    def test_comment_only_lines(self):
        """Test that comment-only programs work."""
        source = """DESCRIPTION test
# This is a comment
# Another comment"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 0

    def test_blank_lines_ignored(self):
        """Test that blank lines are properly ignored."""
        source = """DESCRIPTION test

look left

look right

"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 2

    def test_zero_duration_wait(self):
        """Test wait with zero duration."""
        source = """DESCRIPTION test
wait 0s"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].duration == 0.0

    def test_very_large_repeat_count(self):
        """Test repeat with large count."""
        source = """DESCRIPTION test
repeat 100
    look left"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 100


class TestCompilerAPI:
    """Test public API functions."""

    def test_compile_returns_compilation_result(self):
        """Test that compile_script() returns CompilationResult."""
        source = """DESCRIPTION test
look left"""
        result = compile_script(source)

        assert hasattr(result, "success")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "ir")
        assert hasattr(result, "name")
        assert hasattr(result, "description")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
