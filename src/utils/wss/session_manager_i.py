from abc import ABC, abstractmethod


class SessionManagerI(ABC):
  def __init__(self, settings):
    self.settings = settings
    self.session_data = {}

  @abstractmethod
  async def login(self, force=False) -> dict:
    # Performs login and returns the session data.
    # Optionally, you can force login even if a session data exists.
    # Returns: A dictionary containing session data.
    pass

  @abstractmethod
  def logout(self) -> bool:
    # Performs logout and clears session data.
    # Returns: True if logout was successful, False otherwise.
    pass
