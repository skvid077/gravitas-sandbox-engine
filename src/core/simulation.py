import random
from typing import List, Optional
from config.schemas import BodyState
from core.engine import PhysicsEngine

class Simulation:
    def __init__(self, initial_bodies: Optional[List[BodyState]] = None):
        # Храним состояние мира здесь
        self.bodies: List[BodyState] = initial_bodies if initial_bodies else []
        self.physics_engine = PhysicsEngine()

    def step(self, dt: float) -> None:
        """Продвигает симуляцию на один шаг во времени."""
        if not self.bodies:
            return
        self.physics_engine.update(self.bodies, dt)

    def add_default_body(self, x: float, y: float) -> BodyState:
        """Бизнес-логика создания нового тела (Фабрика)."""
        colors = ["#FF6464", "#64FF64", "#6464FF", "#FFFF64", "#FF64FF", "#64FFFF", "#E0E5E5", "#DDAA55"]
        
        base_name = "New Planet"
        name = base_name
        counter = 1
        existing_names = [p.name for p in self.bodies]
        while name in existing_names:
            name = f"{base_name} {counter}"
            counter += 1

        new_body = BodyState(
            name=name,
            mass=50.0,
            radius=10.0,
            position=(x, y),
            velocity=(0.0, 0.0),
            color=random.choice(colors)
        )
        
        self.bodies.append(new_body)
        return new_body

    def remove_body_by_index(self, index: int) -> None:
        """Удаляет тело из симуляции."""
        if 0 <= index < len(self.bodies):
            self.bodies.pop(index)
