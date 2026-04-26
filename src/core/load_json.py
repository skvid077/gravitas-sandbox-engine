import json
from pathlib import Path
from typing import Any, Dict, List, Union
from pydantic import ValidationError

from config.schemas import SimulationScenario
from core.planets_validator import validate_scenario


class ScenarioLoadError(Exception):
    """Исключение, возникающее при ошибках загрузки или валидации сценария."""
    pass


class ScenarioSaveError(Exception):
    """Исключение, возникающее при ошибках записи сценария на диск."""
    pass


def load_scenario_from_file(file_path: Union[str, Path]) -> SimulationScenario:
    """
    Загружает сценарий из JSON-файла, проводит проверку структуры (Pydantic)
    и глубокую валидацию физической логики (коллизии, параметры).

    Args:
        file_path (Union[str, Path]): Путь к файлу сценария.

    Returns:
        SimulationScenario: Валидированный объект сценария.

    Raises:
        ScenarioLoadError: Если файл не найден, поврежден или нарушает логику симуляции.
    """
    path = Path(file_path)
    if not path.exists():
        raise ScenarioLoadError(f"Файл не найден: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data: Dict[str, Any] = json.load(f)
        
        # 1. Проверка структуры через Pydantic (типы данных, обязательные поля)
        scenario = SimulationScenario(**data)

        # 2. Глубокая проверка логики (отсутствие наложений, уникальность имен)
        errors: List[str] = validate_scenario(scenario)
        if errors:
            error_text = "\n".join([f"- {e}" for e in errors])
            raise ScenarioLoadError(f"Ошибка в логике сценария:\n{error_text}")

        return scenario

    except json.JSONDecodeError as e:
        raise ScenarioLoadError(f"Ошибка синтаксиса JSON (строка {e.lineno}): {e.msg}")
    except ValidationError as e:
        # Извлекаем понятные сообщения об ошибках из Pydantic
        error_msgs = "\n".join([f"- {err['msg']}" for err in e.errors()])
        raise ScenarioLoadError(f"Некорректные параметры тел:\n{error_msgs}")
    except ScenarioLoadError:
        # Пробрасываем уже сформированную ошибку валидации
        raise
    except Exception as e:
        raise ScenarioLoadError(f"Не удалось прочитать файл:\n{str(e)}")


def save_scenario_to_file(scenario: SimulationScenario, file_path: Union[str, Path], indent: int = 4) -> None:
    """
    Сериализует объект сценария в JSON и сохраняет его на диск.

    Args:
        scenario (SimulationScenario): Объект сценария для сохранения.
        file_path (Union[str, Path]): Путь сохранения.
        indent (int, optional): Отступ в JSON-файле. По умолчанию 4.

    Raises:
        ScenarioSaveError: Если не удалось создать директорию или записать файл.
    """
    path = Path(file_path)
    try:
        # Создаем папки, если они отсутствуют в пути
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Преобразуем модель Pydantic в словарь
        data_dict = scenario.model_dump()
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data_dict, f, indent=indent, ensure_ascii=False)
            
    except Exception as e:
        raise ScenarioSaveError(f"Не удалось сохранить файл: {str(e)}")
