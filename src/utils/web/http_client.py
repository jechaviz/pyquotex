from requests import Session
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from bs4 import BeautifulSoup
from .user_agents import agents
from paprika import *

@singleton
class HttpClient():
    def __init__(self):
        user_agents = [line.strip() for line in agents.splitlines() if line.strip()]
        self.session = Session()
        self._configure_session()
        self.headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)'}
        self.user_agents = UserAgents(user_agents)

    def _configure_session(self):
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504, 104],
            allowed_methods=['HEAD', 'POST', 'PUT', 'GET', 'OPTIONS']
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount('https://', adapter)
        self.session.mount('http://', adapter)

    def get(self, url, headers=None, **kwargs):
        return self._update_and_request('GET', url, headers=headers, **kwargs)

    def post(self, url, data=None, headers=None):
        return self._update_and_request('POST', url, data=data, headers=headers)

    def _update_and_request(self, method, url, data=None, headers=None, **kwargs):
        if headers: self.headers.update(headers)
        response = self.send_request(method=method, url=url, data=data, headers=self.headers, **kwargs)
        if response.status_code not in range(200, 300):
            self.headers.update({'user-agent': self.user_agents.get_next()})
        return response

    def send_request(self, method, url, data, headers, **kwargs):
        return self.session.request(method=method, url=url, data=data, headers=headers, **kwargs)

    def get_soup(self, url, **kwargs):
        response = self.get(url, **kwargs)
        return BeautifulSoup(response.content, 'html.parser')

@singleton
class UserAgents:
    def __init__(self, user_agents):
        self.user_agents = user_agents
        self.current_index = 0

    def get_next(self):
        self.current_index = self.current_index % len(self.user_agents) # Cycle through user agents
        user_agent = self.user_agents[self.current_index]
        self.current_index += 1
        return user_agent