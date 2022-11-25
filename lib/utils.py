class TimeUtils:
    weeks = [
        '周日',
        '周一',
        '周二',
        '周三',
        '周四',
        '周五',
        '周六'
    ]


class WeatherUtils:
    @staticmethod
    def get_weather(location_code):
        weather_rss_url = "https://weather-broker-cdn.api.bbci.co.uk/en/forecast/rss/3day/{0}".format(location_code)
