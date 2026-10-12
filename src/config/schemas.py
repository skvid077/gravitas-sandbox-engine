from pydantic import BaseModel, ConfigDict, Field

from config.constants.visual_constants import DEFAULT_BODY_COLOR


class BodyStateSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, allow_inf_nan=False)

    name: str = Field(min_length=1)
    color: str = DEFAULT_BODY_COLOR
    mass: float = Field(gt=0)
    radius: float = Field(gt=0)
    position: tuple[float, float]
    velocity: tuple[float, float] = (0.0, 0.0)


class SimulationScenarioSchema(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    name: str = Field(min_length=1)
    bodies: list[BodyStateSchema] = Field(default_factory=list)


# Псевдонимы для совместимости с прежними именами схем.
BodyState = BodyStateSchema
SimulationScenario = SimulationScenarioSchema
