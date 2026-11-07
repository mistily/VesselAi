from agents.registry import parse_agent_request, resolve_agent_name


def test_parse_agent_request_accepts_short_and_multiword_roles():
    assert parse_agent_request("developer: suggest tests") == ("Developer Copilot", "suggest tests")
    assert parse_agent_request("agent requirements analyst: define acceptance criteria") == (
        "Requirements Analyst", "define acceptance criteria"
    )
    assert parse_agent_request("@qa - review these notes") == ("QA & Reviewer", "review these notes")


def test_agent_role_resolution_is_explicit_and_case_insensitive():
    assert resolve_agent_name("OPS") == "Operations Agent"
    assert resolve_agent_name("unknown role") is None
    assert parse_agent_request("hello, can you help?") is None
