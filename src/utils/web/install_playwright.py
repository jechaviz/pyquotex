from __future__ import annotations

import subprocess

from playwright._impl._driver import compute_driver_executable, get_driver_env
from playwright.async_api import BrowserType as AsyncBrowserType
from playwright.sync_api import BrowserType as SyncBrowserType


def install(browser_type: SyncBrowserType | AsyncBrowserType, *, with_deps=False):
  # install playwright and deps if needed
  # Sample browser_type = `p.chrome`
  # with_deps = install with dependencies.
  driver_executable = str(compute_driver_executable())
  args = [driver_executable, "install-deps"]
  env = None
  if browser_type:
    args = [driver_executable, "install", browser_type.name]
    env = get_driver_env()
    if with_deps:
      args.append("--with-deps")
  proc = subprocess.run(args, env=env, capture_output=True, text=True)
  return proc.returncode == 0
