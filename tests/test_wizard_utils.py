import pytest

from wizard_utils import join_human, md_line, is_meaningful


def test_join_human_empty_and_none():
    assert join_human([]) == "TBD"
    assert join_human(None) == "TBD"
    assert join_human(["", None, False]) == "TBD"


def test_join_human_single_and_multi():
    assert join_human(["CLI"]) == "CLI"
    assert join_human(["CLI", "API"]) == "CLI and API"
    assert join_human(["CLI", "GUI", "API"]) == "CLI, GUI and API"


def test_md_line():
    assert md_line("Something") == "- Something"
    assert md_line("") == ""
    assert md_line(None) == ""


def test_is_meaningful_filters_placeholders_and_tbd():
    assert not is_meaningful("")
    assert not is_meaningful("   ")
    assert not is_meaningful("TBD")
    assert not is_meaningful("No additional gating logic beyond the defined go/no-go criteria.")
    assert not is_meaningful("This solution will not employ a distinct orchestration layer.")

    assert is_meaningful("Users will interact with the solution via CLI and API.")


def test_sentence_examples_like_wizard_usage():
    # Simulate how 03_Solution_Wizard builds sentences
    users = ["Network Engineers", "Operations"]
    interactions = ["CLI", "Web GUI", "API"]
    tools = ["Python", "REST API"]
    auth = ["OAuth2", "API Token"]

    users_sentence = f"This solution targets {join_human(users)}."
    interaction_sentence = f"Users will interact with the solution via {join_human(interactions)}."
    tools_sentence = f"The presentation layer will be built using {join_human(tools)}."
    auth_sentence = f"Presentation authentication will use {join_human(auth)}."

    # Basic checks
    for s in [users_sentence, interaction_sentence, tools_sentence, auth_sentence]:
        assert s.endswith(".")
        assert is_meaningful(s)
        assert md_line(s).startswith("- ")
