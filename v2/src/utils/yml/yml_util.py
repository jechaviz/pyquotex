import yaml
from pathlib import Path

class YmlUtil:
    @staticmethod
    def load(file_path: Path) -> dict:
        if not file_path.exists():
            return {}
        try:
            with file_path.open('r') as f:
                data = yaml.safe_load(f) or {}
            return data
        except yaml.YAMLError as e:
            print(f'Error reading configuration: {e}')
            return {}

    @staticmethod
    def save(data: dict, file_path: Path):
        with file_path.open('w') as f:
            yaml.safe_dump(data, f, default_flow_style=False)
