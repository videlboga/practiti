import importlib, sys

# Проксируем все импорты src.* в backend.src.*
backend_src = importlib.import_module('backend.src')

# Зарегистрируем псевдоним
sys.modules[__name__] = backend_src 