import ast
import json
import re

import yaml
from chevron import render


class ApiParser():
  # Defines an api in a yml per defined actions.
  # See api_parser_conf.yml.
  def __init__(self, config_path: str):
    self.config_path = config_path
    self.api_name = config_path.replace('.yml', '')
    self.api = self._load_config()
    self.action_templates = self._load_action_templates()
    self.class_template = ''
    self.var_defaults = self.api.get('var_defaults', {})
    self.constants = self.api.get('constants', {})

  def _load_config(self):
    with open(self.config_path) as f:
      return yaml.safe_load(f)

  def _load_action_templates(self):
    # load the templates to cache self.action_templates
    request_templates = {}
    for section, sections in self.api.items():
      if section != 'actions': continue
      for action_name, action_items in sections.items():
        requests = []
        if not action_items: continue
        for action_item in action_items:
          endpoint = action_item.get('endpoint', '')
          payload = action_item.get('payload', {})
          response_ok_contains = ''
          response_error_contains = ''
          try:
            response_ok_contains = action_item['is_success']['response_contains']
            response_error_contains = action_item['is_error']['response_contains']
          except:
            pass
          requests.append({'endpoint': endpoint, 'payload': payload,
                           'response_ok_contains': response_ok_contains,
                           'response_error_contains': response_error_contains})
        request_templates[f'{action_name}'] = requests
    return request_templates

  def action_requests(self, action_id, values):
    # fill the action template with values provided
    try:
      action_template = self.action_templates[action_id]
    except KeyError:
      raise KeyError(f"Action '{action_id}' not found in config")
    merged_values = {**self.var_defaults, **values}
    action_str = render(str(action_template), merged_values)
    try:
      action = ast.literal_eval(action_str)
    except (SyntaxError, ValueError) as e:
      raise ValueError(f"Error parsing action '{action_id}': {e}")
    requests = []
    for item in action:
      payload = re.sub(r'"(\d+)"', r'\1', json.dumps(item['payload']))
      request = item['endpoint'].format(payload=payload)
      requests.append(request)
    return requests

  def generate_class(self):
    class_code = f'class {self.api_name.title().replace('_', '')}:\n'
    for action_name, action_items in self.api['actions'].items():
      keys = []
      for action_item in action_items:
        payload = action_item.get('payload', {})
        keys.extend(self._get_template_keys(payload))
      arguments = ", ".join(keys)
      method_code = f'\n  def {action_name}(self, {arguments}):\n'
      method_body = f'    self.ws.send({arguments})'
      method_body += f'    requests = self.api.action_requests({action_name}, values)'
      method_code += method_body
      class_code += method_code + '\n'
    return class_code

  def _get_template_keys(self, data):
    keys = []
    if isinstance(data, dict):
      for key, value in data.items():
        if isinstance(value, str) and "{{" in value:
          keys.append(re.sub(r'[\{\}]', '', value))
        else:
          keys.extend(self._get_template_keys(value))
    return keys


def print_action(api, action_id, values):
  # for testing purposes
  print(action_id)
  requests = api.action_requests(action_id, values)
  for request in requests:
    print(request)
  print()


def main():
  values = {
    'asset': 'usd',
    'price': 5,
    'duration': 1,
    'direction': 2,
    'is_demo': 1
  }
  api = ApiParser('api_parser_conf.yml')
  print_action(api, 'complex_action', values)
  # class_code = api.generate_class()
  # print(class_code)


# Integration test
if __name__ == '__main__':
  main()
