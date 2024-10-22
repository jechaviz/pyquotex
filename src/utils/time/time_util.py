import time


class TimeUtil:
  @staticmethod
  def wait(timeout_secs, condition_func, interval=0.1):
    start_time = time.time()
    while time.time() - start_time < timeout_secs:
      if condition_func():
        return True
      time.sleep(interval)
    return False


# Integration test
if __name__ == "__main__":
  while not TimeUtil.wait(5, lambda: None):  # Replace self.ws_msg with your condition
    print("Waiting for message (timeout in 5 seconds)...")
