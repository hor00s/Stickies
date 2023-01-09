import os
from enum import Enum
from pathlib import Path


class LabelColor(Enum):
    ERROR = (255, 0, 0)
    SUCCESS = (0, 255, 0)
    INFO = (242, 206, 12)
    WARNING = (243, 183, 18)


BASE_DIR = f'{os.sep}'.join(__file__.split(os.sep)[:-2])
os.chdir(BASE_DIR)

ICONS = os.listdir(Path(f"{BASE_DIR}/icons"))
get_icon = {f"{icon[:icon.index('.')]}": str(Path(f"{BASE_DIR}/icons/{icon}")) for icon in ICONS}
VERSIONS = (
    '1.0',
)
