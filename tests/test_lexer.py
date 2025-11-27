"""Unit tests for rmscript lexer (tokenization)."""

import pytest

from rmscript.lexer import Lexer, TokenType


@pytest.fixture
def lexer():
    """Reusable lexer factory."""
    return lambda src: Lexer(src)


class TestLexer:
    """Test tokenization."""

    def test_tokenize_keywords(self, lexer):
        """Test that all movement keywords are recognized."""
        source = "turn look head tilt antenna wait picture play loop repeat end"
        tokens = lexer(source).tokenize()

        expected_types = [
            TokenType.KEYWORD_TURN,
            TokenType.KEYWORD_LOOK,
            TokenType.KEYWORD_HEAD,
            TokenType.KEYWORD_TILT,
            TokenType.KEYWORD_ANTENNA,
            TokenType.KEYWORD_WAIT,
            TokenType.KEYWORD_PICTURE,
            TokenType.KEYWORD_PLAY,
            TokenType.KEYWORD_LOOP,
            TokenType.KEYWORD_REPEAT,
            TokenType.KEYWORD_END,
            TokenType.EOF,
        ]

        assert len(tokens) == len(expected_types)
        for token, expected_type in zip(tokens, expected_types):
            assert token.type == expected_type

    def test_tokenize_numbers(self, lexer):
        """Test that numbers are tokenized correctly."""
        source = "30 2.5 10"
        tokens = lexer(source).tokenize()

        assert tokens[0].type == TokenType.NUMBER
        assert tokens[0].value == "30"
        assert tokens[1].type == TokenType.NUMBER
        assert tokens[1].value == "2.5"
        assert tokens[2].type == TokenType.NUMBER
        assert tokens[2].value == "10"

    def test_tokenize_durations(self, lexer):
        """Test that duration values with 's' suffix are recognized."""
        source = "1s 2.5s 10s"
        tokens = lexer(source).tokenize()

        assert tokens[0].type == TokenType.DURATION
        assert tokens[0].value == "1s"
        assert tokens[1].type == TokenType.DURATION
        assert tokens[1].value == "2.5s"
        assert tokens[2].type == TokenType.DURATION
        assert tokens[2].value == "10s"

    def test_tokenize_directions(self, lexer):
        """Test that direction keywords are recognized."""
        source = "left right up down center back backward backwards"
        tokens = lexer(source).tokenize()

        for i in range(8):  # All 8 directions plus EOF
            if i < 8:
                assert tokens[i].type == TokenType.DIRECTION
                assert tokens[i].value in [
                    "left",
                    "right",
                    "up",
                    "down",
                    "center",
                    "back",
                    "backward",
                    "backwards",
                ]

    def test_tokenize_duration_keywords(self, lexer):
        """Test that duration keywords are recognized."""
        source = "fast slow slowly superfast superslow"
        tokens = lexer(source).tokenize()

        assert tokens[0].type == TokenType.DURATION_KEYWORD
        assert tokens[0].value == "fast"
        assert tokens[1].type == TokenType.DURATION_KEYWORD
        assert tokens[1].value == "slow"
        assert tokens[2].type == TokenType.DURATION_KEYWORD
        assert tokens[2].value == "slowly"

    def test_tokenize_indentation(self, lexer):
        """Test that indentation generates INDENT/DEDENT tokens."""
        source = """repeat 3
    look left
    look right
turn center"""
        tokens = lexer(source).tokenize()

        # Find INDENT and DEDENT tokens
        indent_tokens = [t for t in tokens if t.type == TokenType.INDENT]
        dedent_tokens = [t for t in tokens if t.type == TokenType.DEDENT]

        assert len(indent_tokens) == 1
        assert len(dedent_tokens) == 1

    def test_tokenize_comments(self, lexer):
        """Test that comments are ignored."""
        source = """# This is a comment
look left  # inline comment
# Another comment
look right"""
        tokens = lexer(source).tokenize()

        # Should only have look keywords, directions, newlines, and EOF
        look_tokens = [t for t in tokens if t.type == TokenType.KEYWORD_LOOK]
        assert len(look_tokens) == 2

    def test_tokenize_error_unexpected_character(self, lexer):
        """Test that unexpected characters raise an error."""
        source = "look left @ right"

        with pytest.raises(SyntaxError) as excinfo:
            lexer(source).tokenize()

        assert "Unexpected character" in str(excinfo.value)

    def test_case_insensitive_keywords(self, lexer):
        """Test that keywords are case-insensitive."""
        source = "LOOK Look loOk TURN Turn ANTENNA Antenna"
        tokens = lexer(source).tokenize()

        # All should be recognized as keywords
        keyword_tokens = [
            t
            for t in tokens
            if t.type
            in (TokenType.KEYWORD_LOOK, TokenType.KEYWORD_TURN, TokenType.KEYWORD_ANTENNA)
        ]
        assert len(keyword_tokens) == 7

    def test_tokenize_qualitative_keywords(self, lexer):
        """Test that qualitative strength keywords are recognized."""
        source = "little medium large tiny enormous"
        tokens = lexer(source).tokenize()

        # All should be qualitative tokens
        for i in range(5):
            assert tokens[i].type == TokenType.QUALITATIVE

    def test_tokenize_sound_blocking_keywords(self, lexer):
        """Test that sound blocking keywords are recognized."""
        source = "pause fully wait block complete"
        tokens = lexer(source).tokenize()

        # Some might be keywords (wait), others sound_blocking
        wait_token = [t for t in tokens if t.type == TokenType.KEYWORD_WAIT]
        blocking_tokens = [t for t in tokens if t.type == TokenType.SOUND_BLOCKING]

        assert len(wait_token) == 1  # 'wait' is a keyword
        assert len(blocking_tokens) == 4  # Others are blocking modifiers

    def test_tokenize_antenna_clock_keywords(self, lexer):
        """Test antenna clock position keywords."""
        source = "high low ext int"
        tokens = lexer(source).tokenize()

        for i in range(4):
            assert tokens[i].type == TokenType.ANTENNA_CLOCK

    def test_tokenize_line_tracking(self, lexer):
        """Test that tokens track line numbers."""
        source = """look left
wait 1s
look right"""
        tokens = lexer(source).tokenize()

        # Find the three keywords
        keywords = [
            t
            for t in tokens
            if t.type in (TokenType.KEYWORD_LOOK, TokenType.KEYWORD_WAIT)
        ]

        assert keywords[0].line == 1  # look
        assert keywords[1].line == 2  # wait
        assert keywords[2].line == 3  # look

    def test_tokenize_column_tracking(self, lexer):
        """Test that tokens track column positions."""
        source = "look left"
        tokens = lexer(source).tokenize()

        assert tokens[0].column == 1  # 'look' starts at column 1
        assert tokens[1].column == 6  # 'left' starts at column 6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
