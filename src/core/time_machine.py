from __future__ import annotations

from dataclasses import dataclass

from config.constants import (
    DEFAULT_FPS_FOR_TIME_MACHINE,
    DEFAULT_MAX_SECONDS_FOR_TIME_MACHINE,
)
from config.models import BodyState


@dataclass(frozen=True, slots=True)
class BodySnapshot:
    name: str
    color: str
    mass: float
    radius: float
    position: tuple[float, float]
    velocity: tuple[float, float]

    @classmethod
    def from_body(cls, body: BodyState) -> BodySnapshot:
        return cls(
            name=body.name,
            color=body.color,
            mass=body.mass,
            radius=body.radius,
            position=body.position,
            velocity=body.velocity,
        )

    def to_body_state(self) -> BodyState:
        return BodyState(
            name=self.name,
            color=self.color,
            mass=self.mass,
            radius=self.radius,
            position=self.position,
            velocity=self.velocity,
        )


class TimeMachine:
    def __init__(
        self,
        max_seconds: int = DEFAULT_MAX_SECONDS_FOR_TIME_MACHINE,
        fps: int = DEFAULT_FPS_FOR_TIME_MACHINE,
    ) -> None:
        self._max_frames = max(1, max_seconds * fps)
        self._frames: list[list[BodySnapshot]] = []
        self._cursor = -1
        self.is_paused = False

    def save_snapshot(self, bodies: list[BodyState]) -> None:
        if self.is_paused:
            return
        self._append_snapshot(bodies)

    def record_change(self, bodies: list[BodyState]) -> None:
        self._append_snapshot(bodies)

    def _append_snapshot(self, bodies: list[BodyState]) -> None:
        if self._cursor < len(self._frames) - 1:
            del self._frames[self._cursor + 1 :]

        self._frames.append(self._make_snapshot(bodies))
        if len(self._frames) > self._max_frames:
            self._frames.pop(0)

        self._cursor = len(self._frames) - 1

    def reset(self, bodies: list[BodyState]) -> None:
        self._frames = [self._make_snapshot(bodies)]
        self._cursor = 0

    def pause(self) -> None:
        self.is_paused = True

    def resume(self) -> None:
        if self._cursor >= 0:
            del self._frames[self._cursor + 1 :]
        self.is_paused = False

    def get_total_frames(self) -> int:
        return max(0, len(self._frames) - 1)

    def get_current_frame_index(self) -> int:
        return max(0, self._cursor)

    def get_current_snapshot(self) -> list[BodySnapshot] | None:
        if self._cursor < 0:
            return None
        return self._frames[self._cursor].copy()

    def scrub_backward(self) -> list[BodySnapshot] | None:
        if self._cursor <= 0:
            return None
        self._cursor -= 1
        return self.get_current_snapshot()

    def scrub_forward(self) -> list[BodySnapshot] | None:
        if self._cursor >= len(self._frames) - 1:
            return None
        self._cursor += 1
        return self.get_current_snapshot()

    def jump_to(self, target_index: int) -> list[BodySnapshot] | None:
        if not self._frames:
            return None
        self._cursor = min(max(target_index, 0), len(self._frames) - 1)
        return self.get_current_snapshot()

    @staticmethod
    def _make_snapshot(bodies: list[BodyState]) -> list[BodySnapshot]:
        return [BodySnapshot.from_body(body) for body in bodies]
