"""pytest 공통 픽스처."""
import sys
from pathlib import Path

# src/ 경로 자동 추가
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
