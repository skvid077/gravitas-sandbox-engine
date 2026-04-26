import math
from typing import List
from config.schemas import BodyState
from config.constants import GRAVITY_CONSTANT, SOFTENING_CONSTANT

class PhysicsEngine:
    def __init__(self, g_const: float = GRAVITY_CONSTANT) -> None:
        self.G = g_const
        # Коэффициент упругости отскока (0.8 - заметный отскок, 0.2 - глухой удар)
        self.restitution = 0.8
        self.sub_steps = 128

    def update(self, bodies: List[BodyState], dt: float) -> None:
        """Главный цикл физики."""
        n = len(bodies)
        if n < 2:
            for body in bodies:
                body.position = (
                    body.position[0] + body.velocity[0] * dt,
                    body.position[1] + body.velocity[1] * dt
                )
            return

        sub_dt = dt / self.sub_steps

        for _ in range(self.sub_steps):
            self._apply_gravity_and_integrate(bodies, sub_dt)
            self._resolve_collisions(bodies)

    def _apply_gravity_and_integrate(self, bodies: List[BodyState], dt: float) -> None:
        """Расчет гравитации и перемещение тел (Полунеявный метод Эйлера)."""
        n = len(bodies)
        accelerations: List[List[float]] = [[0.0, 0.0] for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1, n):
                b1 = bodies[i]
                b2 = bodies[j]
                
                dx = b2.position[0] - b1.position[0]
                dy = b2.position[1] - b1.position[1]
                
                dist_sq = dx*dx + dy*dy + SOFTENING_CONSTANT**2
                dist = math.sqrt(dist_sq)
                
                force_mag = self.G / dist_sq
                ax = force_mag * (dx / dist)
                ay = force_mag * (dy / dist)
                
                # Применяем a = F/m
                accelerations[i][0] += ax * b2.mass
                accelerations[i][1] += ay * b2.mass
                accelerations[j][0] -= ax * b1.mass
                accelerations[j][1] -= ay * b1.mass

        # Интегрирование (Semi-Implicit Euler)
        for i, body in enumerate(bodies):
            vx = body.velocity[0] + accelerations[i][0] * dt
            vy = body.velocity[1] + accelerations[i][1] * dt
            body.velocity = (vx, vy)
            
            body.position = (
                body.position[0] + vx * dt,
                body.position[1] + vy * dt
            )

    def _resolve_collisions(self, bodies: List[BodyState]) -> None:
        """Мгновенное расталкивание и обмен импульсами."""
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
                        dist = 0.001
                        dx, dy = 0.001, 0.0

                    nx = dx / dist
                    ny = dy / dist

                    # 1. Позиционная коррекция (чтобы тела не слипались)
                    overlap = min_dist - dist
                    total_mass = b1.mass + b2.mass
                    
                    ratio1 = b2.mass / total_mass
                    ratio2 = b1.mass / total_mass

                    b1.position = (b1.position[0] - nx * overlap * ratio1, 
                                   b1.position[1] - ny * overlap * ratio1)
                    b2.position = (b2.position[0] + nx * overlap * ratio2, 
                                   b2.position[1] + ny * overlap * ratio2)

                    # 2. Коррекция скоростей (импульс)
                    dvx = b2.velocity[0] - b1.velocity[0]
                    dvy = b2.velocity[1] - b1.velocity[1]
                    
                    v_along_normal = dvx * nx + dvy * ny

                    # Если тела уже разлетаются, импульс не применяем
                    if v_along_normal >= 0:
                        continue

                    j_impulse = -(1 + self.restitution) * v_along_normal
                    j_impulse /= (1 / b1.mass + 1 / b2.mass)

                    b1.velocity = (b1.velocity[0] - (j_impulse / b1.mass) * nx,
                                   b1.velocity[1] - (j_impulse / b1.mass) * ny)
                    b2.velocity = (b2.velocity[0] + (j_impulse / b2.mass) * nx,
                                   b2.velocity[1] + (j_impulse / b2.mass) * ny)
