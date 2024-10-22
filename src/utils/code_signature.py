import inspect


class CodeSignature:

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
  def info(obj=None, show_path=False):
    indent = CodeSignature.get_indent()
    obj_path = CodeSignature.get_path()
    fn = f"{obj.__class__.__name__ + '.' if obj else ''}{inspect.stack()[1].function}"
    if show_path:
      print(f'{obj_path}-{fn}')
    else:
      print(f'{indent}{fn}')


# Example usage
class A:
  def a_method(self):
    CodeSignature.info(self)
    CodeSignature.info(self, show_path=True)
    B().b_method()


class B:
  def b_method(self):
    CodeSignature.info(self)
    CodeSignature.info(self, show_path=True)


# Integration test
if __name__ == "__main__":
  A().a_method()
