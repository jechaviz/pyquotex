import inspect
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
class tree:

  @staticmethod
  def get_indent():
    return '  ' * (len(inspect.stack()) - 14)  # Consider only relevant frames

  # TODO: No working
  @staticmethod
  def get_class_path(obj=None):
    if not obj:
      return ''
    path = []
    current_cls = obj.__class__
    while current_cls is not object:
      path.append(current_cls.__name__)
      current_cls = current_cls.__bases__[0] if current_cls.__bases__ else None
    return ".".join(reversed(path)) + "."  # Exclude leading dot

  @staticmethod
  def get_path(frame_offset=1):
    try:
      frame = inspect.stack()[frame_offset]
      return frame.filename
    except (IndexError, AttributeError):
      return ''

  @staticmethod
  def _log(level, obj=None, msg='', show_path=False):
    indent = tree.get_indent()
    obj_path = tree.get_path()
    fn = f"{obj.__class__.__name__ + '.' if obj else ''}{inspect.stack()[2].function}"  # [2] to get caller function
    signature = f'{obj_path}-{fn}' if show_path else f'{indent}{fn}'
    message = f'{indent}> {msg}' if msg else f'{signature}'
    logger.log(level, message)

  @staticmethod
  def debug(obj=None, msg='', show_path=False):
    tree._log(logging.DEBUG, obj, msg, show_path)

  @staticmethod
  def info(obj=None, msg='', show_path=False):
    tree._log(logging.INFO, obj, msg, show_path)

  @staticmethod
  def warning(obj=None, msg='', show_path=False):
    tree._log(logging.WARNING, obj, msg, show_path)

  @staticmethod
  def error(obj=None, msg='', show_path=False):
    tree._log(logging.ERROR, obj, msg, show_path)

  @staticmethod
  def critical(obj=None, msg='', show_path=False):
    tree._log(logging.CRITICAL, obj, msg, show_path)

# Example usage
class A:
  def a_method(self):
    tree.info(self)
    tree.info(self, show_path=True)
    B().b_method()


class B:
  def b_method(self):
    tree.info(self)
    tree.info(self, show_path=True)


# Integration test
if __name__ == "__main__":
  A().a_method()
