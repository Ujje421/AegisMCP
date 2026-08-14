from aegismcp.kernel.ids import generate_request_id, generate_span_id, generate_trace_id


def test_generate_request_id():
    req1 = generate_request_id()
    req2 = generate_request_id()
    assert req1 != req2
    assert isinstance(req1, str)


def test_generate_trace_id():
    t1 = generate_trace_id()
    t2 = generate_trace_id()
    assert t1 != t2
    assert len(t1) == 32


def test_generate_span_id():
    s1 = generate_span_id()
    s2 = generate_span_id()
    assert s1 != s2
    assert len(s1) == 16
