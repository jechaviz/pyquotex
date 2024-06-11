import inspect

class ThisName:

    @staticmethod
    def get_indent():
        return "  " * (len(inspect.stack()) - 2)  # Consider only relevant frames

    # TODO: No working
    @staticmethod
    def get_class_path(obj=None):
      if not obj: #or not inspect.isclass(self.obj):
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
    def print(obj=None, show_path=False):
        indent = ThisName.get_indent()
        obj_path = ThisName.get_path()
        method = f"{obj.__class__.__name__ if obj else ''}.{inspect.stack()[1].function}"
        if show_path:
          print(f'{obj_path}-{method}')
        else:
          print(f'{indent}{method}')

# Example usage
class A:
  def a_method(self):
    ThisName.print(self)
    ThisName.print(self,show_path=True)
    B().b_method()

class B:
    def b_method(self):
        ThisName.print(self)
        ThisName.print(self, show_path=True)

if __name__ == "__main__":
    A().a_method()  # Output:   A.B.some_method
