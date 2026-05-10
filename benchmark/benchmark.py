import cProfile
import pstats
import time
import random
import sys
from pathlib import Path

# Вычисляем пути относительно нового расположения скрипта (папка benchmark)
BENCHMARK_DIR = Path(__file__).parent
PROJECT_ROOT = BENCHMARK_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"

# Добавляем src в PYTHONPATH для корректных импортов
sys.path.append(str(SRC_DIR))

from core.engine import PhysicsEngine
from config.schemas import BodyState

def generate_bodies(n: int) -> list[BodyState]:
    bodies = []
    for i in range(n):
        bodies.append(BodyState(
            name=f"Asteroid-{i}",
            color="#FFFFFF",
            mass=random.uniform(1.0, 10.0),
            radius=random.uniform(2.0, 5.0),
            position=[random.uniform(-2000, 2000), random.uniform(-2000, 2000)],
            velocity=[random.uniform(-50, 50), random.uniform(-50, 50)]
        ))
    return bodies

def run_benchmark() -> None:
    num_bodies = 1000
    steps = 500
    dt = 0.016

    print("Инициализация...")
    engine = PhysicsEngine(g_const=100.0)
    bodies = generate_bodies(num_bodies)

    print(f"Запуск симуляции: {num_bodies} тел, {steps} шагов...")
    start_time = time.time()

    for _ in range(steps):
        engine.update(bodies, dt)

    elapsed = time.time() - start_time
    fps = steps / elapsed
    print(f"\n=== РЕЗУЛЬТАТЫ ===")
    print(f"Чистое время физики: {elapsed:.3f} сек")
    print(f"Средний FPS движка:  {fps:.1f} кадров/сек")
    print(f"==================\n")

if __name__ == "__main__":
    profiler = cProfile.Profile()
    profiler.enable()

    run_benchmark()

    profiler.disable()
    
    # Сохраняем файл профиля внутри папки benchmark
    dump_file = BENCHMARK_DIR / "physics.prof"
    profiler.dump_stats(str(dump_file))
    print(f"Файл профиля сохранен: {dump_file}")

    stats = pstats.Stats(profiler).sort_stats('cumtime')
    stats.print_stats(10)
