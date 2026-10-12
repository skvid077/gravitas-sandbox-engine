from pathlib import Path

import pytest

from config.models import BodyState
from core.engine import PhysicsEngine
from core.simulation import Simulation

DEMO_DIR = Path(__file__).resolve().parents[1] / "demo"


def pytest_generate_tests(metafunc: pytest.Metafunc) -> None:
    if "demo_scenario_path" not in metafunc.fixturenames:
        return

    scenario_paths = sorted(DEMO_DIR.glob("*.json"))
    if not scenario_paths:
        raise pytest.UsageError(f"No JSON demo scenarios found in {DEMO_DIR}")

    metafunc.parametrize("demo_scenario_path", scenario_paths, ids=lambda path: path.stem)


@pytest.fixture
def empty_simulation() -> Simulation:
    return Simulation()


@pytest.fixture
def zero_gravity_engine() -> PhysicsEngine:
    return PhysicsEngine(g_const=0.0)


@pytest.fixture
def standard_body() -> BodyState:
    return BodyState(
        name="Standard",
        mass=10.0,
        radius=5.0,
        position=(0.0, 0.0),
        velocity=(0.0, 0.0),
        color="#FFFFFF",
    )
