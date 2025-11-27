"""Integration tests for movement commands (look, turn, head, tilt, antenna)."""

import math

import pytest
from scipy.spatial.transform import Rotation as R

from rmscript import compile_script
from rmscript.constants import (
    BACKWARD_SYNONYMS,
    BODY_YAW_LARGE,
    BODY_YAW_MEDIUM,
    BODY_YAW_SMALL,
    BODY_YAW_VERY_LARGE,
    BODY_YAW_VERY_SMALL,
    DEFAULT_ANGLE,
    DEFAULT_DURATION,
    HEAD_PITCH_ROLL_VERY_LARGE,
    TRANSLATION_SMALL,
    TRANSLATION_VERY_LARGE,
)
from rmscript.ir import IRAction


class TestBasicMovements:
    """Test turn/look/center commands."""

    def test_simple_look_left(self):
        """Test compiling a simple 'look left' command."""
        source = """"test"
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
        source = """"test"
look right"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(-DEFAULT_ANGLE, abs=0.1)

    def test_look_up(self):
        """Test 'look up' command."""
        source = """"test"
look up"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        _, pitch, _ = rotation.as_euler("xyz", degrees=True)
        assert pitch == pytest.approx(-DEFAULT_ANGLE, abs=0.1)  # up = negative pitch

    def test_look_down(self):
        """Test 'look down' command."""
        source = """"test"
look down"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        _, pitch, _ = rotation.as_euler("xyz", degrees=True)
        assert pitch == pytest.approx(DEFAULT_ANGLE, abs=0.1)  # down = positive pitch

    def test_look_center(self):
        """Test 'look center' command resets head."""
        source = """"test"
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
        source = """"test"
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
        source = """"test"
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
        source = """"test"
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
        source = """"test"
head left 10"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose is not None
        # left = positive Y translation
        assert result.ir[0].head_pose[1, 3] == pytest.approx(0.010, abs=0.0001)  # 10mm

    def test_head_right_negative_y(self):
        """Test 'head right' moves head in negative Y direction."""
        source = """"test"
head right 10"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose is not None
        # right = negative Y translation
        assert result.ir[0].head_pose[1, 3] == pytest.approx(-0.010, abs=0.0001)  # -10mm

    def test_head_up_positive_z(self):
        """Test 'head up' moves head in positive Z direction."""
        source = """"test"
head up 15"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose is not None
        # up = positive Z translation
        assert result.ir[0].head_pose[2, 3] == pytest.approx(0.015, abs=0.0001)  # 15mm

    def test_head_down_negative_z(self):
        """Test 'head down' moves head in negative Z direction."""
        source = """"test"
head down 15"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose is not None
        # down = negative Z translation
        assert result.ir[0].head_pose[2, 3] == pytest.approx(-0.015, abs=0.0001)  # -15mm

    def test_head_forward_backward(self):
        """Test 'head forward' and backward synonyms."""
        # Forward
        forward_source = """"test"
head forward 10"""
        result = compile_script(forward_source)
        assert result.success
        assert result.ir[0].head_pose[0, 3] == pytest.approx(0.010, abs=0.0001)  # +10mm

        # Backward
        backward_source = """"test"
head backward 10"""
        result = compile_script(backward_source)
        assert result.success
        assert result.ir[0].head_pose[0, 3] == pytest.approx(-0.010, abs=0.0001)  # -10mm

    @pytest.mark.parametrize("direction", BACKWARD_SYNONYMS)
    def test_backward_synonyms_all_work(self, direction):
        """Test that all backward synonyms work for head movement."""
        source = f""""test"
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
        source = """"test"
tilt left"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, _, _ = rotation.as_euler("xyz", degrees=True)
        assert roll == pytest.approx(DEFAULT_ANGLE, abs=0.1)

    def test_tilt_right(self):
        """Test 'tilt right' command."""
        source = """"test"
tilt right"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, _, _ = rotation.as_euler("xyz", degrees=True)
        assert roll == pytest.approx(-DEFAULT_ANGLE, abs=0.1)

    def test_tilt_center(self):
        """Test 'tilt center' command resets roll."""
        source = """"test"
