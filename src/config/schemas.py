from typing import List, Tuple
from pydantic import BaseModel, Field, ConfigDict

class BodyState(BaseModel):
    """
    Чистая модель данных физического тела. 
    Используется для хранения состояния, передачи данных между модулями 
    и автоматической сериализации/десериализации в JSON.
    """
    # Настройки модели для Pydantic V2
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True
    )

    name: str = Field(..., min_length=1, description="Имя тела")
    color: str = Field(default="#FFFFFF", description="Цвет в HEX")
    mass: float = Field(..., gt=0, description="Масса (m > 0)")
    radius: float = Field(..., gt=0, description="Радиус (r > 0)")
    position: Tuple[float, float] = Field(..., description="Координаты (x, y)")
    velocity: Tuple[float, float] = Field(default=(0.0, 0.0), description="Вектор скорости (vx, vy)")


class SimulationScenario(BaseModel):
    """
    Модель сценария симуляции. 
    Представляет собой заголовок и полный набор физических тел для инициализации мира.
    """
    # Настройки модели для Pydantic V2
    model_config = ConfigDict(
        populate_by_name=True
    )

    name: str = Field(..., min_length=1, description="Название сценария")
    bodies: List[BodyState] = Field(default_factory=list, description="Список небесных тел")
