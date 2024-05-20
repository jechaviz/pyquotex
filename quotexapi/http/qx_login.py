from ..http.qx_session_setter import QxSessionSetter

class Login(QxSessionSetter):
    async def __call__(self, settings):
        self.settings = settings
        self.load_settings(settings)
        await self.set_session()
