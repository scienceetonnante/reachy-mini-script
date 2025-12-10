"""Tests for high-level compiler API functions."""

import pytest
from pathlib import Path

from rmscript import compile_script, compile_file, verify_script


class TestCompileScript:
    """Test compile_script() function."""

    def test_compile_script_basic(self):
        """Test basic script compilation."""
        source = """"test"
look left"""
        result = compile_script(source)

        assert result.success
        assert result.description == "test"
        assert len(result.ir) == 1

    def test_compile_script_returns_compilation_result(self):
        """Test that compile_script() returns CompilationResult with all fields."""
        source = """"test"
look left"""
        result = compile_script(source)

        assert hasattr(result, "success")
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")
        assert hasattr(result, "ir")
        assert hasattr(result, "name")
        assert hasattr(result, "description")
        assert hasattr(result, "source_code")

    def test_compile_script_preserves_source(self):
        """Test that source code is preserved in result."""
        source = """"test"
look left
wait 1s"""
        result = compile_script(source)

        assert result.source_code == source

    def test_compile_script_with_errors(self):
        """Test compile_script with invalid syntax."""
        source = """"test"
jump up"""
        result = compile_script(source)

        assert not result.success
        assert len(result.errors) > 0

    def test_compile_script_with_warnings(self):
        """Test compile_script with warnings."""
        source = """"test"
turn left 200"""
        result = compile_script(source)

        assert result.success  # Compiles successfully
        assert len(result.warnings) > 0


class TestCompileFile:
    """Test compile_file() function."""

    def test_compile_file_success(self, tmp_path):
        """Test compiling valid rmscript file."""
        script_file = tmp_path / "test.rmscript"
        script_file.write_text('"test"\nlook left')

        result = compile_file(str(script_file))

        assert result.success
        assert result.name == "test"  # Derived from filename
        assert result.source_file_path == str(script_file.resolve())
        assert len(result.ir) == 1

    def test_compile_file_not_found(self):
        """Test error handling for missing file."""
        result = compile_file("nonexistent.rmscript")

        assert not result.success
        assert len(result.errors) > 0
        assert any("not found" in err.message.lower() for err in result.errors)

    def test_compile_file_with_spaces_in_name(self, tmp_path):
        """Test filename with spaces becomes underscore tool name."""
        script_file = tmp_path / "wave hello.rmscript"
        script_file.write_text('"test"\nlook left')

        result = compile_file(str(script_file))

        assert result.success
        assert result.name == "wave_hello"

    def test_compile_file_preserves_path(self, tmp_path):
        """Test that file path is preserved in result."""
        script_file = tmp_path / "mytest.rmscript"
        script_file.write_text('"test"\nlook left')

        result = compile_file(str(script_file))

        assert result.success
        assert result.source_file_path is not None
        assert Path(result.source_file_path).name == "mytest.rmscript"

    def test_compile_file_with_complex_script(self, tmp_path):
        """Test compiling complex script from file."""
        script_content = '''"Complex behavior"
repeat 2
    look left
    wait 0.5s
    look right
    wait 0.5s
antenna both up
picture'''
        script_file = tmp_path / "complex.rmscript"
        script_file.write_text(script_content)

        result = compile_file(str(script_file))

        assert result.success
        assert result.name == "complex"
        assert len(result.ir) > 0

    def test_compile_file_with_errors(self, tmp_path):
        """Test compile_file with syntax errors."""
        script_file = tmp_path / "bad.rmscript"
        script_file.write_text('"test"\njump up')

        result = compile_file(str(script_file))

        assert not result.success
        assert len(result.errors) > 0

    def test_compile_file_preserves_source(self, tmp_path):
        """Test that file contents are preserved in source_code."""
        content = '"test"\nlook left\nwait 1s'
        script_file = tmp_path / "test.rmscript"
        script_file.write_text(content)

        result = compile_file(str(script_file))

        assert result.success
        assert result.source_code == content

    def test_compile_file_special_characters_in_name(self, tmp_path):
        """Test filename with special characters."""
        script_file = tmp_path / "test-behavior_v2.rmscript"
        script_file.write_text('"test"\nlook left')

        result = compile_file(str(script_file))

        assert result.success
        # Should handle special chars in filename
        assert result.name == "test-behavior_v2"


