from typing import List, Tuple
from pydantic import BaseModel, Field

class BodyState(BaseModel):
    """
    Чистая модель данных физического тела. 
    Используется для передачи данных и сериализации в JSON.
    """
    name: str = Field(..., min_length=1)
    color: str = Field(default="#FFFFFF")
    mass: float = Field(..., gt=0) # Pydantic сам выдаст ошибку, если будет 0 или меньше
    radius: float = Field(..., gt=0)
    position: Tuple[float, float] = Field(..., description="Координаты (x, y)")
    velocity: Tuple[float, float] = Field(default=(0.0, 0.0), description="Вектор скорости (vx, vy)")

class SimulationScenario(BaseModel):
    """Модель сценария симуляции."""
    name: str = Field(..., min_length=1)
    bodies: List[BodyState] = Field(default_factory=list)
