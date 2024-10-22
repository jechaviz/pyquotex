class WebsocketException(Exception):
  # Custom exception class for errors related to WebSocket communication.
  def __init__(self, message):
    super().__init__(message)
