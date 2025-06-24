"""
CyberKitty Practiti Backend Package
"""

__version__ = "1.0.0"
__author__ = "CyberKitty"

import sys

# Позволяем импортировать `src.*` в тестах, перенаправляя на `backend.src.*`
sys.modules.setdefault('src', sys.modules[__name__]) 