class TestVerifyScript:
    """Test verify_script() convenience function."""

    def test_verify_valid_script(self):
        """Test verify_script returns True for valid script."""
        is_valid, messages = verify_script('"test"\nlook left')

        assert is_valid
        assert len(messages) == 0

    def test_verify_invalid_script(self):
        """Test verify_script returns False and messages for invalid script."""
        is_valid, messages = verify_script('"test"\njump up')

        assert not is_valid
        assert len(messages) > 0
        assert any("jump" in msg.lower() for msg in messages)

    def test_verify_includes_warnings(self):
        """Test verify_script includes warnings in messages."""
        is_valid, messages = verify_script('"test"\nturn left 200')

        assert is_valid  # Still valid despite warning
        assert len(messages) > 0  # Has warnings
        assert any("200" in msg for msg in messages)

    def test_verify_complex_valid_script(self):
        """Test verify_script with complex valid script."""
        script = '''"test"
repeat 3
    look left
    wait 0.5s
    look right
antenna both up
picture'''
        is_valid, messages = verify_script(script)

        assert is_valid
        assert len(messages) == 0

    def test_verify_multiple_errors(self):
        """Test verify_script returns first error (parser stops at first parse error)."""
        script = '''"test"
jump up
fly high
teleport center'''
        is_valid, messages = verify_script(script)

        assert not is_valid
        assert len(messages) >= 1  # At least 1 error (parser stops at first error)

    def test_verify_empty_script(self):
        """Test verify_script with empty script (only description)."""
        is_valid, messages = verify_script('"test"')

        assert is_valid
        assert len(messages) == 0

    def test_verify_syntax_error(self):
        """Test verify_script with syntax error."""
        is_valid, messages = verify_script('"test"\nlook left and picture')

        assert not is_valid
        assert any("cannot combine" in msg.lower() for msg in messages)

    def test_verify_missing_description(self):
        """Test verify_script without description string uses default."""
        is_valid, messages = verify_script("look left\nwait 1s")

        # Description is now optional - should succeed with default
        assert is_valid is True
        assert messages == []

    def test_verify_returns_tuple(self):
        """Test verify_script returns correct tuple structure."""
        is_valid, messages = verify_script('"test"\nlook left')

        assert isinstance(is_valid, bool)
        assert isinstance(messages, list)
        # All messages should be strings
        for msg in messages:
            assert isinstance(msg, str)


class TestCompilerAPIIntegration:
    """Test integration between different API functions."""

    def test_compile_file_then_verify(self, tmp_path):
        """Test compiling file then verifying same content."""
        content = '"test"\nlook left\nwait 1s'
        script_file = tmp_path / "test.rmscript"
        script_file.write_text(content)

        # Compile file
        file_result = compile_file(str(script_file))

        # Verify same content
        is_valid, messages = verify_script(content)

        # Both should succeed
        assert file_result.success
        assert is_valid
        assert len(messages) == 0

    def test_compile_script_and_file_equivalence(self, tmp_path):
        """Test compile_script and compile_file produce equivalent IR."""
        content = '''"test"
look left
antenna both up
wait 1s'''
        script_file = tmp_path / "test.rmscript"
        script_file.write_text(content)

        # Compile both ways
        script_result = compile_script(content)
        file_result = compile_file(str(script_file))

        # Both should succeed
        assert script_result.success
        assert file_result.success

        # IR should have same length
        assert len(script_result.ir) == len(file_result.ir)

        # IR types should match
        for script_action, file_action in zip(script_result.ir, file_result.ir):
            assert type(script_action) == type(file_action)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
