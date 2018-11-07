from pathlib import Path

from decouple import AutoConfig


current_dir = Path()
config = AutoConfig(current_dir)

DEBUG = config("SIMPLE_SMARTSHEET_DEBUG", default=False, cast=bool)
