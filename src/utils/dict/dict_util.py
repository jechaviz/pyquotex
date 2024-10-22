from typing import Any, Dict

class DictUtil:
    @staticmethod
    def nested_set(data: Dict, key_parts: list, value: Any) -> Dict[str, Any]:
        # Sets a nested value in a dictionary.
        # Args: key_parts: A list of keys representing the nested path.
        if not key_parts: return value
        current_key = key_parts[0]
        if current_key not in data:
            data[current_key] = {}
        data[current_key] = DictUtil.nested_set(data[current_key], key_parts[1:], value)
        return data

    @staticmethod
    def nested_get(data: Dict, key_parts: list) -> Any:
        #Gets a nested value from a dictionary.
        #Args: key_parts: A list of keys representing the nested path.
        if not key_parts: return None
        current_key = key_parts[0]
        if current_key in data:
            value = data[current_key]
            if isinstance(value, dict) and key_parts[1:]:
                return DictUtil.nested_get(value, key_parts[1:])
            else:
                return value
        return None

def main():
  data = {'a': {'b': {'c': 'value'}}}
  key_parts = 'a.b.c'.split('.')
  print(DictUtil.nested_set({}, key_parts, ['a', 'b', 'c']))
  print(DictUtil.nested_get(data, ['a', 'b', 'c']))
  print(DictUtil.nested_get(data, ['a']))

# Integration test
if __name__ == '__main__':
    main()