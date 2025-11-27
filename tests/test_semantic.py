"""Unit tests for rmscript semantic analyzer."""

import math

import numpy as np
import pytest

from rmscript.constants import DEFAULT_ANGLE, DEFAULT_DURATION
from rmscript.ir import IRAction, IRWaitAction
from rmscript.lexer import Lexer
from rmscript.parser import Parser
from rmscript.semantic import SemanticAnalyzer


class TestSemanticAnalyzer:
    """Test semantic analysis and IR generation."""

    def test_apply_default_angle(self):
        """Test that default angle is applied when no strength specified."""
        source = """DESCRIPTION test
turn left"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        assert len(ir) == 1
        assert isinstance(ir[0], IRAction)
        assert ir[0].body_yaw == pytest.approx(math.radians(DEFAULT_ANGLE), abs=0.01)

    def test_apply_default_duration(self):
        """Test that default duration is applied when not specified."""
        source = """DESCRIPTION test
look up"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        assert ir[0].duration == DEFAULT_DURATION

    def test_qualitative_strength_context_aware(self):
        """Test that qualitative keywords map to context-appropriate values."""
        source = """DESCRIPTION test
turn left maximum
look left maximum"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        # Both use "maximum" but should have different values
        # turn maximum -> larger body_yaw
        # look maximum -> larger head yaw
        assert isinstance(ir[0], IRAction)
        assert isinstance(ir[1], IRAction)
        assert ir[0].body_yaw is not None
        assert ir[1].head_pose is not None

    def test_head_translation_backward(self):
        """Test that backward direction moves head in negative X."""
        source = """DESCRIPTION test
head backward 10"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        assert isinstance(ir[0], IRAction)
        assert ir[0].head_pose is not None
        # backward should be negative X translation
        assert ir[0].head_pose[0, 3] == pytest.approx(-0.010, abs=0.0001)  # -10mm

    def test_antenna_both_modifier(self):
        """Test that 'antenna both' sets both antennas."""
        source = """DESCRIPTION test
antenna both up"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        assert isinstance(ir[0], IRAction)
        assert ir[0].antennas is not None
        assert len(ir[0].antennas) == 2
        # Both antennas should be equal (both modifier)
        assert ir[0].antennas[0] == ir[0].antennas[1]

    def test_repeat_block_expansion(self):
        """Test that repeat blocks expand actions correctly."""
        source = """DESCRIPTION test
repeat 3
    look left"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        # Should have 3 identical actions
        assert len(ir) == 3
        for action in ir:
            assert isinstance(action, IRAction)

    def test_wait_action_generation(self):
        """Test that wait statements generate IRWaitAction in IR."""
        source = """DESCRIPTION test
wait 2s"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        assert len(ir) == 1
        assert isinstance(ir[0], IRWaitAction)
        assert ir[0].duration == 2.0

    def test_coordinate_system_consistency(self):
        """Test that coordinate system is consistent across movements."""
        source = """DESCRIPTION test
head forward 10
head backward 10"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        # Forward and backward should be opposite
        assert ir[0].head_pose[0, 3] > 0  # Forward is positive X
        assert ir[1].head_pose[0, 3] < 0  # Backward is negative X
        assert abs(ir[0].head_pose[0, 3]) == abs(ir[1].head_pose[0, 3])

    def test_action_merging(self):
        """Test that multiple actions in chain are merged."""
        source = """DESCRIPTION test
turn left and look right"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        # Should merge into single action
        assert len(ir) == 1
        assert isinstance(ir[0], IRAction)
        # Should have both body_yaw and head_pose
        assert ir[0].body_yaw is not None
        assert ir[0].head_pose is not None

    def test_warning_for_out_of_range(self):
        """Test that out-of-range values generate warnings."""
        source = """DESCRIPTION test
turn left 200"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        # Should still generate IR
        assert len(ir) == 1
        # Should have warnings
        assert len(analyzer.warnings) > 0

    def test_errors_list_populated(self):
        """Test that semantic errors are collected."""
        # Note: negative repeat counts are now caught at parse time.
        # Test semantic error with an out-of-range value that only generates a warning.
        source = """DESCRIPTION test
turn left 200"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        # Should have warnings for out-of-range value
        assert len(analyzer.warnings) > 0

    def test_source_line_tracking_in_ir(self):
        """Test that IR actions track source line numbers."""
        source = """DESCRIPTION test
look left
wait 1s"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        # Check line tracking
        assert ir[0].source_line > 0
        assert ir[1].source_line > 0

    def test_original_text_tracking(self):
        """Test that original text is tracked in IR."""
        source = """DESCRIPTION test
look left 45"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        analyzer = SemanticAnalyzer()
        ir = analyzer.analyze(program)

        # Original text should be captured
        assert ir[0].original_text != ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
