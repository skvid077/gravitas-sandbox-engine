import random
from typing import List, Optional, Set
from config.schemas import BodyState
from core.engine import PhysicsEngine
from config.constants import (
    DEFAULT_PLANET_NAME,
    DEFAULT_PLANET_MASS,
    DEFAULT_PLANET_RADIUS,
    RANDOM_COLORS
)


class Simulation:
    """
    Класс управления состоянием симуляции.
    Служит контейнером для небесных тел и связующим звеном 
    между графическим интерфейсом и физическим движком.
    """

    def __init__(self, initial_bodies: Optional[List[BodyState]] = None) -> None:
        """
        Инициализирует симуляцию.

        Args:
            initial_bodies (Optional[List[BodyState]]): Начальный список тел. 
                Если не передан, создается пустая симуляция.
        """
        # Храним состояние мира здесь
        self.bodies: List[BodyState] = initial_bodies if initial_bodies else []
        self.physics_engine: PhysicsEngine = PhysicsEngine()

    def step(self, dt: float) -> None:
        """
        Продвигает симуляцию на один шаг во времени (dt).

        Args:
            dt (float): Шаг времени в секундах.
        """
        if not self.bodies:
            return
        self.physics_engine.update(self.bodies, dt)

    def add_default_body(self, x: float, y: float) -> BodyState:
        """
        Создает новое тело с параметрами по умолчанию и добавляет его в мир.
        Реализует логику генерации уникального имени.

        Args:
            x (float): Координата появления по оси X.
            y (float): Координата появления по оси Y.

        Returns:
            BodyState: Созданный объект состояния тела.
        """
        name = DEFAULT_PLANET_NAME
        counter = 1
        
        # Используем set для быстрой проверки наличия имени (O(1))
        existing_names: Set[str] = {p.name for p in self.bodies}
        
        while name in existing_names:
            name = f"{DEFAULT_PLANET_NAME} {counter}"
            counter += 1

        new_body = BodyState(
            name=name,
            mass=DEFAULT_PLANET_MASS,
            radius=DEFAULT_PLANET_RADIUS,
            position=(x, y),
            velocity=(0.0, 0.0),
            color=random.choice(RANDOM_COLORS)
        )
        
        self.bodies.append(new_body)
        return new_body

    def remove_body_by_index(self, index: int) -> None:
        """
        Безопасно удаляет тело из симуляции по его индексу.

        Args:
            index (int): Индекс удаляемого тела в списке.
        """
        if 0 <= index < len(self.bodies):
            self.bodies.pop(index)
