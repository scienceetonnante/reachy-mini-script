# Test Organization

This document describes the test suite structure for rmscript.

## Test Statistics

- **Total Tests:** 185+
- **Unit Tests:** 89
- **Integration Tests:** 91
- **API Tests:** 5+

## Directory Structure

```
tests/
├── __init__.py                    # Test package
│
├── Unit Tests (by compiler layer)
├── test_lexer.py                  # 14 tests - Tokenization
├── test_parser.py                 # 18 tests - AST construction
├── test_semantic.py               # 13 tests - Semantic analysis & IR generation
├── test_optimizer.py              # 11 tests - IR optimization
│
├── API Tests
├── test_compiler_api.py           # 24 tests - compile_script, compile_file, verify_script
├── test_types.py                  # 5 tests - Type definitions (IRActionType, IRList)
├── test_adapters.py               # 9 tests - Adapter protocol & ExecutionContext
│
└── integration/                   # Integration tests
    ├── __init__.py
    ├── test_movements.py          # 34 tests - Movement commands (look, turn, head, tilt, antenna)
    ├── test_control_flow.py       # 26 tests - Repeat, wait, and, duration, case insensitivity
    └── test_media_errors_edge_cases.py  # 31 tests - Picture, sound, errors, edge cases

```

## Test Coverage by Feature

### Compiler Pipeline (Unit Tests)

**Lexer (14 tests)**
- ✅ Keyword recognition (all movement and control keywords)
- ✅ Number and duration tokenization
- ✅ Direction keywords
- ✅ Duration keywords (fast, slow, etc.)
- ✅ Indentation tracking (INDENT/DEDENT)
- ✅ Comment handling
- ✅ Case insensitivity
- ✅ Qualitative keywords
- ✅ Sound blocking keywords
- ✅ Antenna clock keywords
- ✅ Line and column tracking
- ✅ Error handling (unexpected characters)

**Parser (18 tests)**
- ✅ DESCRIPTION header parsing
- ✅ Simple action statements
- ✅ Actions with strength/duration
- ✅ Compound actions with 'and'
- ✅ Repeat blocks (including nested)
- ✅ Wait statements
- ✅ Picture statements
- ✅ Play/loop sound commands
- ✅ Antenna with modifiers
- ✅ Qualitative strength
- ✅ Duration keywords
- ✅ Multi-line descriptions
- ✅ Error handling (invalid directions, missing parameters)

**Semantic Analyzer (13 tests)**
- ✅ Default value application (angles, durations)
- ✅ Context-aware qualitative strengths
- ✅ Head translation (coordinate system)
- ✅ Antenna control (both modifier)
- ✅ Repeat block expansion
- ✅ Wait action generation
- ✅ Coordinate system consistency
- ✅ Action merging
- ✅ Warning generation (out of range)
- ✅ Error collection
- ✅ Source line tracking
- ✅ Original text tracking

**Optimizer (11 tests)**
- ✅ Consecutive wait merging
- ✅ No-op action removal
- ✅ Non-mergeable action preservation
- ✅ Picture and sound action preservation
- ✅ Empty IR handling
- ✅ Single action pass-through
- ✅ Waits not merged across movements
- ✅ Mixed no-op and wait handling
- ✅ Metadata preservation
- ✅ Action order preservation
- ✅ Zero-duration wait merging

### API (29 tests)

**Compiler API (24 tests)**
- ✅ compile_script() basic functionality
- ✅ CompilationResult structure
- ✅ Source code preservation
- ✅ Error handling
- ✅ Warning handling
- ✅ compile_file() from disk
- ✅ File not found handling
- ✅ Filename to tool name conversion
- ✅ Spaces in filenames
- ✅ Path preservation
- ✅ Complex script compilation
- ✅ verify_script() valid scripts
- ✅ verify_script() invalid scripts
- ✅ verify_script() with warnings
- ✅ Multiple errors handling
- ✅ Empty script handling
- ✅ API integration tests

