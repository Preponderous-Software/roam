"""Root conftest for all tests - mocks pygame globally."""

import sys
from unittest.mock import MagicMock

# Mock pygame before any test imports
sys.modules["pygame"] = MagicMock()
sys.modules["pygame.font"] = MagicMock()
sys.modules["pygame.display"] = MagicMock()
sys.modules["pygame.image"] = MagicMock()
