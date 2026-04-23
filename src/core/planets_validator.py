from typing import List, Optional
from config.schemas import BodyState, SimulationScenario


def check_name_uniqueness(name: str, planets: List[BodyState], exclude_idx: Optional[int] = None) -> bool:
    """Проверяет, нет ли уже тела с таким именем."""
    for i, p in enumerate(planets):
        if exclude_idx is not None and i == exclude_idx:
            continue
        if p.name == name:
            return False
    return True

def check_collision(new_body: BodyState, planets: List[BodyState], exclude_idx: Optional[int] = None) -> Optional[str]:
    """Проверяет, не накладывается ли новое тело на существующие."""
    for i, other in enumerate(planets):
        if exclude_idx is not None and i == exclude_idx:
            continue
            
        dx = new_body.position[0] - other.position[0]
        dy = new_body.position[1] - other.position[1]
        dist_sq = dx*dx + dy*dy
        min_dist = new_body.radius + other.radius
        
        if dist_sq < min_dist * min_dist:
            return other.name
    return None

def validate_body_params(body: BodyState) -> Optional[str]:
    """
    Проверяет физическую корректность параметров тела.
    Возвращает текст ошибки или None, если всё Ок.
    """
    if body.mass <= 0:
        return f"Масса должна быть больше нуля."
    if body.radius <= 0:
        return f"Радиус должен быть больше нуля."
    return None



def validate_scenario(scenario: SimulationScenario) -> list[str]:
    """Комплексная проверка сценария."""
    errors = []
    seen_names = set()
    
    for i, body in enumerate(scenario.bodies):
        # 1. Проверка параметров (масса/радиус > 0)
        p_error = validate_body_params(body)
        if p_error:
            errors.append(p_error)
        
        # 2. Проверка уникальности имен
        if body.name in seen_names:
            errors.append(f"Дубликат имени: '{body.name}'")
        seen_names.add(body.name)
        
        # 3. Проверка наложений тел
        # Проверяем текущее тело со всеми ПРЕДЫДУЩИМИ телами в списке
        conflict = check_collision(body, scenario.bodies[:i])
        if conflict:
            errors.append(f"Тело '{body.name}' накладывается на '{conflict}'")
            
    return errors
