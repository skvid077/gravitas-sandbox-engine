from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CollisionEvent:
    simulation_time: float
    first_body_name: str
    second_body_name: str
    result_body_name: str
    result_mass: float
