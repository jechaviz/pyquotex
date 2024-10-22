from abc import ABC, abstractmethod

class WsMsgHandlerI(ABC):
  def __init__(self, ws_state):
    self.ws_state = ws_state
    self.api = {}
    self.msg = None

  @abstractmethod
  def set_msg(self, msg):
    pass

  @abstractmethod
  def handle_msg(self, msg):
    pass

  @abstractmethod
  def is_connected(self, msg):
    pass
