from pathlib import Path

from pydantic import ValidationError

from config.constants import (
    ERROR_FILE_NOT_FOUND,
    ERROR_FILE_READ,
    ERROR_FILE_SAVE,
    ERROR_JSON_SYNTAX,
    ERROR_SCENARIO_LOGIC,
    ERROR_SCENARIO_PARAMETERS,
    ERROR_SCENARIO_SAVE,
    ERROR_UNKNOWN,
    JSON_INDENT,
)
from config.models import BodyState, SimulationScenario
from config.schemas import BodyStateSchema, SimulationScenarioSchema
from core.planets_validator import ScenarioValidator


class ScenarioLoadError(Exception):
    pass


class ScenarioSaveError(Exception):
    pass


class ScenarioFileService:
    @staticmethod
    def load(file_path: str | Path) -> SimulationScenario:
        path = Path(file_path)
        try:
            schema = SimulationScenarioSchema.model_validate_json(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise ScenarioLoadError(ERROR_FILE_NOT_FOUND.format(path)) from error
        except (OSError, UnicodeDecodeError) as error:
            raise ScenarioLoadError(ERROR_FILE_READ.format(error)) from error
        except ValidationError as error:
            validation_errors = error.errors()
            if validation_errors[0]["type"] == "json_invalid":
                context = validation_errors[0].get("ctx") or {}
                detail = context.get("error", ERROR_UNKNOWN)
                raise ScenarioLoadError(ERROR_JSON_SYNTAX.format(detail)) from error
            error_messages = "\n".join(f"- {item['msg']}" for item in validation_errors)
            raise ScenarioLoadError(ERROR_SCENARIO_PARAMETERS.format(error_messages)) from error

        scenario = SimulationScenario(
            name=schema.name,
            bodies=[BodyState(**body.model_dump()) for body in schema.bodies],
        )
        errors = ScenarioValidator.validate_scenario(scenario)
        if errors:
            error_text = "\n".join(f"- {item}" for item in errors)
            raise ScenarioLoadError(ERROR_SCENARIO_LOGIC.format(error_text))
        return scenario

    @staticmethod
    def save(
        scenario: SimulationScenario, file_path: str | Path, indent: int = JSON_INDENT
    ) -> None:
        path = Path(file_path)
        try:
            schema = SimulationScenarioSchema(
                name=scenario.name,
                bodies=[
                    BodyStateSchema(
                        name=body.name,
                        color=body.color,
                        mass=body.mass,
                        radius=body.radius,
                        position=body.position,
                        velocity=body.velocity,
                    )
                    for body in scenario.bodies
                ],
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(schema.model_dump_json(indent=indent), encoding="utf-8")
        except ValidationError as error:
            raise ScenarioSaveError(ERROR_SCENARIO_SAVE.format(error)) from error
        except OSError as error:
            raise ScenarioSaveError(ERROR_FILE_SAVE.format(error)) from error
