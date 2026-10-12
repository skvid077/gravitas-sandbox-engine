from collections.abc import Iterator

from config.models import BodyState


class SpatialGrid:
    def __init__(self, cell_size: float) -> None:
        self._cell_size = cell_size
        self._cells: dict[tuple[int, int], list[BodyState]] = {}

    def add(self, body: BodyState) -> None:
        cell = self._cell_for(body.position)
        self._cells.setdefault(cell, []).append(body)

    def nearby(self, body: BodyState) -> Iterator[BodyState]:
        cell_x, cell_y = self._cell_for(body.position)
        for offset_x in range(-1, 2):
            for offset_y in range(-1, 2):
                yield from self._cells.get((cell_x + offset_x, cell_y + offset_y), ())

    def _cell_for(self, position: tuple[float, float]) -> tuple[int, int]:
        return (
            int(position[0] // self._cell_size),
            int(position[1] // self._cell_size),
        )
