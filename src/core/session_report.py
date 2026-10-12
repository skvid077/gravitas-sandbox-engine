import logging
from datetime import datetime
from pathlib import Path
from time import perf_counter

from config.constants import DEFAULT_SCENARIO_NAME, GRAVITY_CONSTANT
from config.constants.report_constants import (
    REPORT_APPLICATION_DURATION,
    REPORT_BODIES,
    REPORT_COLLISION_COUNT,
    REPORT_COLLISION_EVENT,
    REPORT_COLLISION_MASS,
    REPORT_CREATED_BODIES,
    REPORT_DATETIME_FORMAT,
    REPORT_DURATION_HOURS,
    REPORT_DURATION_MINUTES,
    REPORT_DURATION_SECONDS,
    REPORT_ENDED_AT,
    REPORT_FILENAME_FORMAT,
    REPORT_FINAL_GRAVITY,
    REPORT_FINAL_TIME_SCALE,
    REPORT_INITIAL_BODIES,
    REPORT_INITIAL_GRAVITY,
    REPORT_PARAMETERS,
    REPORT_REMAINING_BODIES,
    REPORT_REMOVED_BODIES,
    REPORT_SAVE_LOG,
    REPORT_SCENARIO,
    REPORT_SIMULATION_DURATION,
    REPORT_STARTED_AT,
    REPORT_TITLE,
)
from core.events import CollisionEvent

logger = logging.getLogger(__name__)


class SessionReport:
    def __init__(self, reports_directory: Path | None = None) -> None:
        self.started_at = datetime.now().astimezone()
        self._started_at_monotonic = perf_counter()
        self._reports_directory = (
            reports_directory or Path(__file__).resolve().parents[2] / "reports"
        )
        self.scenario_name = DEFAULT_SCENARIO_NAME
        self.initial_body_count = 0
        self.created_body_count = 0
        self.removed_body_count = 0
        self.initial_gravity = GRAVITY_CONSTANT
        self.simulated_seconds = 0.0
        self.collisions: list[CollisionEvent] = []
        self._saved_path: Path | None = None
        self._save_attempted = False

    def set_initial_state(
        self, scenario_name: str, body_count: int, gravitational_constant: float
    ) -> None:
        self.scenario_name = scenario_name
        self.initial_body_count = body_count
        self.initial_gravity = gravitational_constant

    def record_created_body(self) -> None:
        self.created_body_count += 1

    def record_removed_bodies(self, count: int) -> None:
        self.removed_body_count += count

    def record_simulation_step(self, elapsed_seconds: float) -> None:
        self.simulated_seconds += elapsed_seconds

    def record_collisions(self, events: list[CollisionEvent]) -> None:
        self.collisions.extend(events)

    def save(
        self,
        final_body_count: int,
        final_gravity: float,
        final_time_scale: float,
    ) -> Path | None:
        if self._saved_path is not None:
            return self._saved_path
        if self._save_attempted:
            return None

        self._save_attempted = True
        ended_at = datetime.now().astimezone()
        wall_seconds = perf_counter() - self._started_at_monotonic
        report_text = self._render(
            ended_at,
            wall_seconds,
            final_body_count,
            final_gravity,
            final_time_scale,
        )
        file_name = self.started_at.strftime(REPORT_FILENAME_FORMAT)
        report_path = self._reports_directory / file_name
        try:
            self._reports_directory.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_text, encoding="utf-8")
        except OSError:
            logger.exception(REPORT_SAVE_LOG, report_path)
            return None
        self._saved_path = report_path
        return self._saved_path

    def _render(
        self,
        ended_at: datetime,
        wall_seconds: float,
        final_body_count: int,
        final_gravity: float,
        final_time_scale: float,
    ) -> str:
        lines = [
            REPORT_TITLE,
            REPORT_SCENARIO.format(self.scenario_name),
            REPORT_STARTED_AT.format(self.started_at.strftime(REPORT_DATETIME_FORMAT)),
            REPORT_ENDED_AT.format(ended_at.strftime(REPORT_DATETIME_FORMAT)),
            REPORT_APPLICATION_DURATION.format(self._format_duration(wall_seconds)),
            REPORT_SIMULATION_DURATION.format(self._format_duration(self.simulated_seconds)),
            "",
            REPORT_BODIES,
            REPORT_INITIAL_BODIES.format(self.initial_body_count),
            REPORT_CREATED_BODIES.format(self.created_body_count),
            REPORT_REMOVED_BODIES.format(self.removed_body_count),
            REPORT_REMAINING_BODIES.format(final_body_count),
            "",
            REPORT_COLLISION_COUNT.format(len(self.collisions)),
        ]
        lines.extend(self._render_collisions())
        lines.extend(
            [
                "",
                REPORT_PARAMETERS,
                REPORT_INITIAL_GRAVITY.format(self.initial_gravity),
                REPORT_FINAL_GRAVITY.format(final_gravity),
                REPORT_FINAL_TIME_SCALE.format(final_time_scale),
            ]
        )
        return "\n".join(lines) + "\n"

    def _render_collisions(self) -> list[str]:
        lines: list[str] = []
        for event in self.collisions:
            time_text = self._format_duration(event.simulation_time)
            lines.extend(
                [
                    REPORT_COLLISION_EVENT.format(
                        time_text,
                        event.first_body_name,
                        event.second_body_name,
                        event.result_body_name,
                    ),
                    REPORT_COLLISION_MASS.format(event.result_mass),
                ]
            )
        return lines

    @staticmethod
    def _format_duration(seconds: float) -> str:
        total_seconds = max(0, int(seconds))
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds_part = divmod(remainder, 60)
        if hours:
            return REPORT_DURATION_HOURS.format(hours, minutes, seconds_part)
        if minutes:
            return REPORT_DURATION_MINUTES.format(minutes, seconds_part)
        return REPORT_DURATION_SECONDS.format(seconds_part)
