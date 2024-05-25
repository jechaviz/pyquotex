from quotexapi.ws.objects.base import Base

class Candle(object):
    def __init__(self, candle_data):
        self.__candle_data = candle_data

    @property
    def time(self):
        return self.__candle_data[0]

    @property
    def open(self):
        return self.__candle_data[1]

    @property
    def close(self):
        return self.__candle_data[2]

    @property
    def high(self):
        return self.__candle_data[3]

    @property
    def low(self):
        return self.__candle_data[4]

    @property
    def color(self):
        if self.open < self.close:
            return "green"
        elif self.open > self.close:
            return "red"


class Candles(Base):
    def __init__(self):
        super(Candles, self).__init__()
        self.__name = "candles"
        self.__candles_data = None

    @property
    def _list(self):
        return self.__candles_data

    @_list.setter
    def _list(self, candles_data):
        self.__candles_data = candles_data

    @property
    def first_candle(self):
        return Candle(self._list[0])

    @property
    def second_candle(self):
        return Candle(self._list[1])

    @property
    def current_candle(self):
        return Candle(self._list[-1])
