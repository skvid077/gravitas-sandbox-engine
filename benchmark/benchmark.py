from __future__ import annotations

import argparse
import cProfile
import io
import pstats
import sys
from pathlib import Path
from time import perf_counter
from typing import Any, cast


class BenchmarkRunner:
    BENCHMARK_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = BENCHMARK_DIR.parent
    DEFAULT_STEP_COUNT = 250
    DEFAULT_DT = 0.016
    FUNCTIONS_PER_REPORT = 10

    @staticmethod
    def run_scenario(path: Path, step_count: int) -> float:
        from core.load_json import ScenarioFileService
        from core.simulation import Simulation

        scenario = ScenarioFileService.load(path)
        simulation = Simulation(scenario.bodies)
        started = perf_counter()
        for _ in range(step_count):
            simulation.step(BenchmarkRunner.DEFAULT_DT)
        return perf_counter() - started

    @staticmethod
    def profile_scenario(path: Path, step_count: int, output_path: Path) -> cProfile.Profile:
        profiler = cProfile.Profile()
        profiler.enable()
        BenchmarkRunner.run_scenario(path, step_count)
        profiler.disable()
        profiler.dump_stats(output_path)
        return profiler

    @staticmethod
    def format_profile(profiler: cProfile.Profile | pstats.Stats, limit: int) -> str:
        output = io.StringIO()
        stats = profiler if isinstance(profiler, pstats.Stats) else pstats.Stats(profiler)
        cast(Any, stats).stream = output
        stats.strip_dirs().sort_stats(pstats.SortKey.CUMULATIVE).print_stats(limit)
        return output.getvalue()

    def run(self) -> None:
        sys.path.insert(0, str(self.PROJECT_ROOT / "src"))
        parser = argparse.ArgumentParser(description="Профилирование demo-сценариев симуляции")
        parser.add_argument("--steps", type=int, default=self.DEFAULT_STEP_COUNT)
        args = parser.parse_args()
        if args.steps < 1:
            parser.error("--steps must be positive")

        scenarios = sorted((self.PROJECT_ROOT / "demo").glob("*.json"))
        if not scenarios:
            parser.error("No JSON scenarios found in demo/")

        profile_dir = self.BENCHMARK_DIR / "profiles"
        profile_dir.mkdir(parents=True, exist_ok=True)

        timings: list[tuple[Path, float]] = []
        profilers: list[tuple[Path, cProfile.Profile]] = []
        for path in scenarios:
            elapsed = self.run_scenario(path, args.steps)
            profiler_path = profile_dir / f"{path.stem}.prof"
            profiler = self.profile_scenario(path, args.steps, profiler_path)
            timings.append((path, elapsed))
            profilers.append((path, profiler))

        aggregate_stats = pstats.Stats(profilers[0][1])
        for _, profiler in profilers[1:]:
            aggregate_stats.add(profiler)

        aggregate_profile_path = self.BENCHMARK_DIR / "physics_latest.prof"
        aggregate_report_path = self.BENCHMARK_DIR / "profile_latest.txt"
        aggregate_stats.dump_stats(aggregate_profile_path)

        sections = [
            "Demo scenario timing (without profiler):",
            *(f"  {path.name}: {elapsed:.4f}s ({args.steps} steps)" for path, elapsed in timings),
            f"  Total: {sum(elapsed for _, elapsed in timings):.4f}s",
            "",
            "Individual profiles:",
        ]
        for path, profiler in profilers:
            profiler_path = profile_dir / f"{path.stem}.prof"
            sections.extend(
                [
                    f"\n{path.name} ({args.steps} steps): {profiler_path}",
                    self.format_profile(profiler, self.FUNCTIONS_PER_REPORT),
                ]
            )

        sections.extend(
            [
                "\nAggregate profile (all demo scenarios):",
                self.format_profile(aggregate_stats, 25),
            ]
        )
        report = "\n".join(sections)
        aggregate_report_path.write_text(report, encoding="utf-8")
        print(report)
        print(f"Aggregate profile saved to: {aggregate_profile_path}")
        print(f"Individual profiles saved in: {profile_dir}")
        print(f"Summary saved to: {aggregate_report_path}")


if __name__ == "__main__":
    BenchmarkRunner().run()
