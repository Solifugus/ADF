"""
Test parser against the example ADF files in the repository
"""

import pytest
from pathlib import Path
from adf import parse_file


# Path to examples directory (relative to tests directory)
EXAMPLES_DIR = Path(__file__).parent.parent.parent.parent / "examples"


def test_examples_dir_exists():
    """Verify examples directory exists"""
    assert EXAMPLES_DIR.exists(), f"Examples directory not found at {EXAMPLES_DIR}"


def test_basic_example():
    """Test basic.adf example"""
    if not (EXAMPLES_DIR / "basicadf").exists():
        pytest.skip("basicadf not found")

    doc = parse_file(str(EXAMPLES_DIR / "basicadf"))
    # Basic validation - check that it parsed without error
    assert doc is not None
    data = doc.to_dict()
    assert isinstance(data, dict)


def test_arrays_example():
    """Test arrays.adf example"""
    if not (EXAMPLES_DIR / "arraysadf").exists():
        pytest.skip("arraysadf not found")

    doc = parse_file(str(EXAMPLES_DIR / "arraysadf"))
    assert doc is not None
    data = doc.to_dict()
    assert isinstance(data, dict)


def test_multiline_example():
    """Test multiline.adf example"""
    if not (EXAMPLES_DIR / "multiline.adf").exists():
        pytest.skip("multiline.adf not found")

    doc = parse_file(str(EXAMPLES_DIR / "multiline.adf"))
    assert doc is not None
    data = doc.to_dict()
    assert isinstance(data, dict)


def test_constraints_example():
    """Test constraints.adf example"""
    if not (EXAMPLES_DIR / "constraints.adf").exists():
        pytest.skip("constraints.adf not found")

    doc = parse_file(str(EXAMPLES_DIR / "constraints.adf"))
    assert doc is not None
    data = doc.to_dict()
    assert isinstance(data, dict)


def test_config_full_example():
    """Test config_full.adf example"""
    if not (EXAMPLES_DIR / "config_full.adf").exists():
        pytest.skip("config_full.adf not found")

    doc = parse_file(str(EXAMPLES_DIR / "config_full.adf"))
    assert doc is not None

    # Check specific values
    assert doc.get("app.name") == "StoryWeaver"
    assert doc.get("app.version") == 1.0
    assert doc.get("app.ui.theme") == "dark"

    # Check array
    features = doc.get("app.features")
    assert isinstance(features, list)
    assert "autosave" in features

    # Check object array
    providers = doc.get("app.auth.providers")
    assert isinstance(providers, list)
    assert len(providers) == 3


def test_game_state_example():
    """Test game_state.adf example"""
    if not (EXAMPLES_DIR / "game_state.adf").exists():
        pytest.skip("game_state.adf not found")

    doc = parse_file(str(EXAMPLES_DIR / "game_state.adf"))
    assert doc is not None

    # Check nested structure
    assert doc.get("game.title") == "Illumera: Echoes of the Archive"
    assert doc.get("game.player.name") == "Arlen"
    assert doc.get("game.player.level") == 7

    # Check stats
    assert doc.get("game.player.stats.health") == 68
    assert doc.get("game.player.stats.health_max") == 100

    # Check inventory (object array)
    inventory = doc.get("game.player.inventory")
    assert isinstance(inventory, list)
    assert len(inventory) == 3

    # Check NPCs
    npcs = doc.get("game.world.region.npcs")
    assert isinstance(npcs, list)
    assert len(npcs) == 2


def test_agent_memory_example():
    """Test agent_memory.adf example"""
    if not (EXAMPLES_DIR / "agent_memory.adf").exists():
        pytest.skip("agent_memory.adf not found")

    doc = parse_file(str(EXAMPLES_DIR / "agent_memory.adf"))
    assert doc is not None
    data = doc.to_dict()
    assert isinstance(data, dict)


def test_upgrade_patch_example():
    """Test upgrade_patch.adf (relative sections)"""
    if not (EXAMPLES_DIR / "upgrade_patch.adf").exists():
        pytest.skip("upgrade_patch.adf not found")

    doc = parse_file(str(EXAMPLES_DIR / "upgrade_patch.adf"))
    assert doc is not None

    # This file has relative sections
    relative = doc.get_relative_sections()
    assert isinstance(relative, dict)
    assert len(relative) > 0


def test_docs_mixed_example():
    """Test docs_mixed.adf example"""
    if not (EXAMPLES_DIR / "docs_mixed.adf").exists():
        pytest.skip("docs_mixed.adf not found")

    doc = parse_file(str(EXAMPLES_DIR / "docs_mixed.adf"))
    assert doc is not None
    data = doc.to_dict()
    assert isinstance(data, dict)
