from datetime import UTC, datetime

import pytest

from aegismcp.kernel.context import AegisContext, create_anonymous_context
from aegismcp.workflow.decorator import WorkflowRegistry
from aegismcp.workflow.engine import Step, WorkflowEngine, WorkflowError


def test_workflow_decorator():
    reg = WorkflowRegistry()
    
    @reg.workflow("my_wf")
    async def my_wf(): return 1
        
    assert "my_wf" in reg.workflows
    
    @reg.workflow()
    async def auto_name(): return 2
        
    assert "auto_name" in reg.workflows


class MockStep(Step):
    def __init__(self, name: str, should_fail: bool = False):
        self.name = name
        self.executed = False
        self.compensated = False
        self.should_fail = should_fail
        
    async def execute(self, *args, ctx: AegisContext, **kwargs):
        if self.should_fail:
            raise ValueError(f"Step {self.name} failed")
        self.executed = True
        return self.name
        
    async def compensate(self, *args, ctx: AegisContext, **kwargs):
        self.compensated = True

@pytest.mark.asyncio
async def test_workflow_saga_success():
    ctx = create_anonymous_context("r1", "t1", "s1", datetime.now(UTC))
    engine = WorkflowEngine()
    
    step1 = MockStep("step1")
    step2 = MockStep("step2")
    
    from typing import Any
    steps: list[tuple[Step, tuple[Any, ...], dict[str, Any]]] = [
        (step1, (), {}),
        (step2, (), {})
    ]
    
    results = await engine.execute_saga(steps, ctx)
    
    assert results == ["step1", "step2"]
    assert step1.executed
    assert step2.executed
    assert not step1.compensated
    assert not step2.compensated

@pytest.mark.asyncio
async def test_workflow_saga_compensation():
    ctx = create_anonymous_context("r1", "t1", "s1", datetime.now(UTC))
    engine = WorkflowEngine()
    
    step1 = MockStep("step1")
    step2 = MockStep("step2", should_fail=True)
    step3 = MockStep("step3")
    
    steps: list[tuple[Step, tuple[Any, ...], dict[str, Any]]] = [
        (step1, (), {}),
        (step2, (), {}),
        (step3, (), {})
    ]
    
    with pytest.raises(WorkflowError) as exc:
        await engine.execute_saga(steps, ctx)
        
    assert "Saga execution failed" in str(exc.value)
    
    assert step1.executed
    assert not step2.executed
    assert not step3.executed
    
    assert step1.compensated
    assert not step2.compensated
    assert not step3.compensated
