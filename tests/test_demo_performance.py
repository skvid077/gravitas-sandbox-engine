from pathlib import Path
from time import perf_counter

from core.load_json import ScenarioFileService
from core.simulation import Simulation

STEPS = 250
DT = 0.016
MAX_SECONDS = 30.0


def test_demo_scenario_runs_within_time_budget(demo_scenario_path: Path) -> None:
    scenario = ScenarioFileService.load(demo_scenario_path)
    simulation = Simulation(scenario.bodies)

    started = perf_counter()
    for _ in range(STEPS):
        simulation.step(DT)
    elapsed = perf_counter() - started

    assert elapsed < MAX_SECONDS, (
        f"{demo_scenario_path.name} took {elapsed:.3f}s for {STEPS} steps; "
        f"budget is {MAX_SECONDS:.1f}s"
    )
