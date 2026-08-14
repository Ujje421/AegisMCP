from aegismcp.tools.decorator import tool


def test_tool_decorator():
    @tool(description="A test tool", timeout=15.0)
    def my_tool(x: int, y: str = "default") -> int:
        return x

    assert hasattr(my_tool, "__aegis_tool__")
    desc = my_tool.__aegis_tool__
    assert desc.name == "my_tool"
    assert desc.description == "A test tool"
    assert desc.timeout_seconds == 15.0
    
    schema = desc.input_schema
    assert schema["type"] == "object"
    assert "x" in schema["properties"]
    assert "x" in schema["required"]
    assert "y" not in schema["required"]
