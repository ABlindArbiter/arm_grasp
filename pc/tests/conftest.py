import sys
from pathlib import Path

# 把 pc/ 加入 sys.path，让测试能 import arm.transforms
PC_DIR = Path(__file__).resolve().parents[1]
if str(PC_DIR) not in sys.path:
    sys.path.insert(0, str(PC_DIR))
