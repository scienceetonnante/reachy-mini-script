"""Tests for rmscript adapter protocol and execution context."""

from dataclasses import dataclass
from typing import Any, Dict

import pytest

from rmscript import ExecutionContext, compile_script
from rmscript.ir import IRAction, IRWaitAction, IRPictureAction
from rmscript.types import IRList


class TestExecutionContext:
    """Test ExecutionContext dataclass."""

    def test_execution_context_creation(self):
        """Test creating basic execution context."""
        context = ExecutionContext(
            script_name="test_script", script_description="Test description"
        )

        assert context.script_name == "test_script"
        assert context.script_description == "Test description"
        assert context.source_file_path is None

    def test_execution_context_with_file_path(self):
        """Test ExecutionContext with source file path."""
        context = ExecutionContext(
            script_name="test",
            script_description="desc",
            source_file_path="/path/to/script.rmscript",
        )

        assert context.source_file_path == "/path/to/script.rmscript"

    def test_extended_execution_context(self):
        """Test extending ExecutionContext with custom fields."""

        @dataclass
        class RobotContext(ExecutionContext):
            robot: Any = None
            verbose: bool = False

        context = RobotContext(
            script_name="test",
            script_description="desc",
            robot="mock_robot",
            verbose=True,
        )

        assert context.script_name == "test"
        assert context.robot == "mock_robot"
        assert context.verbose is True

    def test_execution_context_immutability(self):
        """Test ExecutionContext fields can be accessed."""
        context = ExecutionContext(script_name="test", script_description="desc")

        # Should be able to read fields
        assert context.script_name == "test"
        assert context.script_description == "desc"


class TestAdapterProtocol:
    """Test adapter protocol implementation."""

    def test_adapter_protocol_signature(self):
        """Test adapter implements correct protocol signature."""

        class MockAdapter:
            def execute(self, ir: IRList, context: ExecutionContext) -> Dict[str, Any]:
                return {"success": True, "actions": len(ir)}

        adapter = MockAdapter()
        result = adapter.execute([], ExecutionContext("test", "desc"))

        assert result["success"]
        assert result["actions"] == 0

    def test_adapter_with_real_ir(self):
        """Test adapter with real IR from compilation."""

        class CountingAdapter:
            def execute(self, ir: IRList, context: ExecutionContext) -> Dict[str, Any]:
                counts = {
                    "movements": 0,
                    "waits": 0,
                    "pictures": 0,
                }

                for action in ir:
                    if isinstance(action, IRAction):
                        counts["movements"] += 1
                    elif isinstance(action, IRWaitAction):
                        counts["waits"] += 1
                    elif isinstance(action, IRPictureAction):
                        counts["pictures"] += 1

                return counts

        # Compile a script
        source = """"test"
look left
wait 1s
picture"""
        result = compile_script(source)
        assert result.success

        # Execute with adapter
        adapter = CountingAdapter()
        context = ExecutionContext(
            script_name=result.name, script_description=result.description
        )
        counts = adapter.execute(result.ir, context)

        assert counts["movements"] == 1
        assert counts["waits"] == 1
        assert counts["pictures"] == 1

    def test_adapter_receives_context_metadata(self):
        """Test adapter receives script metadata through context."""

        class MetadataCapturingAdapter:
            def execute(self, ir: IRList, context: ExecutionContext) -> Dict[str, Any]:
                return {
                    "script_name": context.script_name,
                    "description": context.script_description,
                    "has_file_path": context.source_file_path is not None,
                }

        source = """"Test behavior"
look left"""
        result = compile_script(source)

        adapter = MetadataCapturingAdapter()
        context = ExecutionContext(
            script_name=result.name,
            script_description=result.description,
            source_file_path="/path/to/test.rmscript",
        )

        metadata = adapter.execute(result.ir, context)

        assert metadata["script_name"] == result.name
        assert metadata["description"] == "Test behavior"
        assert metadata["has_file_path"] is True

    def test_adapter_error_handling(self):
        """Test adapter can handle errors gracefully."""

        class ErrorHandlingAdapter:
            def execute(self, ir: IRList, context: ExecutionContext) -> Dict[str, Any]:
                try:
                    # Simulate processing
                    for action in ir:
                        if isinstance(action, IRAction):
                            # Simulate potential error
                            if action.head_pose is None and action.body_yaw is None:
                                raise ValueError("Invalid action")
                    return {"success": True, "errors": []}
                except Exception as e:
                    return {"success": False, "errors": [str(e)]}

        # Valid IR
        source = """"test"
look left"""
        result = compile_script(source)

        adapter = ErrorHandlingAdapter()
        context = ExecutionContext(script_name="test", script_description="desc")
        execution_result = adapter.execute(result.ir, context)

        assert execution_result["success"]
        assert len(execution_result["errors"]) == 0

    def test_adapter_with_custom_context_fields(self):
        """Test adapter using extended context with custom fields."""

        @dataclass
        class CustomContext(ExecutionContext):
            config: Dict[str, Any] = None

        class ConfigurableAdapter:
            def execute(self, ir: IRList, context: CustomContext) -> Dict[str, Any]:
                max_actions = context.config.get("max_actions", float("inf"))
                return {
                    "executed": min(len(ir), max_actions),
                    "config": context.config,
                }

        source = """"test"
look left
look right
look up"""
        result = compile_script(source)

        adapter = ConfigurableAdapter()
        context = CustomContext(
            script_name=result.name,
            script_description=result.description,
            config={"max_actions": 2, "verbose": True},
        )

        execution_result = adapter.execute(result.ir, context)

        assert execution_result["executed"] == 2  # Limited by config
        assert execution_result["config"]["verbose"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
