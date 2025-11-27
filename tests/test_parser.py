"""Unit tests for rmscript parser (AST construction)."""

import pytest

from rmscript.lexer import Lexer
from rmscript.parser import Parser, ParseError


class TestParser:
    """Test AST generation."""

    def test_parse_description(self):
        """Test that DESCRIPTION header is parsed correctly."""
        source = """"This is a test tool"
look left"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert program.description == "This is a test tool"

    def test_parse_action_statement(self):
        """Test that simple action statements are parsed."""
        source = """"test"
look left
turn right"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert len(program.statements) == 2
        assert program.statements[0].actions[0].keyword == "look"
        assert program.statements[0].actions[0].direction == "left"
        assert program.statements[1].actions[0].keyword == "turn"
        assert program.statements[1].actions[0].direction == "right"

    def test_parse_action_with_strength(self):
        """Test that actions with numeric strength are parsed."""
        source = """"test"
turn left 45"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert program.statements[0].actions[0].strength == 45.0

    def test_parse_action_with_duration(self):
        """Test that actions with duration are parsed."""
        source = """"test"
look up 2s"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert program.statements[0].actions[0].duration == 2.0

    def test_parse_compound_action_with_and(self):
        """Test that compound actions with 'and' are parsed."""
        source = """"test"
turn left and look right"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert len(program.statements[0].actions) == 2
        assert program.statements[0].actions[0].keyword == "turn"
        assert program.statements[0].actions[1].keyword == "look"

    def test_parse_repeat_block(self):
        """Test that repeat blocks are parsed."""
        source = """"test"
repeat 3
    look left
    look right"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert len(program.statements) == 1
        repeat_block = program.statements[0]
        assert repeat_block.count == 3
        assert len(repeat_block.body) == 2

    def test_parse_wait_statement(self):
        """Test that wait statements are parsed."""
        source = """"test"
wait 2s"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert program.statements[0].duration == 2.0

    def test_parse_picture_statement(self):
        """Test that picture statements are parsed."""
        source = """"test"
picture"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert len(program.statements) == 1

    def test_parse_play_sound_with_duration(self):
        """Test that play sound with duration is parsed."""
        source = """"test"
play mysound 5s"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert program.statements[0].sound_name == "mysound"
        assert program.statements[0].duration == 5.0
        assert program.statements[0].blocking

    def test_parse_error_and_with_picture(self):
        """Test that 'and picture' produces a parse error."""
        source = """"test"
look left and picture"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        with pytest.raises(ParseError) as excinfo:
            parser.parse()

        assert "cannot combine" in str(excinfo.value).lower()

    def test_parse_antenna_with_modifier(self):
        """Test parsing antenna with left/right/both modifier."""
        source = """"test"
antenna both up"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert program.statements[0].actions[0].antenna_modifier == "both"
        assert program.statements[0].actions[0].direction == "up"

    def test_parse_nested_repeat_blocks(self):
        """Test parsing nested repeat blocks."""
        source = """"test"
repeat 2
    repeat 3
        look left"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert len(program.statements) == 1
        outer_repeat = program.statements[0]
        assert outer_repeat.count == 2
        assert len(outer_repeat.body) == 1
        inner_repeat = outer_repeat.body[0]
        assert inner_repeat.count == 3

    def test_parse_qualitative_strength(self):
        """Test parsing qualitative strength keywords."""
        source = """"test"
turn left little"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert program.statements[0].actions[0].strength_qualitative == "little"

    def test_parse_duration_keyword(self):
        """Test parsing duration keywords like 'fast' or 'slow'."""
        source = """"test"
look left fast"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert program.statements[0].actions[0].duration_keyword == "fast"

    def test_parse_loop_sound(self):
        """Test parsing loop sound command."""
        source = """"test"
loop mysound 10s"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)
        program = parser.parse()

        assert program.statements[0].sound_name == "mysound"
        assert program.statements[0].loop is True
        assert program.statements[0].duration == 10.0

    def test_parse_error_invalid_direction(self):
        """Test parse error for invalid direction."""
        source = """"test"
turn up"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        with pytest.raises(ParseError) as excinfo:
            parser.parse()

        assert "turn" in str(excinfo.value).lower()
        assert "up" in str(excinfo.value).lower()

    def test_parse_error_missing_antenna_modifier(self):
        """Test parse error when antenna missing modifier."""
        source = """"test"
antenna up"""
        lexer = Lexer(source)
        tokens = lexer.tokenize()
        parser = Parser(tokens)

        with pytest.raises(ParseError) as excinfo:
            parser.parse()

        assert "antenna" in str(excinfo.value).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
