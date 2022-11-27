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

    current_weather = None

    @classmethod
    def get_weather(cls, location_code):
        params = cls.default_params.copy()
        params.update({'city': location_code})
        result = requests.get(url=cls.weather_url, params=params)
        if result.ok:
            result.encoding = 'utf-8'
            json_data = result.json()
            status = json_data.get('status')
            if status == 1:
                return json_data.get('lives')
            else:
                print('获取天气信息失败 Code: ', json_data.get('infocode'), ' Info: ', json_data.get('info'))
        else:
            return False
