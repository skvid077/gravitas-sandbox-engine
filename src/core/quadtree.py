from __future__ import annotations

import math

from config.constants import (
    BH_THETA,
    MIN_DIST_EPSILON,
    SOFTENING_CONSTANT,
    SUBDIVISION_FACTOR,
)


class BoundingBox:
    __slots__ = ("x", "y", "width", "height")

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, x: float, y: float) -> bool:
        return self.x <= x < self.x + self.width and self.y <= y < self.y + self.height

    def subdivide(self) -> tuple[BoundingBox, BoundingBox, BoundingBox, BoundingBox]:
        half_width = self.width / SUBDIVISION_FACTOR
        half_height = self.height / SUBDIVISION_FACTOR
        return (
            BoundingBox(self.x, self.y, half_width, half_height),
            BoundingBox(self.x + half_width, self.y, half_width, half_height),
            BoundingBox(self.x, self.y + half_height, half_width, half_height),
            BoundingBox(self.x + half_width, self.y + half_height, half_width, half_height),
        )


class QuadTreeNode:
    __slots__ = (
        "boundary",
        "body_x",
        "body_y",
        "body_mass",
        "total_mass",
        "center_x",
        "center_y",
        "children",
        "is_leaf",
    )

    def __init__(self, boundary: BoundingBox) -> None:
        self.boundary = boundary
        self.body_x: float | None = None
        self.body_y: float | None = None
        self.body_mass = 0.0
        self.total_mass = 0.0
        self.center_x = 0.0
        self.center_y = 0.0
        self.children: list[QuadTreeNode] | None = None
        self.is_leaf = True

    def insert(self, x: float, y: float, mass: float) -> bool:
        if not self.boundary.contains(x, y):
            return False

        new_total_mass = self.total_mass + mass
        self.center_x = (self.center_x * self.total_mass + x * mass) / new_total_mass
        self.center_y = (self.center_y * self.total_mass + y * mass) / new_total_mass
        self.total_mass = new_total_mass

        if self.is_leaf and self.body_x is None:
            self.body_x = x
            self.body_y = y
            self.body_mass = mass
            return True

        if self.is_leaf:
            self._subdivide()
            if self.body_x is not None and self.body_y is not None:
                self._insert_into_children(self.body_x, self.body_y, self.body_mass)
                self.body_x = None
                self.body_y = None
                self.body_mass = 0.0

        return self._insert_into_children(x, y, mass)

    def _subdivide(self) -> None:
        self.children = [QuadTreeNode(boundary) for boundary in self.boundary.subdivide()]
        self.is_leaf = False

    def _insert_into_children(self, x: float, y: float, mass: float) -> bool:
        if self.children is None:
            return False
        return any(child.insert(x, y, mass) for child in self.children)

    def calculate_acceleration(
        self,
        target_x: float,
        target_y: float,
        gravitational_constant: float,
        theta: float = BH_THETA,
        softening: float = SOFTENING_CONSTANT,
    ) -> tuple[float, float]:
        acceleration = [0.0, 0.0]
        self._accumulate_acceleration(
            target_x, target_y, gravitational_constant, theta, softening, acceleration
        )
        return acceleration[0], acceleration[1]

    def _accumulate_acceleration(
        self,
        target_x: float,
        target_y: float,
        gravitational_constant: float,
        theta: float,
        softening: float,
        acceleration: list[float],
    ) -> None:
        if self.total_mass == 0.0:
            return

        dx = self.center_x - target_x
        dy = self.center_y - target_y
        distance_squared = dx * dx + dy * dy
        distance = math.sqrt(distance_squared)

        if distance < MIN_DIST_EPSILON:
            return

        if self.is_leaf or self.boundary.width / distance < theta:
            scale = (
                gravitational_constant
                * self.total_mass
                / (distance_squared + softening * softening)
                / distance
            )
            acceleration[0] += scale * dx
            acceleration[1] += scale * dy
            return

        if self.children is not None:
            for child in self.children:
                child._accumulate_acceleration(
                    target_x,
                    target_y,
                    gravitational_constant,
                    theta,
                    softening,
                    acceleration,
                )
