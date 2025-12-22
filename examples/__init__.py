"""Examples package initialization.

This module adds the project root to sys.path so examples can import src modules
without requiring package installation.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))
