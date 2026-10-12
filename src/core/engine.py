import math

import numpy as np

from config.constants import (
    BH_THETA,
    BOUNDING_BOX_PADDING,
    BOUNDING_BOX_SIZE_OFFSET,
    CELL_SIZE_MULTIPLIER,
    ERROR_INVALID_GRAVITATIONAL_CONSTANT,
    GRAVITY_CONSTANT,
    MIN_BODIES_FOR_PHYSICS,
    MIN_CELL_SIZE,
    SOFTENING_CONSTANT,
)
from config.models import BodyState
from core.events import CollisionEvent
from core.quadtree import BoundingBox, QuadTreeNode
from core.spatial_grid import SpatialGrid


class PhysicsEngine:
    def __init__(self, g_const: float = GRAVITY_CONSTANT) -> None:
        self.gravitational_constant = g_const

    @property
    def gravitational_constant(self) -> float:
        return self._gravitational_constant

    @gravitational_constant.setter
    def gravitational_constant(self, value: float) -> None:
        if not math.isfinite(value) or value < 0:
            raise ValueError(ERROR_INVALID_GRAVITATIONAL_CONSTANT)
        self._gravitational_constant = value

    def update(
        self, bodies: list[BodyState], dt: float, simulation_time: float = 0.0
    ) -> list[CollisionEvent]:
        if not bodies:
            return []

        if len(bodies) < MIN_BODIES_FOR_PHYSICS:
            PhysicsEngine._apply_velocity(bodies, dt)
            return []
        positions_matrix = np.array([b.position for b in bodies], dtype=np.float64)
        min_coordinates = np.min(positions_matrix, axis=0)
        max_coordinates = np.max(positions_matrix, axis=0)

        size = np.max(max_coordinates - min_coordinates) + BOUNDING_BOX_SIZE_OFFSET
        root_boundary = BoundingBox(
            x=float(min_coordinates[0] - BOUNDING_BOX_PADDING),
            y=float(min_coordinates[1] - BOUNDING_BOX_PADDING),
            width=float(size),
            height=float(size),
        )
        root_node = QuadTreeNode(root_boundary)

        for i, body in enumerate(bodies):
            root_node.insert(
                float(positions_matrix[i, 0]),
                float(positions_matrix[i, 1]),
                body.mass,
            )
        for i, body in enumerate(bodies):
            acceleration_x, acceleration_y = root_node.calculate_acceleration(
                target_x=float(positions_matrix[i, 0]),
                target_y=float(positions_matrix[i, 1]),
                gravitational_constant=self.gravitational_constant,
                theta=BH_THETA,
                softening=SOFTENING_CONSTANT,
            )
            body.velocity = (
                body.velocity[0] + acceleration_x * dt,
                body.velocity[1] + acceleration_y * dt,
            )
        PhysicsEngine._apply_velocity(bodies, dt)
        return PhysicsEngine._handle_collisions(bodies, simulation_time)

    @staticmethod
    def _apply_velocity(bodies: list[BodyState], dt: float) -> None:
        pos_mat = np.array([b.position for b in bodies], dtype=np.float64)
        vel_mat = np.array([b.velocity for b in bodies], dtype=np.float64)
        pos_mat += vel_mat * dt
        for i, body in enumerate(bodies):
            body.position = (float(pos_mat[i, 0]), float(pos_mat[i, 1]))

    @staticmethod
    def _handle_collisions(bodies: list[BodyState], simulation_time: float) -> list[CollisionEvent]:
        max_r = max(b.radius for b in bodies)
        cell_size = max(max_r * CELL_SIZE_MULTIPLIER, MIN_CELL_SIZE)
        grid = SpatialGrid(cell_size)
        for body in bodies:
            grid.add(body)

        to_remove_ids: set[int] = set()
        collisions: list[CollisionEvent] = []
        for body_a in bodies:
            b_a_id = id(body_a)
            if b_a_id in to_remove_ids:
                continue

            for body_b in grid.nearby(body_a):
                b_b_id = id(body_b)
                if body_a is body_b or b_b_id in to_remove_ids:
                    continue

                distance_x = body_a.position[0] - body_b.position[0]
                distance_y = body_a.position[1] - body_b.position[1]
                dist_sq = distance_x * distance_x + distance_y * distance_y
                min_dist = body_a.radius + body_b.radius

                if dist_sq < min_dist**2:
                    m_a, m_b = body_a.mass, body_b.mass
                    total_m = m_a + m_b
                    body_a.velocity = (
                        (m_a * body_a.velocity[0] + m_b * body_b.velocity[0]) / total_m,
                        (m_a * body_a.velocity[1] + m_b * body_b.velocity[1]) / total_m,
                    )
                    body_a.position = (
                        (m_a * body_a.position[0] + m_b * body_b.position[0]) / total_m,
                        (m_a * body_a.position[1] + m_b * body_b.position[1]) / total_m,
                    )
                    new_radius = math.sqrt(body_a.radius**2 + body_b.radius**2)

                    body_a.mass = float(total_m)
                    body_a.radius = float(new_radius)

                    to_remove_ids.add(b_b_id)
                    collisions.append(
                        CollisionEvent(
                            simulation_time=simulation_time,
                            first_body_name=body_a.name,
                            second_body_name=body_b.name,
                            result_body_name=body_a.name,
                            result_mass=body_a.mass,
                        )
                    )
        if to_remove_ids:
            bodies[:] = [b for b in bodies if id(b) not in to_remove_ids]
        return collisions
