import math
import pytest
from config.schemas import BodyState
from core.engine import PhysicsEngine


def test_inertia_no_gravity(zero_gravity_engine: PhysicsEngine, standard_body: BodyState) -> None:
    standard_body.velocity = [10.0, -5.0]
    zero_gravity_engine.update([standard_body], dt=1.0)
    
    assert standard_body.position == [10.0, -5.0]
    assert standard_body.velocity == [10.0, -5.0]


def test_gravity_pull_direction() -> None:
    engine = PhysicsEngine(g_const=100.0)
    
    b1 = BodyState(name="L", mass=100.0, radius=5.0, position=(0.0, 0.0), velocity=(0.0, 0.0), color="#FFF")
    b2 = BodyState(name="R", mass=100.0, radius=5.0, position=(20.0, 0.0), velocity=(0.0, 0.0), color="#FFF")
    
    engine.update([b1, b2], dt=0.1)
    
    assert b1.velocity[0] > 0
    assert b2.velocity[0] < 0
    assert b1.velocity[1] == 0.0
    assert b2.velocity[1] == 0.0


def test_collision_merge(zero_gravity_engine: PhysicsEngine) -> None:
    b1 = BodyState(name="A", mass=10.0, radius=10.0, position=(0.0, 0.0), velocity=(10.0, 0.0), color="#FFF")
    b2 = BodyState(name="B", mass=20.0, radius=10.0, position=(15.0, 0.0), velocity=(-5.0, 0.0), color="#FFF")
    
    initial_p = (b1.mass * b1.velocity[0]) + (b2.mass * b2.velocity[0])
    
    bodies = [b1, b2]
    zero_gravity_engine.update(bodies, dt=0.0)
    
    assert len(bodies) == 1
    merged = bodies[0]
    
    assert merged.mass == 30.0
    final_p = merged.mass * merged.velocity[0]
    assert math.isclose(initial_p, final_p, abs_tol=1e-5)
    
    expected_radius = math.sqrt(10.0**2 + 10.0**2)
    assert math.isclose(merged.radius, expected_radius, abs_tol=1e-5)


def test_singularity_protection() -> None:
    engine = PhysicsEngine(g_const=100.0)
    # Смещаем второе тело на 1e-5, чтобы не сломать QuadTree точным совпадением координат, 
    # но при этом проверить защиту от деления на ноль (softening)
    b1 = BodyState(name="A", mass=100.0, radius=5.0, position=(0.0, 0.0), velocity=(0.0, 0.0), color="#FFF")
    b2 = BodyState(name="B", mass=100.0, radius=5.0, position=(0.0, 1e-5), velocity=(0.0, 0.0), color="#FFF")

    try:
        engine.update([b1, b2], dt=0.1)
    except ZeroDivisionError:
        pytest.fail("Параметр softening не работает, произошло деление на ноль.")
    except RecursionError:
        pytest.fail("QuadTree ушел в рекурсию при близком расположении объектов.")
