import json
import re
from pathlib import Path
from typing import List, Tuple, Any

from pydantic import BaseModel, Field, field_validator, model_validator


class BodyState(BaseModel):
    """
    Модель физического состояния отдельного космического тела.
    Отвечает за хранение параметров объекта и валидацию атомарных свойств.
    """
    
    name: str = Field(
        ..., 
        min_length=1,
        description="Уникальное имя или название тела"
    )
    color: str = Field(
        default="#FFFFFF", 
        description="Цвет тела для отрисовки в формате HEX (например, #FF0000)"
    )
    mass: float = Field(
        ..., 
        gt=0, 
        description="Масса тела. Должна быть строго больше 0"
    )
    radius: float = Field(
        ..., 
        gt=0, 
        description="Радиус тела для отрисовки и коллизий. Должен быть больше 0"
    )
    position: Tuple[float, float] = Field(
        ..., 
        description="Начальные координаты (x, y)"
    )
    velocity: Tuple[float, float] = Field(
        default=(0.0, 0.0), 
        description="Начальный вектор скорости (vx, vy)"
    )

    @field_validator('color')
    @classmethod
    def validate_hex_color(cls, value: str) -> str:
        """
        Проверяет, что цвет передан в корректном формате HEX.
        
        Args:
            value (str): Строка цвета.

        Raises:
            ValueError: Если формат не совпадает с паттерном HEX.

        Returns:
            str: Корректная строка цвета в верхнем регистре.
        """
        if not re.match(r'^#[0-9a-fA-F]{6}$', value):
            raise ValueError(f"Некорректный формат цвета: '{value}'. Ожидается HEX, например '#FF0000'.")
        return value.upper()


class SimulationScenario(BaseModel):
    """
    Модель полного сценария симуляции.
    Хранит глобальные настройки физики и список всех тел.
    Осуществляет комплексную валидацию логики (уникальность имен, отсутствие коллизий).
    """
    
    name: str = Field(
        ..., 
        min_length=1,
        description="Название сценария для отображения в UI"
    )
    g_const: float = Field(
        default=1.0, 
        description="Гравитационная постоянная симуляции"
    )
    dt: float = Field(
        default=0.016, 
        gt=0, 
        description="Шаг интегрирования в секундах"
    )
    softening: float = Field(
        default=0.1, 
        ge=0, 
        description="Параметр смягчения гравитации для предотвращения сингулярности"
    )
    bodies: List[BodyState] = Field(
        default_factory=list, 
        description="Набор физических тел, участвующих в симуляции"
    )

    @model_validator(mode='after')
    def validate_scenario_logic(self) -> "SimulationScenario":
        """
        Проверяет бизнес-логику сценария после базовой проверки типов:
        1. Уникальность имен планет.
        2. Отсутствие пересечений (наложений) геометрии планет на старте.

        Raises:
            ValueError: При нахождении дубликатов или пересечений.

        Returns:
            SimulationScenario: Валидный объект сценария.
        """
        seen_names = set()
        
        for i, body in enumerate(self.bodies):
            # Проверка уникальности имени
            if body.name in seen_names:
                raise ValueError(f"Найдено дублирующееся имя планеты: '{body.name}'")
            seen_names.add(body.name)

            # Проверка коллизий (сравнение квадратов расстояний для оптимизации)
            for j in range(i):
                other = self.bodies[j]
                dx: float = body.position[0] - other.position[0]
                dy: float = body.position[1] - other.position[1]
                min_distance: float = body.radius + other.radius
                
                if (dx * dx + dy * dy) < (min_distance * min_distance):
                    raise ValueError(
                        f"Геометрическое пересечение: планета '{body.name}' "
                        f"накладывается на '{other.name}'."
                    )
        return self

    @classmethod
    def load_from_json(cls, file_path: Path) -> "SimulationScenario":
        """
        Загружает сценарий из JSON-файла и автоматически валидирует его.

        Args:
            file_path (Path): Путь к файлу конфигурации.

        Raises:
            FileNotFoundError: Если файл не существует.
            ValidationError: Если структура JSON или логика данных некорректны.

        Returns:
            SimulationScenario: Готовый к использованию сценарий.
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"Файл сценария не найден по пути: {path}")

        with open(path, "r", encoding="utf-8") as file:
            data: dict[str, Any] = json.load(file)

        # Распаковка словаря в Pydantic модель (здесь триггерятся все валидаторы)
        return cls(**data)
