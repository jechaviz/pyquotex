from quotexapi.ws.objects.base import Base


class Profile(Base):
    def __init__(self):
        super(Profile, self).__init__()
        self.__name = "profile"
        self.__nick_name = None
        self.__profile_id = None
        self.__avatar = None
        self.__country = None
        self.__country_name = None
        self.__live_balance = None
        self.__demo_balance = None
        self.__msg = None
        self.__currency_code = None
        self.__currency_symbol = None
        self.__profile_level = None
        self.__minimum_amount = None

    @property
    def nick_name(self):
        return self.__nick_name

    @nick_name.setter
    def nick_name(self, nick_name):
        self.__nick_name = nick_name

    @property
    def live_balance(self):
        return self.__live_balance

    @live_balance.setter
    def live_balance(self, live_balance):
        self.__live_balance = live_balance

    @property
    def profile_id(self):
        return self.__profile_id

    @profile_id.setter
    def profile_id(self, profile_id):
        self.__profile_id = profile_id

    @property
    def demo_balance(self):
        return self.__demo_balance

    @demo_balance.setter
    def demo_balance(self, demo_balance):
        self.__demo_balance = demo_balance

    @property
    def avatar(self):
        return self.__avatar

    @avatar.setter
    def avatar(self, avatar):
        self.__avatar = avatar

    @property
    def msg(self):
        return self.__msg

    @msg.setter
    def msg(self, msg):
        self.__msg = msg

    @property
    def currency_symbol(self):
        return self.__currency_symbol

    @currency_symbol.setter
    def currency_symbol(self, currency_symbol):
        self.__currency_symbol = currency_symbol

    @property
    def country(self):
        return self.__country

    @country.setter
    def country(self, country):
        self.__country = country

    @property
    def country_name(self):
        return self.__country_name

    @country_name.setter
    def country_name(self, country_name):
        self.__country_name = country_name

    @property
    def minimum_amount(self):
        return self.__minimum_amount

    @property
    def currency_code(self):
        return self.__currency_code

    @currency_code.setter
    def currency_code(self, currency_code):
        self.__currency_code = currency_code
        if self.__currency_code.upper() == "BRL":
            self.__minimum_amount = 5

    @property
    def profile_level(self):
        return self.__profile_level

    @profile_level.setter
    def profile_level(self, profile_level):
        self.__profile_level = profile_level