**Types (5 tests)**
- ✅ IRActionType union type
- ✅ IRList type alias
- ✅ Empty IR list
- ✅ Homogeneous lists
- ✅ Mixed type lists

**Adapters (9 tests)**
- ✅ ExecutionContext creation
- ✅ ExecutionContext with file path
- ✅ Extended ExecutionContext
- ✅ Adapter protocol signature
- ✅ Adapter with real IR
- ✅ Context metadata passing
- ✅ Error handling in adapters
- ✅ Custom context fields

### Integration Tests (91 tests)

**Movements (34 tests)**
- ✅ Look commands (left, right, up, down, center)
- ✅ Turn commands (body + head rotation)
- ✅ Head translation (forward, back, left, right, up, down)
- ✅ Backward synonyms (back, backward, backwards)
- ✅ Tilt commands (roll)
- ✅ Antenna control (directional, clock, modifiers)
- ✅ Context-aware qualitative strengths (tiny → maximum)
- ✅ Qualitative for different movement types

**Control Flow (26 tests)**
- ✅ Compound movements with 'and'
- ✅ Error: 'and' with picture/play/loop/wait
- ✅ Duration control (default, explicit, decimal)
- ✅ Duration keywords (fast, slow, slowly)
- ✅ Wait requires 's' suffix
- ✅ Basic repeat blocks
- ✅ Nested repeat blocks (2 and 3 levels deep)
- ✅ Repeat execution order
- ✅ **NEW:** Case insensitivity comprehensive tests
- ✅ **NEW:** Case-sensitive sound names
- ✅ **NEW:** Interpolation mode tests

**Media, Errors, Edge Cases (31 tests)**
- ✅ Sound playback (async, blocking, duration)
- ✅ Loop sound
- ✅ Picture capture (single, multiple, in sequence)
- ✅ Error messages (invalid keywords, directions, parameters)
- ✅ Warnings (out of range)
- ✅ Edge cases (empty programs, comments, blank lines)
- ✅ Zero duration waits
- ✅ Large repeat counts
- ✅ **NEW:** Multi-line descriptions
- ✅ **NEW:** Decimal/negative repeat counts (errors)
- ✅ **NEW:** Source line in errors
- ✅ **NEW:** Unicode handling

## New Tests Added (76 total)

### High Priority (Completed)
1. ✅ compile_file() tests (8 tests)
2. ✅ verify_script() tests (9 tests)
3. ✅ Nested repeat blocks (3 tests)
4. ✅ test_types.py module (5 tests)
5. ✅ test_adapters.py module (9 tests)

### Medium Priority (Completed)
6. ✅ Case insensitivity comprehensive (7 tests)
7. ✅ Source line tracking (2 tests)
8. ✅ Interpolation mode (3 tests)
9. ✅ Optimizer edge cases (3 tests)
10. ✅ Multi-line descriptions (2 tests)
11. ✅ Unicode handling (2 tests)
12. ✅ Additional lexer tests (4 tests)
13. ✅ Additional parser tests (7 tests)
14. ✅ Additional semantic tests (4 tests)
15. ✅ Edge case tests (8 tests)

## Running Tests

### Run all tests
```bash
pytest tests/
```

### Run only unit tests
```bash
pytest tests/test_*.py
```

### Run only integration tests
```bash
pytest tests/integration/
```

### Run specific test file
```bash
pytest tests/test_lexer.py -v
```

### Run with coverage
```bash
pytest tests/ --cov=rmscript --cov-report=html
```

## Test Principles

1. **Unit tests** test individual compiler stages in isolation
2. **Integration tests** test end-to-end compilation of language features
3. **API tests** test public API functions and types
4. **Clear naming** - test names describe what they test
5. **Focused tests** - one concept per test
6. **Good coverage** - all features, errors, and edge cases tested

## Maintenance

- When adding new language features, add tests to appropriate integration test file
- When modifying compiler stages, update corresponding unit test file
- When adding new API functions, add tests to test_compiler_api.py
- Keep test files under ~400 lines when possible
