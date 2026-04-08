"""Shared fixtures for claims_env tests."""

import sys
from pathlib import Path

import pytest

# Ensure the project root is on sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

from models import ClaimsAction, ClaimsObservation, ClaimsState
from server.claims_env_environment import ClaimsEnvironment
from server.generator.scenario_generator import ScenarioGenerator


@pytest.fixture
def env():
    """Fresh environment instance."""
    return ClaimsEnvironment()


@pytest.fixture
def easy_env(env):
    """Environment reset to easy task."""
    env.reset(task_id="easy_auto_collision")
    return env


@pytest.fixture
def medium_env(env):
    """Environment reset to medium task."""
    env.reset(task_id="medium_medical_exclusions")
    return env


@pytest.fixture
def hard_env(env):
    """Environment reset to hard task."""
    env.reset(task_id="hard_property_fraud")
    return env
