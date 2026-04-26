import math
from typing import List
from config.schemas import BodyState
from config.constants import (
    GRAVITY_CONSTANT,
    SOFTENING_CONSTANT,
    DEFAULT_RESTITUTION,
    DEFAULT_SUB_STEPS
)


class PhysicsEngine:
    """
    Физическое ядро симуляции.
    
    Реализует:
    1. Расчет гравитационного взаимодействия N тел.
    2. Интегрирование скоростей и позиций (Semi-Implicit Euler).
    3. Разрешение упругих столкновений с позиционной коррекцией.
    """

    def __init__(self, g_const: float = GRAVITY_CONSTANT) -> None:
        """
        Инициализирует движок.

        Args:
            g_const (float): Гравитационная постоянная.
        """
        self.G = g_const
        self.restitution = DEFAULT_RESTITUTION
        self.sub_steps = DEFAULT_SUB_STEPS

    def update(self, bodies: List[BodyState], dt: float) -> None:
        """
        Продвигает физическое состояние всех тел на шаг dt.
        Использует суб-шаги для предотвращения 'пролетания' тел друг сквозь друга.

        Args:
            bodies (List[BodyState]): Список тел для симуляции.
            dt (float): Общий шаг времени.
        """
        n = len(bodies)
        if n == 0:
            return
            
        if n < 2:
            # Если тело одно, просто двигаем его по инерции
            body = bodies[0]
            body.position = (
                body.position[0] + body.velocity[0] * dt,
                body.position[1] + body.velocity[1] * dt
            )
            return

        # Делим временной шаг на части для точности вычислений
        sub_dt = dt / self.sub_steps

        for _ in range(self.sub_steps):
            self._apply_gravity_and_integrate(bodies, sub_dt)
            self._resolve_collisions(bodies)

    def _apply_gravity_and_integrate(self, bodies: List[BodyState], dt: float) -> None:
        """
        Вычисляет силы гравитации между всеми парами тел и обновляет их скорости и координаты.
        Применяет SOFTENING_CONSTANT для избежания бесконечных сил при сближении.

        Args:
            bodies (List[BodyState]): Список тел.
            dt (float): Шаг времени суб-итерации.
        """
        n = len(bodies)
        # Инициализируем массив ускорений для каждого тела [ax, ay]
        accelerations: List[List[float]] = [[0.0, 0.0] for _ in range(n)]
        
        # 1. Расчет ускорений (O(N^2))
        for i in range(n):
            for j in range(i + 1, n):
                b1 = bodies[i]
                b2 = bodies[j]
                
                dx = b2.position[0] - b1.position[0]
                dy = b2.position[1] - b1.position[1]
                
                # Квадрат расстояния с учетом смягчения (softening)
                dist_sq = dx*dx + dy*dy + SOFTENING_CONSTANT**2
                dist = math.sqrt(dist_sq)
                
                # Величина силы: F = G * (m1 * m2) / r^2 -> Ускорение: a = G * m_other / r^2
                force_mag = self.G / dist_sq
                ax = force_mag * (dx / dist)
                ay = force_mag * (dy / dist)
                
                # Вектор ускорения направлен к другому телу
                accelerations[i][0] += ax * b2.mass
                accelerations[i][1] += ay * b2.mass
                accelerations[j][0] -= ax * b1.mass
                accelerations[j][1] -= ay * b1.mass

        # 2. Интегрирование (Semi-Implicit Euler)
        for i, body in enumerate(bodies):
            # Сначала обновляем скорость (V_new = V_old + a * dt)
            vx = body.velocity[0] + accelerations[i][0] * dt
            vy = body.velocity[1] + accelerations[i][1] * dt
            body.velocity = (vx, vy)
            
            # Затем обновляем позицию (P_new = P_old + V_new * dt)
            body.position = (
                body.position[0] + vx * dt,
                body.position[1] + vy * dt
            )

    def _resolve_collisions(self, bodies: List[BodyState]) -> None:
        """
        Проверяет пересечения тел и разрешает их через мгновенную коррекцию 
        позиций (расталкивание) и импульсный отскок.

        Args:
            bodies (List[BodyState]): Список тел.
        """
        n = len(bodies)
        for i in range(n):
            for j in range(i + 1, n):
                b1 = bodies[i]
                b2 = bodies[j]

                dx = b2.position[0] - b1.position[0]
                dy = b2.position[1] - b1.position[1]
                dist_sq = dx*dx + dy*dy
                min_dist = b1.radius + b2.radius

                if dist_sq < min_dist*min_dist:
                    dist = math.sqrt(dist_sq)
                    if dist == 0.0:
                        # Предотвращение деления на 0 при полном совпадении координат
                        dist = 0.001
                        dx, dy = 0.001, 0.0

                    nx = dx / dist
                    ny = dy / dist

                    # --- 1. Позиционная коррекция (выталкивание тел друг из друга) ---
                    overlap = min_dist - dist
                    total_mass = b1.mass + b2.mass
                    
                    # Тяжелое тело двигается меньше, легкое - больше
                    ratio1 = b2.mass / total_mass
                    ratio2 = b1.mass / total_mass

                    b1.position = (b1.position[0] - nx * overlap * ratio1, 
                                   b1.position[1] - ny * overlap * ratio1)
                    b2.position = (b2.position[0] + nx * overlap * ratio2, 
                                   b2.position[1] + ny * overlap * ratio2)

                    # --- 2. Коррекция скоростей (импульсный отскок) ---
                    dvx = b2.velocity[0] - b1.velocity[0]
                    dvy = b2.velocity[1] - b1.velocity[1]
                    
                    # Проекция относительной скорости на нормаль столкновения
                    v_along_normal = dvx * nx + dvy * ny

                    # Если тела уже разлетаются, импульс не применяем
                    if v_along_normal >= 0:
                        continue

                    # Расчет величины импульса J
                    j_impulse = -(1 + self.restitution) * v_along_normal
                    j_impulse /= (1 / b1.mass + 1 / b2.mass)

                    # Применяем импульс к скоростям
                    b1.velocity = (b1.velocity[0] - (j_impulse / b1.mass) * nx,
                                   b1.velocity[1] - (j_impulse / b1.mass) * ny)
                    b2.velocity = (b2.velocity[0] + (j_impulse / b2.mass) * nx,
                                   b2.velocity[1] + (j_impulse / b2.mass) * ny)
