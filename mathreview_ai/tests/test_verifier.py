from core.verifier import safe_numeric_eval, verify_steps


def test_safe_arithmetic():
    assert str(safe_numeric_eval("12 * 15")) == "180"
    assert str(safe_numeric_eval("450 * 20 / 100")) == "90"


def test_rejects_unsafe_expression():
    try:
        safe_numeric_eval("__import__('os').system('echo unsafe')")
    except Exception:
        pass
    else:
        raise AssertionError("Unsafe expression should be rejected")


def test_verification_and_dependency():
    steps = [
        {"step_id": 1, "expression": "12 * 15", "claimed_result": "170"},
        {"step_id": 2, "expression": "170 + 20", "claimed_result": "190"},
    ]
    result = verify_steps(steps)
    assert result[0]["status"] == "error"
    assert result[1]["status"] == "correct"
    assert result[1]["depends_on_earlier_error"] is True
