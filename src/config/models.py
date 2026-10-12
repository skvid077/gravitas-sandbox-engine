import math
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from types import NotImplementedType

from config.constants import (
    BODY_STRING_FORMAT,
    DEFAULT_BODY_COLOR,
    ERROR_EMPTY_NAME,
    ERROR_MASS_ZERO,
    ERROR_NON_FINITE_COORDINATES,
    ERROR_RADIUS_ZERO,
)


class AbstractBody(ABC):
    @abstractmethod
    def validate(self) -> str | None: ...


@dataclass(eq=False, repr=False, slots=True)
class BodyState(AbstractBody):
    name: str
    mass: float
    radius: float
    position: tuple[float, float]
    velocity: tuple[float, float] = (0.0, 0.0)
    color: str = DEFAULT_BODY_COLOR

    def __eq__(self, other: object) -> bool | NotImplementedType:
        if not isinstance(other, BodyState):
            return NotImplemented
        return (
            self.name,
            self.mass,
            self.radius,
            self.position,
            self.velocity,
            self.color,
        ) == (
            other.name,
            other.mass,
            other.radius,
            other.position,
            other.velocity,
            other.color,
        )

    def __repr__(self) -> str:
        return (
            f"BodyState(name={self.name!r}, mass={self.mass!r}, radius={self.radius!r}, "
            f"position={self.position!r}, velocity={self.velocity!r}, color={self.color!r})"
        )

    def __str__(self) -> str:
        return BODY_STRING_FORMAT.format(self.name, self.mass, self.radius)

    def validate(self) -> str | None:
        if not self.name.strip():
            return ERROR_EMPTY_NAME
        if not math.isfinite(self.mass) or self.mass <= 0:
            return ERROR_MASS_ZERO.format(self.mass)
        if not math.isfinite(self.radius) or self.radius <= 0:
            return ERROR_RADIUS_ZERO.format(self.radius)
        if not all(math.isfinite(value) for value in (*self.position, *self.velocity)):
            return ERROR_NON_FINITE_COORDINATES
        return None


@dataclass(slots=True)
class SimulationScenario:
    name: str
    bodies: list[BodyState] = field(default_factory=list)
