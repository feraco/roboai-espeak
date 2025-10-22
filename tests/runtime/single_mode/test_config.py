from unittest.mock import mock_open, patch

import json5
import pytest

from actions.base import AgentAction
from inputs.base import Sensor, SensorConfig
from llm import LLM
from llm.output_model import CortexOutputModel
from runtime.single_mode.config import RuntimeConfig, load_config
from simulators.base import Simulator, SimulatorConfig


@pytest.fixture
def mock_config_data():
    return {
        "hertz": 10.0,
        "name": "test_config",
        "api_key": "global_test_api_key",
        "system_prompt_base": "system prompt base",
        "system_governance": "system governance",
        "system_prompt_examples": "system prompt examples",
        "agent_inputs": [{"type": "test_input"}],
        "cortex_llm": {"type": "test_llm", "config": {"model": "test-model"}},
        "simulators": [
            {"type": "test_simulator", "config": {"api_key": "sim_test_api_key"}}
        ],
        "agent_actions": [
            {
                "name": "test_action",
                "connector": "test_connector",
                "exclude_from_prompt": False,
                "config": {
                    "arg1": "val1",
                },
            }
        ],
    }


@pytest.fixture
def mock_dependencies():
    class MockInput(Sensor):
        def __init__(self, config=SensorConfig()):
            super().__init__(config)

    class MockAction(AgentAction):
        def __init__(self):
            super().__init__(
                name="mock_action",
                llm_label="mock_llm_label",
                interface="mock_interface",
                connector="mock_connector",
                exclude_from_prompt="mock_exclude_from_prompt",
            )

    class MockSimulator(Simulator):
        def __init__(self, config: SimulatorConfig):
            super().__init__(config)

    class MockLLM(LLM[CortexOutputModel]):
        pass

    return {
        "input": MockInput,
        "action": MockAction,
        "simulator": MockSimulator,
        "llm": MockLLM,
    }


@pytest.fixture
def mock_empty_config_data():
    return {
        "hertz": 10.0,
        "name": "empty_config",
        "system_prompt_base": "",
        "system_governance": "",
        "system_prompt_examples": "",
        "agent_inputs": [{"type": "nonexistent_input_type"}],
        "cortex_llm": {"type": "test_llm", "config": {}},
        "simulators": [],
        "agent_actions": [],
    }


@pytest.fixture
def mock_multiple_components_config():
    return {
        "hertz": 20.0,
        "name": "multiple_components",
        "system_prompt_base": "system prompt base",
        "system_governance": "system governance",
        "system_prompt_examples": "system prompt examples",
        "agent_inputs": [
            {"type": "test_input_1"},
            {"type": "test_input_2"},
        ],
        "cortex_llm": {"type": "test_llm", "config": {"model": "test-model"}},
        "simulators": [{"type": "test_simulator_1"}, {"type": "test_simulator_2"}],
        "agent_actions": [
            {
                "name": "test_action_1",
                "llm_label": "emotion",
                "connector": "test_connector_1",
                "exclude_from_prompt": False,
            },
            {
                "name": "test_action_2",
                "llm_label": "emotion",
                "connector": "test_connector_2",
                "exclude_from_prompt": True,
            },
        ],
    }


def test_load_config(mock_config_data, mock_dependencies):
    with (
        patch("builtins.open", mock_open(read_data=json5.dumps(mock_config_data))),
        patch(
            "runtime.single_mode.config.load_input",
            return_value=mock_dependencies["input"],
        ),
        patch(
            "runtime.single_mode.config.load_action",
            return_value=mock_dependencies["action"](),
        ),
        patch(
            "runtime.single_mode.config.load_simulator",
            return_value=mock_dependencies["simulator"],
        ),
        patch(
            "runtime.single_mode.config.load_llm", return_value=mock_dependencies["llm"]
        ),
    ):
        config = load_config("test_config")

        assert isinstance(config, RuntimeConfig)
        assert config.hertz == mock_config_data["hertz"]
        assert config.name == mock_config_data["name"]
        assert config.system_prompt_base == mock_config_data["system_prompt_base"]
        assert config.system_governance == mock_config_data["system_governance"]
        assert (
            config.system_prompt_examples == mock_config_data["system_prompt_examples"]
        )
        assert config.api_key == mock_config_data["api_key"]
        assert len(config.agent_inputs) == 1
        assert isinstance(config.agent_inputs[0], mock_dependencies["input"])
        assert config.agent_inputs[0].config.api_key == mock_config_data["api_key"]
        assert isinstance(config.cortex_llm, mock_dependencies["llm"])
        assert len(config.simulators) == 1
        assert isinstance(config.simulators[0], mock_dependencies["simulator"])
        assert config.simulators[0].config.api_key == "sim_test_api_key"
        assert len(config.agent_actions) == 1
        assert isinstance(config.agent_actions[0], mock_dependencies["action"])


