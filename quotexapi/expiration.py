import time
import calendar
from datetime import datetime, timedelta


def get_timestamp():
  return calendar.timegm(time.gmtime())


def date_to_timestamp(dt):
  return time.mktime(dt.timetuple())


def timestamp_to_date(timestamp):
  return datetime.fromtimestamp(timestamp)


def get_expiration_time_quotex(timestamp, duration):
  now_date = datetime.fromtimestamp(timestamp)
  shift = 1 if now_date.second >= 30 else 0
  exp_date = now_date.replace(second=0, microsecond=0) + timedelta(minutes=duration // 60 + shift)
  return date_to_timestamp(exp_date)


def get_expiration_time(timestamp, duration):
  exp_date = datetime.now().replace(second=0, microsecond=0) + timedelta(seconds=duration)
  return int(date_to_timestamp(exp_date.replace(second=0, microsecond=0)))


def get_period_time(duration):
  period_date = datetime.now() - timedelta(seconds=duration)
  return int(date_to_timestamp(period_date))


def get_remaining_time(timestamp):
  exp_date = datetime.fromtimestamp(timestamp).replace(second=0, microsecond=0)
  if date_to_timestamp(exp_date + timedelta(minutes=1)) - timestamp > 30:
    exp_date += timedelta(minutes=1)
  else:
    exp_date += timedelta(minutes=2)
  exp = [date_to_timestamp(exp_date + timedelta(minutes=i)) for i in range(5)]

  now_date = datetime.fromtimestamp(timestamp)
  exp_date = now_date.replace(second=0, microsecond=0)
  idx, index = 11, 0
  while index < idx:
    if int(exp_date.strftime("%M")) % 15 == 0 and date_to_timestamp(exp_date) - timestamp > 300:
      exp.append(date_to_timestamp(exp_date))
      index += 1
    exp_date += timedelta(minutes=1)

  remaining = [(i + 1 if i < 5 else 15 * (i - 4), int(t) - int(time.time())) for i, t in enumerate(exp)]
  return remaining
