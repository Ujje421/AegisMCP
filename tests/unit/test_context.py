from datetime import UTC, datetime, timedelta

from aegismcp.kernel.context import create_anonymous_context


def test_context_deadline_tightening():
    now = datetime.now(UTC)
    original_deadline = now + timedelta(seconds=10)
    ctx = create_anonymous_context("req1", "trace1", "span1", original_deadline)

    tighter_deadline = now + timedelta(seconds=5)
    new_ctx = ctx.with_deadline(tighter_deadline)

    assert new_ctx.deadline == tighter_deadline
    assert new_ctx is not ctx


def test_context_deadline_cannot_be_extended():
    now = datetime.now(UTC)
    original_deadline = now + timedelta(seconds=10)
    ctx = create_anonymous_context("req1", "trace1", "span1", original_deadline)

    looser_deadline = now + timedelta(seconds=20)
    new_ctx = ctx.with_deadline(looser_deadline)

    assert new_ctx.deadline == original_deadline
    assert new_ctx is ctx


def test_with_span():
    now = datetime.now(UTC)
    ctx = create_anonymous_context("req1", "trace1", "span1", now)

    new_ctx = ctx.with_span("span2")
    assert new_ctx.span_id == "span2"
    assert new_ctx.trace_id == "trace1"


def test_with_metadata():
    now = datetime.now(UTC)
    ctx = create_anonymous_context("req1", "trace1", "span1", now)
    ctx = ctx.with_metadata({"k1": "v1"})

    new_ctx = ctx.with_metadata({"k2": "v2", "k1": "v1_new"})
    assert new_ctx.metadata == {"k1": "v1_new", "k2": "v2"}
