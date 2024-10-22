import time

from src.utils.dict.dict_util import DictUtil
from src.utils.log import logger
from paprika import singleton

@singleton
class WsState:
  def __init__(self):
    self.state = {}
    self.previous_state = {}

  def print_state_change(self):
    for key, value in self.state.items():
      if key not in self.previous_state or self.previous_state[key] != value:
        print(f'{key}:{value}')
    self.previous_state = self.state.copy()

  def get_state(self, key: str):
    keys = key.split('.')
    state = DictUtil.nested_get(self.state, keys)
    # state.update(self.state[keys[0]]['timestamp'])
    return state

  def set_state(self, key: str, value):
    # logger.debug(f'{key}:{value}')
    keys = key.split('.')
    DictUtil.nested_set(self.state, keys, value)
    # self.state[keys[0]]['timestamp'] = time.time()
    self.print_state_change()
    return self.state