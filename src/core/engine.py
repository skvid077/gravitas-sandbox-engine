import numpy as np
from typing import List, Dict, Tuple, Set
from config.schemas import BodyState

from config.constants import (
    GRAVITY_CONSTANT,
    BH_THETA,
    SOFTENING_CONSTANT,
    MIN_BODIES_FOR_PHYSICS,
    BOUNDING_BOX_PADDING,
    BOUNDING_BOX_SIZE_OFFSET,
    CELL_SIZE_MULTIPLIER,
    MIN_CELL_SIZE
)
from core.quadtree import BoundingBox, QuadTreeNode, calculate_bh_acceleration

class PhysicsEngine:
    """
    Высокопроизводительное физическое ядро симуляции.
    
    Оптимизации:
    1. Гравитация: Алгоритм Барнса-Хата (O(N log N)).
    2. Коллизии: Пространственное хеширование (O(N)).
    3. Вычисления: Векторизация через NumPy (матричные операции).
    """

    def __init__(self, g_const: float = GRAVITY_CONSTANT) -> None:
        self.G = g_const

    def update(self, bodies: list[BodyState], dt: float) -> None:
        """
        Главный цикл обновления физики.
        """
        if not bodies:
            return

        if len(bodies) < MIN_BODIES_FOR_PHYSICS:
            self._apply_velocity(bodies, dt)
            return

        # 1. Подготовка данных: выгружаем позиции в матрицу для поиска границ и построения дерева
        positions_matrix = np.array([b.position for b in bodies], dtype=np.float64)
        
        # 2. Построение QuadTree
        min_coords = np.min(positions_matrix, axis=0)
        max_coords = np.max(positions_matrix, axis=0)
        
        size = np.max(max_coords - min_coords) + BOUNDING_BOX_SIZE_OFFSET
        root_boundary = BoundingBox(
            x=float(min_coords[0] - BOUNDING_BOX_PADDING),
            y=float(min_coords[1] - BOUNDING_BOX_PADDING),
            width=float(size),
            height=float(size)
        )
        root_node = QuadTreeNode(root_boundary)

        for i, body in enumerate(bodies):
            root_node.insert(positions_matrix[i], body.mass)

        # 3. Расчет ускорений и обновление скоростей
        # Используем пред-вычисленную матрицу позиций, чтобы не создавать массивы в цикле
        for i, body in enumerate(bodies):
            acceleration = calculate_bh_acceleration(
                node=root_node,
                target_pos=positions_matrix[i],
                G=self.G,
                theta=BH_THETA,
                softening=SOFTENING_CONSTANT
            )
            
            # Обновляем скорость в модели (Pydantic принимает list)
            vel_arr = np.array(body.velocity, dtype=np.float64)
            vel_arr += acceleration * dt
            body.velocity = vel_arr.tolist()

        # 4. Обновление позиций (Векторизовано)
        self._apply_velocity(bodies, dt)

        # 5. Обработка столкновений (O(N))
        self._handle_collisions(bodies)

    def _apply_velocity(self, bodies: list[BodyState], dt: float) -> None:
        """Обновление позиций через матричные операции NumPy."""
        if not bodies:
            return

        pos_mat = np.array([b.position for b in bodies], dtype=np.float64)
        vel_mat = np.array([b.velocity for b in bodies], dtype=np.float64)
        
        # Матричное сложение на уровне C
        pos_mat += vel_mat * dt
        
        # Запись результатов обратно в модели
        for i, body in enumerate(bodies):
            body.position = pos_mat[i].tolist()

    def _handle_collisions(self, bodies: list[BodyState]) -> None:
        """
        Разрешение неупругих столкновений (слияний) за O(N).
        Использует пространственное хеширование (Uniform Grid).
        """
        if len(bodies) < MIN_BODIES_FOR_PHYSICS:
            return

        # Определяем размер ячейки сетки на основе самого крупного объекта
        max_r = max(b.radius for b in bodies)
        cell_size = max_r * CELL_SIZE_MULTIPLIER
        if cell_size < MIN_CELL_SIZE:
            cell_size = MIN_CELL_SIZE

        # Broad-phase: распределение по ячейкам
        grid: Dict[Tuple[int, int], List[BodyState]] = {}
        for body in bodies:
            cell = (int(body.position[0] // cell_size), int(body.position[1] // cell_size))
            if cell not in grid:
                grid[cell] = []
            grid[cell].append(body)

        to_remove_ids: Set[int] = set()

        # Narrow-phase: проверка пересечений с соседями
        for body_a in bodies:
            b_a_id = id(body_a)
            if b_a_id in to_remove_ids:
                continue

            cx, cy = int(body_a.position[0] // cell_size), int(body_a.position[1] // cell_size)

            for dx in range(-1, 2):
                for dy in range(-1, 2):
                    cell = (cx + dx, cy + dy)
                    if cell not in grid:
                        continue

                    for body_b in grid[cell]:
                        b_b_id = id(body_b)
                        if body_a is body_b or b_b_id in to_remove_ids:
                            continue

                        pos_a = np.array(body_a.position, dtype=np.float64)
                        pos_b = np.array(body_b.position, dtype=np.float64)
                        
                        dist_sq = np.sum((pos_a - pos_b)**2)
                        min_dist = body_a.radius + body_b.radius

                        if dist_sq < min_dist**2:
                            # Физика слияния (Закон сохранения массы и импульса)
                            m_a, m_b = body_a.mass, body_b.mass
                            total_m = m_a + m_b
                            
                            vel_a = np.array(body_a.velocity, dtype=np.float64)
                            vel_b = np.array(body_b.velocity, dtype=np.float64)
                            
                            # Новые параметры для body_a
                            new_vel = (m_a * vel_a + m_b * vel_b) / total_m
                            new_pos = (m_a * pos_a + m_b * pos_b) / total_m
                            new_radius = np.sqrt(body_a.radius**2 + body_b.radius**2)

                            body_a.position = new_pos.tolist()
                            body_a.velocity = new_vel.tolist()
                            body_a.mass = float(total_m)
                            body_a.radius = float(new_radius)

                            to_remove_ids.add(b_b_id)

        # Удаляем "съеденные" объекты из основного списка
        if to_remove_ids:
            bodies[:] = [b for b in bodies if id(b) not in to_remove_ids]
