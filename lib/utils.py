import requests


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
    weather_url = 'https://restapi.amap.com/v3/weather/weatherInfo'

    application_key = '2e98c2c2f51141f6bdaf1da94a40a7e7'

    default_params = {'key': application_key}

    has_data = False

    province = ''

    city = ''

    weather = ''

    temperature = ''

    wind_direction = ''

    wind_power = ''

    humidity = ''

    @classmethod
    def get_weather(cls, location_code):
        params = cls.default_params.copy()
        params.update({'city': location_code})
        result = requests.get(url=cls.weather_url, params=params)
        if result.ok:
            result.encoding = 'utf-8'
            json_data = result.json()
            status = json_data.get('status')
            if status == '1':
                weather_data = json_data.get('lives')[0]
                cls.province = weather_data.get('province')
                cls.city = weather_data.get('city')
                cls.weather = weather_data.get('weather')
                cls.temperature = weather_data.get('temperature')
                cls.wind_direction = weather_data.get('winddirection')
                cls.wind_power = weather_data.get('windpower')
                cls.humidity = weather_data.get('humidity')
                cls.has_data = True
                return weather_data
            else:
                cls.has_data = False
                print('获取天气信息失败 Code: ', json_data.get('infocode'), ' Info: ', json_data.get('info'))
        else:
            cls.has_data = False
            return False
