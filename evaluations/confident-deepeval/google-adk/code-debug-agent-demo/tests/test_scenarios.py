from google_adk_deepeval_run.paths import DEFAULT_SCENARIO_DIR
from google_adk_deepeval_run.utils.scenarios import (
    ConversationTurn,
    collect_turn_expectations,
    list_scenario_files,
    load_scenarios_from_file,
)


def test_list_scenario_files_finds_samples():
    files = list_scenario_files(DEFAULT_SCENARIO_DIR)
    assert files, "Expected bundled scenario files to be discoverable"
    assert files[0].scenario_count >= 1


def test_collect_expectations_deduplicates_entries():
    turns = [
        ConversationTurn(
            user_input="first",
            expected_tools=["search_stack_exchange_for_error"],
            expected_keywords=["pandas"],
            expected_links=["https://stackoverflow.com/q/1"],
        ),
        ConversationTurn(
            user_input="second",
            expected_tools=["search_stack_exchange_for_error", "analyze_error_and_suggest_fix"],
            expected_keywords=["pandas"],
            expected_links=["https://stackoverflow.com/q/2"],
        ),
    ]

    expectations = collect_turn_expectations(turns)

    assert expectations.expected_tools == [
        "analyze_error_and_suggest_fix",
        "search_stack_exchange_for_error",
    ]
    assert expectations.expected_keywords == ["pandas"]
    assert len(expectations.expected_links) == 2


def test_load_scenarios_round_trips_sample_file():
    sample_file = next(DEFAULT_SCENARIO_DIR.glob("*.json"))
    scenarios = load_scenarios_from_file(sample_file)
    assert scenarios, "Expected at least one scenario in the sample file"
