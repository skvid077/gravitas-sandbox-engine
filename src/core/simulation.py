import random

from config.constants import (
    DEFAULT_PLANET_MASS,
    DEFAULT_PLANET_NAME,
    DEFAULT_PLANET_RADIUS,
    RANDOM_COLORS,
)
from config.models import BodyState
from core.engine import PhysicsEngine
from core.events import CollisionEvent


class Simulation:
    def __init__(self, initial_bodies: list[BodyState] | None = None) -> None:
        self.bodies = list(initial_bodies) if initial_bodies else []
        self.physics_engine: PhysicsEngine = PhysicsEngine()
        self.elapsed_seconds = 0.0
        self.collision_events: list[CollisionEvent] = []

    def step(self, dt: float) -> list[CollisionEvent]:
        self.elapsed_seconds += dt
        events = self.physics_engine.update(self.bodies, dt, self.elapsed_seconds)
        self.collision_events.extend(events)
        return events

    def add_default_body(self, x: float, y: float) -> BodyState:
        name = DEFAULT_PLANET_NAME
        counter = 1
        existing_names = {body.name for body in self.bodies}

        while name in existing_names:
            name = f"{DEFAULT_PLANET_NAME} {counter}"
            counter += 1

        new_body = BodyState(
            name=name,
            mass=DEFAULT_PLANET_MASS,
            radius=DEFAULT_PLANET_RADIUS,
            position=(x, y),
            velocity=(0.0, 0.0),
            color=random.choice(RANDOM_COLORS),
        )

        self.bodies.append(new_body)
        return new_body

    def remove_body_by_index(self, index: int) -> None:
        if 0 <= index < len(self.bodies):
            self.bodies.pop(index)
