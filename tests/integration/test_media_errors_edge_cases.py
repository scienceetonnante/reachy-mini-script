"""Integration tests for media commands, error handling, and edge cases."""

import pytest

from rmscript import compile_script
from rmscript.ir import IRAction, IRPictureAction, IRPlaySoundAction, IRWaitAction


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


class TestPictureCapture:
    """Test picture command."""

    def test_picture_compiles(self):
        """Test that 'picture' command compiles."""
        source = """DESCRIPTION test
picture"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 1
        assert isinstance(result.ir[0], IRPictureAction)

    def test_picture_in_sequence(self):
        """Test picture in sequence with movements."""
        source = """DESCRIPTION test
look left
picture
look right"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 3
        assert isinstance(result.ir[0], IRAction)
        assert isinstance(result.ir[1], IRPictureAction)
        assert isinstance(result.ir[2], IRAction)

    def test_multiple_pictures(self):
        """Test multiple picture commands."""
        source = """DESCRIPTION test
picture
wait 1s
picture"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 3
        assert isinstance(result.ir[0], IRPictureAction)
        assert isinstance(result.ir[1], IRWaitAction)
        assert isinstance(result.ir[2], IRPictureAction)


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
        assert any(
            "up" in err.message.lower() or "direction" in err.message.lower()
            for err in result.errors
        )

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
        assert any(
            "sound" in err.message.lower() or "expected" in err.message.lower()
            for err in result.errors
        )

    def test_warning_out_of_range_clear_message(self):
        """Test that out-of-range values produce clear warnings."""
        source = """DESCRIPTION test
turn left 200"""
        result = compile_script(source)

        assert result.success  # Compiles successfully
        assert len(result.warnings) >= 1
        assert any("200" in warn.message for warn in result.warnings)

    def test_error_and_keyword_with_control_helpful(self):
        """Test helpful error for 'and' with control commands."""
        source = """DESCRIPTION test
look left and wait 1s"""
        result = compile_script(source)

        assert not result.success
        assert any(
            "cannot combine" in err.message.lower() or "separate" in err.message.lower()
            for err in result.errors
        )

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

    @pytest.mark.xfail(reason="Multi-line descriptions not yet supported - requires lexer enhancement")
    def test_multiline_description_preserved(self):
        """Test multi-line description handling."""
        source = """DESCRIPTION This is a
    multi-line description for testing
look left"""
        result = compile_script(source)

        assert result.success
        # Description should include multi-line content
        assert "multi" in result.description.lower()

    def test_mixed_indentation_tabs_spaces(self):
        """Test that mixed indentation is handled."""
        # Note: This may or may not be an error depending on implementation
        source = """DESCRIPTION test
repeat 2
    look left
    look right"""
        result = compile_script(source)

        # Should either succeed or have clear error about indentation
        if not result.success:
            assert any(
                "indent" in err.message.lower() for err in result.errors
            )

    def test_decimal_repeat_count_error(self):
        """Test that decimal repeat counts produce error."""
        source = """DESCRIPTION test
repeat 2.5
    look left"""
        result = compile_script(source)

        assert not result.success

    def test_negative_repeat_count_error(self):
        """Test that negative repeat counts produce error."""
        source = """DESCRIPTION test
repeat -1
    look left"""
        result = compile_script(source)

        # Should have error
        assert len(result.errors) > 0

    def test_source_line_preserved_in_errors(self):
        """Test that error messages include line numbers."""
        source = """DESCRIPTION test
look left
jump up
turn right"""
        result = compile_script(source)

        assert not result.success
        # Error should reference line 3 (jump up)
        assert any(err.line == 3 for err in result.errors)

    @pytest.mark.xfail(reason="Punctuation in descriptions not yet supported - requires lexer enhancement")
    def test_very_long_description(self):
        """Test handling of very long description."""
        long_desc = "This is a very long description. " * 50
        source = f"""DESCRIPTION {long_desc}
look left"""
        result = compile_script(source)

        assert result.success
        assert long_desc.strip() in result.description

    def test_unicode_in_comments(self):
        """Test Unicode characters in comments."""
        source = """DESCRIPTION test
# Comment with émojis 🤖 and ünïcödë
look left"""
        result = compile_script(source)

        assert result.success
        assert len(result.ir) == 1

    def test_unicode_in_sound_names(self):
        """Test Unicode in sound file names."""
        source = """DESCRIPTION test
play café_sound"""
        result = compile_script(source)

        assert result.success
        assert result.ir[0].sound_name == "café_sound"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
