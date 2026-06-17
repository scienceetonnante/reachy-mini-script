"""Integration tests for movement commands (look, body, head, tilt, antenna)."""

import math

import pytest
from scipy.spatial.transform import Rotation as R  # noqa: N817

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
    MAX_HEAD_BODY_YAW_DIFF_DEG,
    MAX_HEAD_PITCH_DEG,
    MAX_HEAD_ROLL_DEG,
    TRANSLATION_SMALL,
    TRANSLATION_VERY_LARGE,
)
from rmscript.ir import IRAction


class TestBasicMovements:
    """Test body/look/center commands."""

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

    def test_body_left_rotates_body_and_head(self):
        """Test that 'body left' rotates both body yaw and head yaw."""
        source = """"test"
body left 50"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.body_yaw == pytest.approx(math.radians(50.0), abs=0.01)

        rotation = R.from_matrix(action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(50.0, abs=0.1)

    def test_body_right_rotates_body_and_head(self):
        """Test that 'body right' rotates both body yaw and head yaw."""
        source = """"test"
body right 30"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.body_yaw == pytest.approx(math.radians(-30.0), abs=0.01)

        rotation = R.from_matrix(action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(-30.0, abs=0.1)

    def test_body_center_resets_body_and_head(self):
        """Test that 'body center' resets both body and head to zero."""
        source = """"test"
body center"""
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
        # LEFT tilt = negative roll (top of head leans to the robot's left)
        assert roll == pytest.approx(-DEFAULT_ANGLE, abs=0.1)

    def test_tilt_right(self):
        """Test 'tilt right' command."""
        source = """"test"
tilt right"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, _, _ = rotation.as_euler("xyz", degrees=True)
        # RIGHT tilt = positive roll (top of head leans to the robot's right)
        assert roll == pytest.approx(DEFAULT_ANGLE, abs=0.1)

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
        # tilt left = negative roll; magnitude clamped to the pitch/roll limit
        assert roll == pytest.approx(-HEAD_PITCH_ROLL_VERY_LARGE, abs=0.1)


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
        assert action.antennas[0] == pytest.approx(math.radians(90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(90), abs=0.01)

    def test_antenna_directional_right(self):
        """Test antenna with 'right' direction."""
        source = """"test"
antenna both right"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(-90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(-90), abs=0.01)

    def test_antenna_directional_down(self):
        """Test antenna with 'down' direction."""
        source = """"test"
antenna both down"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(-180), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(-180), abs=0.01)

    def test_antenna_left_modifier(self):
        """Test 'antenna left left' moves the LEFT antenna (index 1)."""
        source = """"test"
antenna left left"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        # antennas is [right, left]; the left modifier targets index 1
        assert action.antennas[1] == pytest.approx(math.radians(90), abs=0.01)
        # the right antenna is not commanded -> left in place (None)
        assert action.antennas[0] is None

    def test_antenna_right_modifier(self):
        """Test 'antenna right right' moves the RIGHT antenna (index 0)."""
        source = """"test"
antenna right right"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        # antennas is [right, left]; the right modifier targets index 0
        assert action.antennas[0] == pytest.approx(math.radians(-90), abs=0.01)
        # the left antenna is not commanded -> left in place (None)
        assert action.antennas[1] is None

    def test_antenna_clock_numeric(self):
        """Test antenna with numeric clock position."""
        source = """"test"
antenna both 3"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(-90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(-90), abs=0.01)

    def test_antenna_clock_keyword(self):
        """Test antenna with clock keyword (ext/int/high/low)."""
        source = """"test"
antenna both ext"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.antennas[0] == pytest.approx(math.radians(-90), abs=0.01)
        assert action.antennas[1] == pytest.approx(math.radians(-90), abs=0.01)


class TestQualitativeStrengths:
    """Test context-aware qualitative keywords."""

    def test_very_small_qualitative_body(self):
        """Test VERY_SMALL qualitative for body."""
        source = """"test"
body left tiny"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.body_yaw == pytest.approx(math.radians(BODY_YAW_VERY_SMALL), abs=0.01)

    def test_small_qualitative_body(self):
        """Test SMALL qualitative for body."""
        source = """"test"
body left little"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_SMALL), abs=0.01)

    def test_medium_qualitative_body(self):
        """Test MEDIUM qualitative for body."""
        source = """"test"
body left medium"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_MEDIUM), abs=0.01)

    def test_large_qualitative_body(self):
        """Test LARGE qualitative for body."""
        source = """"test"
body left strong"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_LARGE), abs=0.01)

    def test_very_large_qualitative_body(self):
        """Test VERY_LARGE qualitative for body."""
        source = """"test"
body left enormous"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].body_yaw == pytest.approx(math.radians(BODY_YAW_VERY_LARGE), abs=0.01)

    def test_qualitative_for_head_translation(self):
        """Test qualitative keywords for head translations (mm)."""
        source = """"test"
head forward little"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].head_pose[0, 3] == pytest.approx(TRANSLATION_SMALL / 1000.0, abs=0.0001)

    def test_maximum_body_vs_look_pitch(self):
        """Test 'maximum' uses different values for body vs look up."""
        # Body
        body_source = """"test"
body left maximum"""
        body_result = compile_script(body_source)
        assert body_result.success
        assert body_result.ir[0].body_yaw == pytest.approx(
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


class TestRotationLimitsClamped:
    """Out-of-range rotations are clamped to mechanical limits (not compensated)."""

    def test_look_yaw_clamped_to_differential_limit(self):
        """'look right 80' clamps head yaw to the ±65° head/body differential."""
        source = """"test"
look right 80"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        # right = negative yaw, clamped to -65°
        assert yaw == pytest.approx(-MAX_HEAD_BODY_YAW_DIFF_DEG, abs=0.1)
        assert any("clamped" in str(w).lower() for w in result.warnings)

    def test_look_yaw_within_limit_unchanged(self):
        """'look right 45' stays at 45° (within the ±65° limit)."""
        source = """"test"
look right 45"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(-45.0, abs=0.1)

    def test_look_pitch_clamped_to_cone_limit(self):
        """'look up 50' clamps head pitch to the ±40° cone limit."""
        source = """"test"
look up 50"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        _, pitch, _ = rotation.as_euler("xyz", degrees=True)
        # up = negative pitch, clamped to -40°
        assert pitch == pytest.approx(-MAX_HEAD_PITCH_DEG, abs=0.1)

    def test_tilt_roll_clamped_to_cone_limit(self):
        """'tilt right 50' clamps head roll to the ±40° cone limit."""
        source = """"test"
tilt right 50"""
        result = compile_script(source)

        assert result.success
        rotation = R.from_matrix(result.ir[0].head_pose[:3, :3])
        roll, _, _ = rotation.as_euler("xyz", degrees=True)
        # tilt right = positive roll, clamped to +40°
        assert roll == pytest.approx(MAX_HEAD_ROLL_DEG, abs=0.1)


class TestLookRelativeToBody:
    """`look` is head-only and relative to the current body yaw axis."""

    def test_look_alone_does_not_move_body(self):
        """'look right 20' on its own leaves the body yaw at 0."""
        source = """"test"
look right 20"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.body_yaw == pytest.approx(0.0, abs=0.01)
        rotation = R.from_matrix(action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(-20.0, abs=0.1)

    def test_look_after_body_composes_in_world_frame(self):
        """'body right 70' then 'look right 20' => head at 90° world, body untouched.

        The look action keeps the body at the turned value (-70°) and its head
        pose is composed into the world frame (-90°), so the head/body
        differential is the intended -20° (20° right of the body axis).
        """
        source = """"test"
body right 70
look right 20"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 2

        body_action, look_action = result.ir[0], result.ir[1]
        # body motor reaches -70° on the body move and stays there during the look
        assert body_action.body_yaw == pytest.approx(math.radians(-70.0), abs=0.01)
        assert look_action.body_yaw == pytest.approx(math.radians(-70.0), abs=0.01)

        # head pose of the look is world-frame -90°
        rotation = R.from_matrix(look_action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(-90.0, abs=0.1)

        # => realized head/body differential is the intended -20°
        differential = yaw - math.degrees(look_action.body_yaw)
        assert differential == pytest.approx(-20.0, abs=0.1)

    def test_look_after_body_opposite_direction(self):
        """'body right 70' then 'look left 20' => 50° right in the world frame."""
        source = """"test"
body right 70
look left 20"""
        result = compile_script(source)

        assert result.success
        look_action = result.ir[1]
        rotation = R.from_matrix(look_action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        # world = -70 + 20 = -50
        assert yaw == pytest.approx(-50.0, abs=0.1)
        assert look_action.body_yaw == pytest.approx(math.radians(-70.0), abs=0.01)

    def test_same_line_body_and_look(self):
        """'body right 70 and look right 20' on one line => -90° world, body -70°."""
        source = """"test"
body right 70 and look right 20"""
        result = compile_script(source)

        assert result.success
        action = result.ir[0]
        assert action.body_yaw == pytest.approx(math.radians(-70.0), abs=0.01)
        rotation = R.from_matrix(action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(-90.0, abs=0.1)


class TestBodyKeepsLookOffset:
    """`body` after `look` must keep the head's look offset (regression).

    Mirror of `TestLookRelativeToBody`: a body-only move should rotate the body
    and carry the head's existing look offset with it, not reset the head to the
    body axis.
    """

    def test_body_after_look_keeps_offset(self):
        """'look left 60' then 'body left 30' => head 90° world, offset preserved."""
        source = """"test"
look left 60
body left 30"""
        result = compile_script(source)

        assert result.success
        body_action = result.ir[1]
        assert body_action.body_yaw == pytest.approx(math.radians(30.0), abs=0.01)

        rotation = R.from_matrix(body_action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        # body 30 + retained look 60 => 90° world
        assert yaw == pytest.approx(90.0, abs=0.1)
        # realized head/body differential is still the intended 60°
        assert yaw - math.degrees(body_action.body_yaw) == pytest.approx(60.0, abs=0.1)

    def test_body_after_look_across_wait(self):
        """The original bug report case: offset survives across lines and a wait."""
        source = """"test"
look left 60 and body left 90
wait 1s
body left 10"""
        result = compile_script(source)

        assert result.success
        last = [a for a in result.ir if isinstance(a, IRAction)][-1]
        assert last.body_yaw == pytest.approx(math.radians(10.0), abs=0.01)

        rotation = R.from_matrix(last.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        # body 10 + retained look 60 => 70° world (was wrongly 10° before the fix)
        assert yaw == pytest.approx(70.0, abs=0.1)

    def test_body_center_keeps_look_offset(self):
        """'body center' faces the body forward but keeps the current look."""
        source = """"test"
look left 40
body center"""
        result = compile_script(source)

        assert result.success
        body_action = result.ir[1]
        assert body_action.body_yaw == pytest.approx(0.0, abs=0.01)
        rotation = R.from_matrix(body_action.head_pose[:3, :3])
        _, _, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(40.0, abs=0.1)

    def test_body_rotates_head_translation_offset(self):
        """A `head` translation offset is carried through a later `body` rotation."""
        source = """"test"
head forward 10
body left 90"""
        result = compile_script(source)

        assert result.success
        body_action = result.ir[1]
        # forward (+x, body frame) rotated 90° left maps to +y in the world frame
        assert body_action.head_pose[0, 3] == pytest.approx(0.0, abs=1e-4)
        assert body_action.head_pose[1, 3] == pytest.approx(0.010, abs=1e-4)

    def test_look_after_look_stays_absolute(self):
        """Head commands remain absolute per line (minimal-scope guard).

        `look up` after `look left` rebuilds the head from neutral, so the prior
        yaw is not retained (only `body` preserves the offset).
        """
        source = """"test"
look left 60
look up 30"""
        result = compile_script(source)

        assert result.success
        second = result.ir[1]
        rotation = R.from_matrix(second.head_pose[:3, :3])
        _, pitch, yaw = rotation.as_euler("xyz", degrees=True)
        assert yaw == pytest.approx(0.0, abs=0.1)
        assert pitch == pytest.approx(-30.0, abs=0.1)


class TestReset:
    """Test the 'reset' keyword (neutral base pose on all DOFs)."""

    def test_reset_produces_neutral_pose(self):
        """'reset' should zero body yaw, head orientation, and raise antennas up."""
        source = """"test"
body left 90
look right 30
tilt left 20
antenna both down
reset"""
        result = compile_script(source)

        assert result.success

        # The last IR action is the expanded reset.
        action = result.ir[-1]

        # Body yaw back to zero.
        assert action.body_yaw == pytest.approx(0.0, abs=0.01)

        # Head orientation back to identity (no yaw/pitch/roll, no translation).
        rotation = R.from_matrix(action.head_pose[:3, :3])
        roll, pitch, yaw = rotation.as_euler("xyz", degrees=True)
        assert roll == pytest.approx(0.0, abs=0.1)
        assert pitch == pytest.approx(0.0, abs=0.1)
        assert yaw == pytest.approx(0.0, abs=0.1)
        assert action.head_pose[:3, 3] == pytest.approx([0.0, 0.0, 0.0], abs=1e-4)

        # Both antennas raised "up" (clock 0 => 0°).
        assert action.antennas is not None
        assert action.antennas[0] == pytest.approx(0.0, abs=1e-6)
        assert action.antennas[1] == pytest.approx(0.0, abs=1e-6)

    def test_reset_is_single_merged_action(self):
        """'reset' expands to one simultaneous IR action, not four."""
        source = """"test"
reset"""
        result = compile_script(source)

        assert result.success
        action_count = sum(1 for a in result.ir if isinstance(a, IRAction))
        assert action_count == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
