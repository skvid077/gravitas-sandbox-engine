from config.constants import (
    ERROR_COLLISION,
    ERROR_DUPLICATE_NAME,
)
from config.models import BodyState, SimulationScenario


class ScenarioValidator:
    @staticmethod
    def check_name_uniqueness(
        name: str, planets: list[BodyState], exclude_idx: int | None = None
    ) -> bool:
        clean_name = name.strip()
        if not clean_name:
            return False

        for index, planet in enumerate(planets):
            if exclude_idx is not None and index == exclude_idx:
                continue
            if planet.name == clean_name:
                return False
        return True

    @staticmethod
    def check_collision(
        new_body: BodyState, planets: list[BodyState], exclude_idx: int | None = None
    ) -> str | None:
        for index, other in enumerate(planets):
            if exclude_idx is not None and index == exclude_idx:
                continue

            dx = new_body.position[0] - other.position[0]
            dy = new_body.position[1] - other.position[1]
            distance_squared = dx * dx + dy * dy
            minimum_distance = new_body.radius + other.radius

            if distance_squared < minimum_distance * minimum_distance:
                return other.name
        return None

    @staticmethod
    def validate_body_params(body: BodyState) -> str | None:
        return body.validate()

    @staticmethod
    def validate_scenario(scenario: SimulationScenario) -> list[str]:
        errors: list[str] = []
        seen_names: set[str] = set()
        previous_bodies: list[BodyState] = []

        for body in scenario.bodies:
            if body.name in seen_names:
                errors.append(ERROR_DUPLICATE_NAME.format(body.name))
            seen_names.add(body.name)
            conflict = ScenarioValidator.check_collision(body, previous_bodies)
            if conflict:
                errors.append(ERROR_COLLISION.format(body.name, conflict))
            previous_bodies.append(body)

        return errors
