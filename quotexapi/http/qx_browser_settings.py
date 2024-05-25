from quotexapi.http.navigator import Navigator

class QxBrowserSettings(Navigator):
    def __init__(self, api):
        super().__init__()
        self.api = api
        self._set_api_headers()

    def _set_api_headers(self):
        self.add_headers({
            'content-type': 'application/json',
            'Referer': 'https://qxbroker.com/en/trade',
            'cookie': self.api.session_data['cookies'],
            'User-Agent': self.api.session_data['user_agent']
        })

    def get(self):
        response = self.send_request('GET', 'https://qxbroker.com/api/v1/cabinets/digest')
        return response.json() if response.ok else None