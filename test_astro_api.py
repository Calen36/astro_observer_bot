import json

with open('test.json', 'r') as file:
    for x in json.loads(file.read())['data']['table']['rows']:
        planet_name = x['cells'][0]['name']
        elongation = x['cells'][0]['extraInfo']['elongation']
        try:
            magnitude = round(float(x['cells'][0]['extraInfo']['magnitude']), 2)
        except:
            magnitude = None
        constellation = x['cells'][0]['position']['constellation']['name']  # name можно заменить на id для трехбуквенных обозначений
        rightAscension = x['cells'][0]['position']['equatorial']['rightAscension']['string']  # hours
        declination = x['cells'][0]['position']['equatorial']['declination']['string']  # degrees
        altitude = x['cells'][0]['position']['horizonal']['altitude']['string']  # degrees
        azimuth = x['cells'][0]['position']['horizonal']['azimuth']['string']  # degrees
        # print(x.keys())
        # print(x['entry'])
        # print(x['cells'][0].keys())
        # print( x['cells'][0]['position'])
        # if x['cells'][0]['name'] == 'Uranus':
        #     print(x['cells'][0]['position'])

        summary = f"""  {planet_name.upper()}
находится в созвездии {constellation} и имеет яркость {magnitude} з.в.
элонгация {elongation}
  ЭКВАТОРИАЛЬНЫЕ КООРДИДАНТЫ
прямое восхождение {rightAscension}
cклонение {declination}
  ГОРИЗОНТАЛЬНЫЕ КООРДИНАТЫ
высота над горизонтом {altitude}
азимут {azimuth}
        """
        print(summary)