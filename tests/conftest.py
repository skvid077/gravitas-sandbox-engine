import pytest
from config.schemas import BodyState
from core.simulation import Simulation
from core.engine import PhysicsEngine

@pytest.fixture
def empty_simulation():
    return Simulation()

@pytest.fixture
def zero_gravity_engine():
    return PhysicsEngine(g_const=0.0)

@pytest.fixture
def standard_body():
    return BodyState(
        name="Standard",
        mass=10.0,
        radius=5.0,
        position=(0.0, 0.0),
        velocity=(0.0, 0.0),
        color="#FFFFFF"
    )
