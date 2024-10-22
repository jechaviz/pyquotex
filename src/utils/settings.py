from pathlib import Path
from typing import Optional, Any
import os
from src.utils.dict.dict_util import DictUtil
from src.utils.yml.yml_util import YmlUtil


class Settings:
    # Manages application settings from a YAML configuration file.
    def __init__(self, config_path: Path = None):
        self.data: dict = {}
        self.root_dir = Path(__file__).parent.parent.parent
        self.config_path = config_path or Path(os.path.join(self.root_dir, 'src/resources/settings.yml'))
        self._load_data()

    def _load_data(self):
        self.data = YmlUtil.load(self.config_path)

    def _save_data(self):
        YmlUtil.save(self.data, self.config_path)

    def set(self, key: str, value: Any):
        # Sets a setting like key.subkey...value
        self.data = DictUtil.nested_set(self.data, key.split('.'), value)
        self._save_data()

    def get(self, key: str, default: Optional[Any] = None) -> Optional[str | Path]:
        # Gets a setting value like key.subkey...value
        value = DictUtil.nested_get(self.data, key.split('.'))
        if value is None and default is not None:
            value = default
        if isinstance(value, str):
            value = self._handle_path(key, value)
            value = self._handle_url(key, value)
        return value

    def _handle_path(self, key: str, value: str):
        # Handles path settings by prepending the root directory if the key contains 'paths'.
        if 'paths' in key:
            return Path(os.path.join(self.root_dir, value))
        return value

    def _handle_url(self, key: str, value: str):
        # Handles URL settings by constructing the full URL with a base URL if necessary.
        if 'urls' in key and not 'base' in key and not '://' in value:
            last_dot = key.rfind('.')
            parent_key = key[:last_dot]
            base_url = self.get(parent_key + '.base')
            if base_url:
                return str(base_url) + str(value)
        return value


def main():
  settings = Settings()
  print(settings.get('qx.urls.login'))
  print(settings.get('qx.wss.url'))

# Integration test
if __name__ == '__main__':
  main()