import math
import pytest
from config.schemas import BodyState
from core.engine import PhysicsEngine

def test_inertia_no_gravity(zero_gravity_engine: PhysicsEngine, standard_body: BodyState) -> None:
    standard_body.velocity = (10.0, -5.0)
    
    zero_gravity_engine.update([standard_body], dt=1.0)
    
    assert standard_body.position == (10.0, -5.0)
    assert standard_body.velocity == (10.0, -5.0)

def test_gravity_pull_direction() -> None:
    from core.engine import PhysicsEngine
    engine = PhysicsEngine(g_const=100.0)
    
    # Ставим вторую планету на X: 20 (расстояние 20 > суммы радиусов 10)
    b1 = BodyState(name="L", mass=100.0, radius=5.0, position=(0.0, 0.0), velocity=(0.0, 0.0), color="#FFF")
    b2 = BodyState(name="R", mass=100.0, radius=5.0, position=(20.0, 0.0), velocity=(0.0, 0.0), color="#FFF")
    
    engine.update([b1, b2], dt=0.1)
    
    # Теперь они корректно притягиваются без столкновения
    assert b1.velocity[0] > 0
    assert b2.velocity[0] < 0
    assert b1.velocity[1] == 0.0
    assert b2.velocity[1] == 0.0

def test_momentum_conservation(zero_gravity_engine: PhysicsEngine) -> None:
    zero_gravity_engine.restitution = 1.0  # Абсолютно упругий удар
    
    b1 = BodyState(name="A", mass=10.0, radius=10.0, position=(0.0, 0.0), velocity=(10.0, 0.0), color="#FFF")
    b2 = BodyState(name="B", mass=20.0, radius=10.0, position=(15.0, 0.0), velocity=(-5.0, 0.0), color="#FFF")
    
    initial_p = sum(b.mass * b.velocity[0] for b in [b1, b2])
    
    zero_gravity_engine._resolve_collisions([b1, b2])
    
    final_p = sum(b.mass * b.velocity[0] for b in [b1, b2])
    
    assert math.isclose(initial_p, final_p, abs_tol=1e-5)
    assert math.dist(b1.position, b2.position) >= (b1.radius + b2.radius)

def test_singularity_protection() -> None:
    engine = PhysicsEngine(g_const=100.0)
    # Тела в одной точке
    b1 = BodyState(name="A", mass=100.0, radius=5.0, position=(0.0, 0.0), velocity=(0.0, 0.0), color="#FFF")
    b2 = BodyState(name="B", mass=100.0, radius=5.0, position=(0.0, 0.0), velocity=(0.0, 0.0), color="#FFF")
    
    try:
        engine.update([b1, b2], dt=0.1)
    except ZeroDivisionError:
        pytest.fail("Параметр softening не работает, произошло деление на ноль.")
