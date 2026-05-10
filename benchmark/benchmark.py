import cProfile
import pstats
import time
import random
import sys
import logging
import io
from pathlib import Path

# 1. Настройка путей
BENCHMARK_DIR = Path(__file__).parent
PROJECT_ROOT = BENCHMARK_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

# Импорты движка и схем
from core.engine import PhysicsEngine
from config.schemas import BodyState

# 2. Настройка логгирования
log_file = BENCHMARK_DIR / "benchmark_20planet.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Benchmark")

def generate_bodies(n: int) -> list[BodyState]:
    bodies = []
    for i in range(n):
        bodies.append(BodyState(
            name=f"Ast-{i}",
            color="#FFFFFF",
            mass=random.uniform(10.0, 100.0),
            radius=random.uniform(2.0, 5.0),
            position=[random.uniform(-1000, 1000), random.uniform(-1000, 1000)],
            velocity=[random.uniform(-50, 50), random.uniform(-50, 50)]
        ))
    return bodies

def run_benchmark(num_bodies: int = 100, steps: int = 50) -> None:
    dt = 0.016
    engine = PhysicsEngine(g_const=100.0)
    bodies = generate_bodies(num_bodies)

    logger.info("="*50)
    logger.info(f"START: {num_bodies} bodies | {steps} steps")
    
    start_time = time.perf_counter()
    last_checkpoint = start_time
    
    # Интервал в 1% (но не реже чем 1 шаг)
    log_interval = max(1, steps // 100) 

    for step in range(1, steps + 1):
        engine.update(bodies, dt)
        
        # Логируем каждые 1% прогресса
        if step % log_interval == 0 or step == steps:
            now = time.perf_counter()
            # Время конкретно за этот интервал шагов
            interval_time = now - last_checkpoint
            total_elapsed = now - start_time
            
            progress = (step / steps) * 100
            
            # Расчет ETA (сколько осталось)
            eta = (total_elapsed / (step / steps)) - total_elapsed if step < steps else 0
            
            logger.info(
                f"[{progress:>3.0f}%] Step {step}/{steps} | "
                f"Int: {interval_time:.4f}s | "
                f"Total: {total_elapsed:.2f}s | "
                f"ETA: {eta:.2f}s"
            )
            last_checkpoint = now

    total_time = time.perf_counter() - start_time
    logger.info("-" * 50)
    logger.info(f"FINISH | Total Time: {total_time:.3f}s | Result: {steps / total_time:.2f} FPS")
    logger.info("=" * 50)

if __name__ == "__main__":
    # Параметры теста
    B_COUNT = 20
    S_COUNT = 500

    profiler = cProfile.Profile()

    try:
        profiler.enable()
        run_benchmark(num_bodies=B_COUNT, steps=S_COUNT)
        profiler.disable()
    except Exception as e:
        logger.error(f"Error: {e}", exc_info=True)
    finally:
        # Сохранение профиля для snakeviz
        prof_file = BENCHMARK_DIR / "physics_20planet.prof"
        profiler.dump_stats(str(prof_file))
        
        # Запись ТОП-10 функций
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumtime')
        ps.print_stats(10)
        logger.info("\nTOP-10 PERFORMANCE KILLERS:\n" + s.getvalue())
