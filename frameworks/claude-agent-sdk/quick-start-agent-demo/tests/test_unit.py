"""Unit tests for Claude Agent SDK quick start - tests code logic without API calls."""

import json
from pathlib import Path

import pytest

from src.main import (
    load_scenario_files,
    parse_scenario_options,
)
from claude_agent_sdk import ClaudeAgentOptions


class TestParseScenarioOptions:
    """Test parse_scenario_options function."""

    def test_parse_scenario_options_with_all_fields(self):
        """Test parsing options with all fields."""
        options_dict = {
            "system_prompt": "You are a helpful assistant",
            "max_turns": 5,
            "allowed_tools": ["Read", "Write"],
        }
        
        result = parse_scenario_options(options_dict)
        
        assert result is not None
        assert isinstance(result, ClaudeAgentOptions)
        assert result.system_prompt == "You are a helpful assistant"
        assert result.max_turns == 5
        assert result.allowed_tools == ["Read", "Write"]

    def test_parse_scenario_options_with_partial_fields(self):
        """Test parsing options with only some fields."""
        options_dict = {
            "system_prompt": "Test prompt",
            "max_turns": 3,
        }
        
        result = parse_scenario_options(options_dict)
        
        assert result is not None
        assert result.system_prompt == "Test prompt"
        assert result.max_turns == 3
        assert result.allowed_tools is None

    def test_parse_scenario_options_with_none(self):
        """Test parsing None options."""
        result = parse_scenario_options(None)
        
        assert result is None

    def test_parse_scenario_options_with_empty_dict(self):
        """Test parsing empty options dict."""
        result = parse_scenario_options({})
        
        # Empty dict is falsy, so returns None
        assert result is None

    def test_parse_scenario_options_with_only_system_prompt(self):
        """Test parsing options with only system prompt."""
        options_dict = {
            "system_prompt": "Just a prompt",
        }
        
        result = parse_scenario_options(options_dict)
        
        assert result is not None
        assert result.system_prompt == "Just a prompt"
        assert result.max_turns is None
        assert result.allowed_tools is None


class TestLoadScenarioFiles:
    """Test load_scenario_files function."""

    def test_load_scenario_files_single_scenario(self, tmp_path):
        """Test loading a single scenario file."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        # Create a single scenario file
        scenario_file = scenarios_dir / "test_scenario.json"
        scenario_data = {
            "name": "Test Scenario",
            "description": "A test scenario",
            "prompt": "Test prompt",
        }
        scenario_file.write_text(json.dumps(scenario_data))
        
        result = load_scenario_files(scenarios_dir)
        
        assert len(result) == 1
        assert result[0]["name"] == "Test Scenario"
        assert result[0]["prompt"] == "Test prompt"

    def test_load_scenario_files_multiple_scenarios(self, tmp_path):
        """Test loading multiple scenario files."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        # Create multiple scenario files
        for i in range(3):
            scenario_file = scenarios_dir / f"scenario_{i}.json"
            scenario_data = {
                "name": f"Scenario {i}",
                "prompt": f"Prompt {i}",
            }
            scenario_file.write_text(json.dumps(scenario_data))
        
        result = load_scenario_files(scenarios_dir)
        
        assert len(result) == 3
        assert all("name" in s for s in result)
        assert all("prompt" in s for s in result)

    def test_load_scenario_files_with_scenarios_array(self, tmp_path):
        """Test loading a file with scenarios array."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        scenario_file = scenarios_dir / "combined.json"
        scenario_data = {
            "scenarios": [
                {"name": "Scenario 1", "prompt": "Prompt 1"},
                {"name": "Scenario 2", "prompt": "Prompt 2"},
            ]
        }
        scenario_file.write_text(json.dumps(scenario_data))
        
        result = load_scenario_files(scenarios_dir)
        
        assert len(result) == 2
        assert result[0]["name"] == "Scenario 1"
        assert result[1]["name"] == "Scenario 2"

    def test_load_scenario_files_empty_directory(self, tmp_path):
        """Test loading from empty directory."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        result = load_scenario_files(scenarios_dir)
        
        assert len(result) == 0

    def test_load_scenario_files_handles_invalid_json(self, tmp_path):
        """Test that invalid JSON files are handled gracefully."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        # Create invalid JSON file
        invalid_file = scenarios_dir / "invalid.json"
        invalid_file.write_text("{ invalid json }")
        
        # Create valid file
        valid_file = scenarios_dir / "valid.json"
        valid_file.write_text(json.dumps({"name": "Valid", "prompt": "test"}))
        
        # Should not raise, but should skip invalid file
        result = load_scenario_files(scenarios_dir)
        
        # Should only load the valid file
        assert len(result) == 1
        assert result[0]["name"] == "Valid"

    def test_load_scenario_files_mixed_format(self, tmp_path):
        """Test loading mixed format files."""
        scenarios_dir = tmp_path / "scenarios"
        scenarios_dir.mkdir()
        
        # Single scenario file
        single_file = scenarios_dir / "single.json"
        single_file.write_text(json.dumps({"name": "Single", "prompt": "test"}))
        
        # Combined file with scenarios array
        combined_file = scenarios_dir / "combined.json"
        combined_file.write_text(json.dumps({
            "scenarios": [
                {"name": "Combined 1", "prompt": "test1"},
                {"name": "Combined 2", "prompt": "test2"},
            ]
        }))
        
        result = load_scenario_files(scenarios_dir)
        
        # Files are loaded in sorted order, so "combined.json" comes before "single.json"
        assert len(result) == 3
        assert result[0]["name"] == "Combined 1"
        assert result[1]["name"] == "Combined 2"
        assert result[2]["name"] == "Single"

