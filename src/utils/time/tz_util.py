from datetime import datetime, timezone

import pytz


class TZUtil:
  def __init__(self, local_tz):
    self.local_tz = pytz.timezone(local_tz)

  def get_tz_offset(self):
    return datetime.now().astimezone(self.local_tz).utcoffset()

  def format(self, dt):
    return dt.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]

  def utc_to_local(self, timestamp):
    utc_dt = datetime.fromtimestamp(timestamp, timezone.utc)
    local_dt = utc_dt.astimezone(self.local_tz)
    return self.format(local_dt)
