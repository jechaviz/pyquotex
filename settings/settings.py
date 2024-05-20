import yaml
from pathlib import Path

class Settings:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self.data = {}
        self._load_config()
    def _save_config(self):
        with self.config_path.open("w") as f:
            yaml.safe_dump(self.data, f, default_flow_style=False)
    def _load_config(self):
        if not self.config_path.exists():
            self._save_config()
        try:
            with self.config_path.open("r") as f:
                self.data = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Error reading configuration: {e}")

    def get(self, key, default=None):
        if key not in self.data:
            self.data[key] = input(f"Enter value for {key}: ")
            if self.data[key]=='' and default is not None:
                self.data[key] = default
            self._save_config()
        return self.data[key]