def test_load_empty_config(mock_empty_config_data, mock_dependencies):
    with (
        patch(
            "builtins.open", mock_open(read_data=json5.dumps(mock_empty_config_data))
        ),
        patch(
            "runtime.single_mode.config.load_input",
            return_value=mock_dependencies["input"],
        ),
        patch(
            "runtime.single_mode.config.load_action",
            return_value=mock_dependencies["action"](),
        ),
        patch(
            "runtime.single_mode.config.load_simulator",
            return_value=mock_dependencies["simulator"],
        ),
        patch(
            "runtime.single_mode.config.load_llm", return_value=mock_dependencies["llm"]
        ),
    ):
        config = load_config("empty_config")

        assert isinstance(config, RuntimeConfig)
        assert config.hertz == mock_empty_config_data["hertz"]
        assert config.name == mock_empty_config_data["name"]
        assert config.system_prompt_base == ""
        assert config.system_governance == ""
        assert config.system_prompt_examples == ""
        assert len(config.agent_inputs) == 1
        assert isinstance(config.agent_inputs[0], mock_dependencies["input"])
        assert isinstance(config.cortex_llm, mock_dependencies["llm"])
        assert len(config.simulators) == 0
        assert len(config.agent_actions) == 0


def test_load_multiple_components(mock_multiple_components_config, mock_dependencies):
    with (
        patch(
            "builtins.open",
            mock_open(read_data=json5.dumps(mock_multiple_components_config)),
        ),
        patch(
            "runtime.single_mode.config.load_input",
            return_value=mock_dependencies["input"],
        ),
        patch(
            "runtime.single_mode.config.load_action",
            return_value=mock_dependencies["action"](),
        ),
        patch(
            "runtime.single_mode.config.load_simulator",
            return_value=mock_dependencies["simulator"],
        ),
        patch(
            "runtime.single_mode.config.load_llm", return_value=mock_dependencies["llm"]
        ),
    ):
        config = load_config("multiple_components")

        assert isinstance(config, RuntimeConfig)
        assert config.hertz == mock_multiple_components_config["hertz"]
        assert config.name == mock_multiple_components_config["name"]
        assert len(config.agent_inputs) == 2
        assert len(config.simulators) == 2
        assert len(config.agent_actions) == 2


def test_load_config_missing_required_fields():
    invalid_config = {
        "name": "invalid_config",
    }

    with (patch("builtins.open", mock_open(read_data=json5.dumps(invalid_config))),):
        with pytest.raises(KeyError):
            load_config("invalid_config")


def test_load_config_invalid_hertz():
    invalid_config = {
        "hertz": -1.0,
        "name": "invalid_hertz",
        "system_prompt_base": "system prompt base",
        "system_governance": "system governance",
        "system_prompt_examples": "system prompt examples",
        "agent_inputs": [],
        "cortex_llm": {"type": "test_llm", "config": {}},
        "simulators": [],
        "agent_actions": [],
    }

    with (patch("builtins.open", mock_open(read_data=json5.dumps(invalid_config))),):
        with pytest.raises(ValueError):
            load_config("invalid_config")


def test_load_config_missing_file():
    with pytest.raises(FileNotFoundError):
        load_config("nonexistent_config")


def test_load_config_invalid_json():
    with patch("builtins.open", mock_open(read_data="invalid json5")):

        # try:
        #     load_config("invalid_config")
        # except Exception as error:
        #     logging.info(f"{error} ERRORTYPE: {type(error).__name__}")

        with pytest.raises(ValueError):
            load_config("invalid_config")


def test_load_config_invalid_component_type():
    invalid_config = {
        "hertz": 10.0,
        "name": "invalid_component",
        "system_prompt_base": "system prompt base",
        "system_governance": "system governance",
        "system_prompt_examples": "system prompt examples",
        "agent_inputs": [{"type": "nonexistent_input_type"}],
        "cortex_llm": {"type": "test_llm", "config": {}},
        "simulators": [],
        "agent_actions": [],
    }

    with (
        patch("builtins.open", mock_open(read_data=json5.dumps(invalid_config))),
        patch("runtime.single_mode.config.load_input", side_effect=ImportError),
    ):
        with pytest.raises(ImportError):
            load_config("invalid_config")
