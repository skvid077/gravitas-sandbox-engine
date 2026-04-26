from typing import List, Optional, Set
from config.schemas import BodyState, SimulationScenario
from config.constants import (
    ERROR_EMPTY_NAME,
    ERROR_MASS_ZERO,
    ERROR_RADIUS_ZERO,
    ERROR_DUPLICATE_NAME,
    ERROR_COLLISION
)

def check_name_uniqueness(name: str, planets: List[BodyState], exclude_idx: Optional[int] = None) -> bool:
    """
    Проверяет уникальность имени среди списка планет.

    Args:
        name (str): Имя для проверки.
        planets (List[BodyState]): Список существующих тел.
        exclude_idx (Optional[int]): Индекс тела, которое нужно игнорировать (при редактировании).

    Returns:
        bool: True, если имя уникально, иначе False.
    """
    clean_name = name.strip()
    if not clean_name:
        return False

    for i, p in enumerate(planets):
        if exclude_idx is not None and i == exclude_idx:
            continue
        if p.name == clean_name:
            return False
    return True


def check_collision(new_body: BodyState, planets: List[BodyState], exclude_idx: Optional[int] = None) -> Optional[str]:
    """
    Проверяет, не пересекается ли геометрически новое тело с существующими.

    Args:
        new_body (BodyState): Тело, позиция которого проверяется.
        planets (List[BodyState]): Список тел для проверки наложения.
        exclude_idx (Optional[int]): Индекс тела, которое нужно игнорировать.

    Returns:
        Optional[str]: Имя первого найденного тела, с которым произошло наложение, или None.
    """
    for i, other in enumerate(planets):
        if exclude_idx is not None and i == exclude_idx:
            continue
            
        dx: float = new_body.position[0] - other.position[0]
        dy: float = new_body.position[1] - other.position[1]
        
        # Оптимизация: работаем с квадратами расстояний, чтобы избежать вычисления sqrt
        dist_sq: float = dx * dx + dy * dy
        min_dist: float = new_body.radius + other.radius
        
        if dist_sq < min_dist * min_dist:
            return other.name
    return None


def validate_body_params(body: BodyState) -> Optional[str]:
    """
    Проверяет физическую и логическую корректность параметров отдельного тела.

    Args:
        body (BodyState): Объект тела для проверки.

    Returns:
        Optional[str]: Текст ошибки или None, если параметры валидны.
    """
    if not body.name.strip():
        return ERROR_EMPTY_NAME
    if body.mass <= 0:
        return ERROR_MASS_ZERO.format(body.mass)
    if body.radius <= 0:
        return ERROR_RADIUS_ZERO.format(body.radius)
    return None


def validate_scenario(scenario: SimulationScenario) -> List[str]:
    """
    Выполняет комплексную проверку всего сценария симуляции:
    параметры тел, уникальность имен и отсутствие начальных коллизий.

    Args:
        scenario (SimulationScenario): Сценарий для проверки.

    Returns:
        List[str]: Список всех найденных ошибок. Пустой список означает успешную валидацию.
    """
    errors: List[str] = []
    seen_names: Set[str] = set()
    
    for i, body in enumerate(scenario.bodies):
        # 1. Проверка физических параметров
        p_error = validate_body_params(body)
        if p_error:
            errors.append(f"Тело #{i} ('{body.name}'): {p_error}")
        
        # 2. Проверка уникальности имен
        if body.name in seen_names:
            errors.append(ERROR_DUPLICATE_NAME.format(body.name))
        seen_names.add(body.name)
        
        # 3. Проверка наложений (сравнение только с уже проверенными телами)
        # Это предотвращает дублирование ошибок (A на B и B на A)
        conflict = check_collision(body, scenario.bodies[:i])
        if conflict:
            errors.append(ERROR_COLLISION.format(body.name, conflict))
            
    return errors
