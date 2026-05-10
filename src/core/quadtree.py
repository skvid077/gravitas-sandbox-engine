import numpy as np
import numpy.typing as npt
from typing import Optional, List, Tuple
from config.constants import (
    SPACE_DIMENSIONS,
    SUBDIVISION_FACTOR,
    DEFAULT_BH_THETA,
    DEFAULT_SOFTENING,
    MIN_DIST_EPSILON
)


class BoundingBox:
    __slots__ = ('x', 'y', 'width', 'height')

    def __init__(self, x: float, y: float, width: float, height: float) -> None:
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    def contains(self, pos: npt.NDArray[np.float64]) -> bool:
        return bool(self.x <= pos[0] < self.x + self.width and 
                self.y <= pos[1] < self.y + self.height)

    def subdivide(self) -> Tuple['BoundingBox', 'BoundingBox', 'BoundingBox', 'BoundingBox']:
        hw = self.width / SUBDIVISION_FACTOR
        hh = self.height / SUBDIVISION_FACTOR
        return (
            BoundingBox(self.x, self.y, hw, hh),
            BoundingBox(self.x + hw, self.y, hw, hh),
            BoundingBox(self.x, self.y + hh, hw, hh),
            BoundingBox(self.x + hw, self.y + hh, hw, hh)
        )


class QuadTreeNode:
    __slots__ = ('boundary', 'body_pos', 'body_mass', 'total_mass', 
                 'center_of_mass', 'children', 'is_leaf')

    def __init__(self, boundary: BoundingBox) -> None:
        self.boundary = boundary
        self.body_pos: Optional[npt.NDArray[np.float64]] = None
        self.body_mass: float = 0.0
        self.total_mass: float = 0.0
        self.center_of_mass: npt.NDArray[np.float64] = np.zeros(SPACE_DIMENSIONS, dtype=np.float64)
        self.children: Optional[List['QuadTreeNode']] = None
        self.is_leaf: bool = True

    def insert(self, pos: npt.NDArray[np.float64], mass: float) -> bool:
        if not self.boundary.contains(pos):
            return False

        new_total_mass = self.total_mass + mass
        # Обновление центра масс
        self.center_of_mass = (self.center_of_mass * self.total_mass + pos * mass) / new_total_mass
        self.total_mass = new_total_mass

        if self.is_leaf and self.body_pos is None:
            self.body_pos = pos.copy()
            self.body_mass = mass
            return True

        if self.is_leaf:
            self._subdivide()
            if self.body_pos is not None:
                self._insert_into_children(self.body_pos, self.body_mass)
                self.body_pos = None
                self.body_mass = 0.0

        return self._insert_into_children(pos, mass)

    def _subdivide(self) -> None:
        nw, ne, sw, se = self.boundary.subdivide()
        self.children = [
            QuadTreeNode(nw),
            QuadTreeNode(ne),
            QuadTreeNode(sw),
            QuadTreeNode(se)
        ]
        self.is_leaf = False

    def _insert_into_children(self, pos: npt.NDArray[np.float64], mass: float) -> bool:
        if self.children is None:
            return False
        for child in self.children:
            if child.insert(pos, mass):
                return True
        return False


def calculate_bh_acceleration(
    node: QuadTreeNode, 
    target_pos: npt.NDArray[np.float64], 
    G: float, 
    theta: float = DEFAULT_BH_THETA,
    softening: float = DEFAULT_SOFTENING
) -> npt.NDArray[np.float64]:
    acc: npt.NDArray[np.float64] = np.zeros(SPACE_DIMENSIONS, dtype=np.float64)
    
    if node.total_mass == 0.0:
        return acc

    r_vec = node.center_of_mass - target_pos
    dist_sq = float(np.sum(r_vec**2))
    dist = float(np.sqrt(dist_sq))

    if dist < MIN_DIST_EPSILON:
        return acc

    if node.is_leaf or (node.boundary.width / dist < theta):
        magnitude = (G * node.total_mass) / (dist_sq + softening**2)
        acc += magnitude * (r_vec / dist)
    else:
        if node.children is not None:
            for child in node.children:
                acc += calculate_bh_acceleration(child, target_pos, G, theta, softening)

    return acc
