from collections import deque
from typing import List, Dict, Any, Optional

from config.schemas import BodyState
from config.constants import (
    DEFAULT_MAX_SECONDS_FOR_TIME_MACHINE,
    DEFAULT_FPS_FOR_TIME_MACHINE
)

class TimeMachine:
    def __init__(self, max_seconds: int = DEFAULT_MAX_SECONDS_FOR_TIME_MACHINE, fps: int = DEFAULT_FPS_FOR_TIME_MACHINE) -> None:
        # Прошлое: кольцевой буфер (ограничен по памяти)
        self.past: deque[List[Dict[str, Any]]] = deque(maxlen=max_seconds * fps)
        # Будущее: стек отмотанных кадров
        self.future: List[List[Dict[str, Any]]] = []
        self.is_paused: bool = False

    def save_snapshot(self, bodies: list[BodyState]) -> None:
        """Сохраняет слепок при нормальном ходе времени."""
        if self.is_paused:
            return

        snapshot = [
            {
                "name": b.name,
                "color": b.color,
                "mass": b.mass,
                "radius": b.radius,
                "position": list(b.position),
                "velocity": list(b.velocity)
            }
            for b in bodies
        ]
        self.past.append(snapshot)

    def pause(self) -> None:
        """Ставит машину на паузу, разрешая перемотку."""
        self.is_paused = True

    def scrub_backward(self) -> Optional[List[Dict[str, Any]]]:
        """Отматывает на один кадр назад."""
        if not self.past:
            return None

        snapshot = self.past.pop()
        self.future.append(snapshot)
        return snapshot

    def scrub_forward(self) -> Optional[List[Dict[str, Any]]]:
        """Перематывает на один кадр вперед."""
        if not self.future:
            return None

        snapshot = self.future.pop()
        self.past.append(snapshot)
        return snapshot

    def resume(self) -> None:
        """Возобновляет ход времени. Стирает альтернативное будущее."""
        self.is_paused = False
        self.future.clear()

    # --- НОВЫЕ МЕТОДЫ ДЛЯ ПОЛЗУНКА ---

    def get_total_frames(self) -> int:
        """Возвращает общее количество доступных кадров в истории."""
        return len(self.past) + len(self.future)

    def get_current_frame_index(self) -> int:
        """Возвращает индекс текущего кадра (от 0 до total_frames)."""
        return len(self.past)

    def get_current_snapshot(self) -> Optional[List[Dict[str, Any]]]:
        """Возвращает слепок для текущего момента без изменения времени."""
        if self.past:
            return self.past[-1]
        return None

    def jump_to(self, target_index: int) -> Optional[List[Dict[str, Any]]]:
        """
        Перемещается к конкретному кадру по индексу (от ползунка).
        Автоматически решает, мотать вперед или назад.
        """
        current_index = self.get_current_frame_index()
        
        if target_index < current_index:
            for _ in range(current_index - target_index):
                self.scrub_backward()
        elif target_index > current_index:
            for _ in range(target_index - current_index):
                self.scrub_forward()
                
        return self.get_current_snapshot()
