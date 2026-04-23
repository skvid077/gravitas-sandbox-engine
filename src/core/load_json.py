import json
from pathlib import Path
from typing import Any, Dict
from pydantic import ValidationError

from config.schemas import SimulationScenario
from core.planets_validator import validate_scenario


class ScenarioLoadError(Exception):
    pass


class ScenarioSaveError(Exception):
    pass


def load_scenario_from_file(file_path: str | Path) -> SimulationScenario:
    """Загружает сценарий и проводит полную проверку физики и логики."""
    path = Path(file_path)
    if not path.exists():
        raise ScenarioLoadError(f"Файл не найден: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        # 1. Проверка структуры (типы, наличие полей)
        scenario = SimulationScenario(**data)

        # 2. Глубокая проверка логики (коллизии, уникальность имен)
        errors = validate_scenario(scenario)
        if errors:
            # Если есть ошибки логики, превращаем их в одну строку и кидаем исключение
            error_text = "\n".join([f"- {e}" for e in errors])
            raise ScenarioLoadError(f"Ошибка в логике сценария:\n{error_text}")

        return scenario

    except json.JSONDecodeError as e:
        raise ScenarioLoadError(f"Ошибка синтаксиса JSON (строка {e.lineno}): {e.msg}")
    except ValidationError as e:
        # Ошибки Pydantic (например, масса <= 0)
        error_msgs = "\n".join([f"- {err.get('msg', str(err))}" for err in e.errors()])
        raise ScenarioLoadError(f"Некорректные параметры тел:\n{error_msgs}")
    except ScenarioLoadError:
        # Пробрасываем нашу ошибку валидации дальше
        raise
    except Exception as e:
        raise ScenarioLoadError(f"Не удалось прочитать файл:\n{str(e)}")


def save_scenario_to_file(scenario: SimulationScenario, file_path: str | Path, indent: int = 4) -> None:
    path = Path(file_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        data_dict = scenario.model_dump()
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=indent, ensure_ascii=False)
    except Exception as e:
        raise ScenarioSaveError(f"Не удалось сохранить файл: {str(e)}")
