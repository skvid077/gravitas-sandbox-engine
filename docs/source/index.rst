Документация Gravitas Sandbox Engine
============================================

Gravitas Sandbox Engine — интерактивная симуляция гравитационного взаимодействия
небесных тел. Документация модулей строится Sphinx из docstring исходного кода.

.. toctree::
   :maxdepth: 2
   :caption: Содержание:

   modules

Примеры сценариев
-----------------

Готовые JSON-сценарии находятся в ``demo/``. Проверки времени запуска для них
можно выполнить командой ``python -m pytest tests/test_demo_performance.py``.
Для полного воспроизводимого профиля используйте ``python benchmark/benchmark.py``.
