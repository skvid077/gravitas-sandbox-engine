import pytest
from pydantic import ValidationError
from config.schemas import BodyState

def test_body_state_valid_creation():
    body = BodyState(
        name="Earth",
        mass=5.97,
        radius=6.37,
        position=(100.0, 200.0),
        velocity=(0.0, 30.0),
        color="#4A90E2"
    )
    assert body.name == "Earth"
    assert body.position == (100.0, 200.0)

def test_body_state_missing_fields():
    with pytest.raises(ValidationError):
        BodyState(name="Invalid")  # Отсутствуют обязательные поля

def test_body_state_type_coercion():
    # Pydantic должен автоматически конвертировать int в float
    body = BodyState(
        name="Coerced",
        mass=10, 
        radius=5,
        position=(0, 0),
        velocity=(0, 0),
        color="#FFF"
    )
    assert isinstance(body.mass, float)
    assert isinstance(body.position[0], float)
