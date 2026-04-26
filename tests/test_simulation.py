import pytest

from core.simulation import Simulation

def test_simulation_initialization(empty_simulation: Simulation) -> None:
    assert len(empty_simulation.bodies) == 0

def test_add_default_body(empty_simulation: Simulation) -> None:
    body = empty_simulation.add_default_body(150.0, 250.0)
    
    assert len(empty_simulation.bodies) == 1
    assert body.position == (150.0, 250.0)
    assert body.mass == 50.0
    assert body.name.startswith("New Planet")

def test_unique_name_generation(empty_simulation: Simulation) -> None:
    b1 = empty_simulation.add_default_body(0.0, 0.0)
    b2 = empty_simulation.add_default_body(10.0, 10.0)
    
    assert b1.name != b2.name

def test_remove_body_by_index(empty_simulation: Simulation) -> None:
    empty_simulation.add_default_body(0.0, 0.0)
    empty_simulation.add_default_body(10.0, 10.0)
    
    empty_simulation.remove_body_by_index(0)
    
    assert len(empty_simulation.bodies) == 1
    assert empty_simulation.bodies[0].position == (10.0, 10.0)

def test_remove_invalid_index(empty_simulation: Simulation) -> None:
    empty_simulation.add_default_body(0.0, 0.0)
    # Не должно падать с IndexError
    empty_simulation.remove_body_by_index(999) 
    assert len(empty_simulation.bodies) == 1

def test_simulation_step_empty(empty_simulation: Simulation) -> None:
    # Не должно вызывать ошибок при отсутствии тел
    empty_simulation.step(0.1)
