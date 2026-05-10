import cProfile
import pstats
import time
import random
import sys
import logging
from pathlib import Path

# 1. Настройка путей
BENCHMARK_DIR = Path(__file__).parent
PROJECT_ROOT = BENCHMARK_DIR.parent
SRC_DIR = PROJECT_ROOT / "src"
sys.path.append(str(SRC_DIR))

# Импорты твоего движка
from core.engine import PhysicsEngine
from config.schemas import BodyState

# 2. Настройка логгирования
log_file = BENCHMARK_DIR / "benchmark.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("Benchmark")

def generate_bodies(n: int) -> list[BodyState]:
    """Генерация случайных тел для теста."""
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
    """Запуск замера производительности."""
    dt = 0.016
    engine = PhysicsEngine(g_const=100.0)
    bodies = generate_bodies(num_bodies)

    logger.info("="*40)
    logger.info(f"ЗАПУСК БЕНЧМАРКА: {num_bodies} тел, {steps} шагов")
    logger.info(f"Конфигурация: G={engine.G}, dt={dt}")
    
    start_time = time.perf_counter()
    last_checkpoint = start_time
    
    # Рекурсивное логгирование каждые 20% прогресса
    log_interval = max(1, steps // 5)

    for step in range(1, steps + 1):
        engine.update(bodies, dt)
        
        if step % log_interval == 0 or step == steps:
            now = time.perf_counter()
            step_time = (now - last_checkpoint) / log_interval if step > 1 else (now - start_time)
            progress = (step / steps) * 100
            
            logger.info(
                f"Progress: {progress:>3.0f}% | "
                f"Step: {step}/{steps} | "
                f"Avg step time: {step_time:.4f}s"
            )
            last_checkpoint = now

    total_time = time.perf_counter() - start_time
    fps = steps / total_time
    
    logger.info("-" * 40)
    logger.info(f"БЕНЧМАРК ЗАВЕРШЕН")
    logger.info(f"Общее время: {total_time:.3f} сек")
    logger.info(f"Производительность: {fps:.2f} FPS")
    logger.info("=" * 40)

if __name__ == "__main__":
    # Параметры теста
    B_COUNT = 1000
    S_COUNT = 500

    profiler = cProfile.Profile()
    
    try:
        profiler.enable()
        run_benchmark(num_bodies=B_COUNT, steps=S_COUNT)
        profiler.disable()
    except Exception as e:
        logger.error(f"Произошла ошибка во время теста: {e}", exc_info=True)
    finally:
        # Сохранение результатов профилирования
        prof_file = BENCHMARK_DIR / "physics.prof"
        profiler.dump_stats(str(prof_file))
        logger.info(f"Данные cProfile сохранены в {prof_file}")

        # Вывод краткой статистики в консоль через логгер
        import io
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats('cumtime')
        ps.print_stats(10)
        logger.info("\nTOP-10 FUNCTIONS:\n" + s.getvalue())