tilt center"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, _, _ = rotation.as_euler("xyz", degrees=True)
        assert roll == pytest.approx(0.0, abs=0.1)

    def test_tilt_uses_pitch_roll_limits(self):
        """Test that tilt commands use HEAD_PITCH_ROLL limits."""
        source = """"test"
tilt left maximum"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, _, _ = rotation.as_euler("xyz", degrees=True)
        assert roll == pytest.approx(HEAD_PITCH_ROLL_VERY_LARGE, abs=0.1)


class TestAntennaControl:
    """Test antenna commands."""

    def test_antenna_directional_up(self):
        """Test antenna with 'up' direction."""
        source = """"test"
antenna both up"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas is not None
        assert action.antennas[0] == pytest.approx(0.0, abs=0.01)
        assert action.antennas[1] == pytest.approx(0.0, abs=0.01)

    def test_antenna_directional_left(self):
        """Test antenna with 'left' direction."""
        source = """"test"
antenna both left"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(-90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(-90), abs=0.01)

    def test_antenna_directional_right(self):
        """Test antenna with 'right' direction."""
        source = """"test"
antenna both right"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(90), abs=0.01)

    def test_antenna_directional_down(self):
        """Test antenna with 'down' direction."""
        source = """"test"
antenna both down"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(180), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(180), abs=0.01)

    def test_antenna_left_modifier(self):
        """Test 'antenna left left' (left antenna pointing left)."""
        source = """"test"
antenna left left"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(-90), abs=0.01)

    def test_antenna_right_modifier(self):
        """Test 'antenna right right' (right antenna pointing right)."""
        source = """"test"
antenna right right"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[1] == pytest.approx(math.radians(90), abs=0.01)

    def test_antenna_clock_numeric(self):
        """Test antenna with numeric clock position."""
        source = """"test"
antenna both 3"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(90), abs=0.01)

    def test_antenna_clock_keyword(self):
        """Test antenna with clock keyword (ext/int/high/low)."""
        source = """"test"
antenna both ext"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(90), abs=0.01)


class TestQualitativeStrengths:
    """Test context-aware qualitative keywords."""

    def test_very_small_qualitative_turn(self):
        """Test VERY_SMALL qualitative for turn."""
        source = """"test"
turn left tiny"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.body_yaw == pytest.approx(math.radians(BODY_YAW_VERY_SMALL), abs=0.01)

    def test_small_qualitative_turn(self):
        """Test SMALL qualitative for turn."""
        source = """"test"
turn left little"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_SMALL), abs=0.01)

    def test_medium_qualitative_turn(self):
        """Test MEDIUM qualitative for turn."""
        source = """"test"
turn left medium"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_MEDIUM), abs=0.01)

    def test_large_qualitative_turn(self):
        """Test LARGE qualitative for turn."""
        source = """"test"
turn left strong"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_LARGE), abs=0.01)

    def test_very_large_qualitative_turn(self):
        """Test VERY_LARGE qualitative for turn."""
        source = """"test"
turn left enormous"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(
            math.radians(BODY_YAW_VERY_LARGE), abs=0.01
        )

    def test_qualitative_for_head_translation(self):
        """Test qualitative keywords for head translations (mm)."""
        source = """"test"
head forward little"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose[0, 3] == pytest.approx(
            TRANSLATION_SMALL / 1000.0, abs=0.0001
        )

    def test_maximum_turn_vs_look_pitch(self):
        """Test 'maximum' uses different values for turn vs look up."""
        # Turn
        turn_source = """"test"
turn left maximum"""
        turn_result = compile_script(turn_source)
        assert turn_result.success
        assert turn_result.ir[0].body_yaw == pytest.approx(
            math.radians(BODY_YAW_VERY_LARGE), abs=0.01
        )

        # Look up
        look_source = """"test"
look up maximum"""
        look_result = compile_script(look_source)
        assert look_result.success
        rotation = R.from_matrix(look_result.ir[0].head_pose[:3, :3])
        _, pitch, _ = rotation.as_euler("xyz", degrees=True)
        assert pitch == pytest.approx(-HEAD_PITCH_ROLL_VERY_LARGE, abs=0.1)

    def test_maximum_head_translation(self):
        """Test 'maximum' for head translation uses TRANSLATION_VERY_LARGE."""
        source = """"test"
head forward maximum"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose[0, 3] == pytest.approx(
            TRANSLATION_VERY_LARGE / 1000.0, abs=0.0001
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
