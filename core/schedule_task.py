import datetime
import schedule
from lib.utils import WeatherUtils


def weather_task():
    print('天气定时任务开始 - ',  datetime.datetime.now())
    WeatherUtils.get_weather(310118)


schedule.every(30).minutes.do(weather_task)
