import authentication
import pyowm
import pytz
import contact_info
from datetime import datetime
from twilio.rest import Client


def degToCompass(num):
    val = int((num / 22.5) + .5)
    arr = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW",
           "WSW", "W", "WNW", "NW", "NNW"]
    return arr[(val % 16)]


def send_weather_report(event=None, context=None):
    twilio_sid = authentication.sid
    auth_token = authentication.auth_token

    owm = pyowm.OWM(authentication.owm_api_key)
    places = ["Sao Jose dos Campos", "Praia de São Lourenço"]
    reg = owm.city_id_registry()
    observations = {}
    for place in places:
        observations[place] = {}

    for place in observations.keys():
        place_id = reg.ids_for(place)
        observations[place]["ID"] = place_id[0][0]
        observations[place]["place_name"] = place_id[0][1]
        observations[place]["country"] = place_id[0][2]
        obs = owm.weather_at_id(observations[place]["ID"])
        weather = obs.get_weather()
        observations[place]["weather"] = weather

    brazil_tz = pytz.timezone("America/Sao_Paulo")
    sp_time = datetime.now(brazil_tz)
    sp_hour = sp_time.hour

    if sp_hour >= 5 and sp_hour < 12:
        salutation = "Good morning!"
    elif sp_hour >= 12 and sp_hour < 18:
        salutation = "Good afternoon!"
    elif sp_hour >= 18 and sp_hour < 21:
        salutation = "Good evening!"
    else:
        salutation = "Good night!"

    msg_body = salutation + "\n"

    for place in observations.keys():
        place_obs = observations[place]
        place_weather = place_obs["weather"]
        msg_body += "\nThe weather report for {} ({}) right now is:\n".format(
            place_obs["place_name"],
            place_obs["country"]
        )
        msg_body += "Status: {}\n".format(
            place_weather.get_detailed_status())

        place_temperature = place_weather.get_temperature(unit='celsius')
        current_temp = place_temperature["temp"]
        max_temp = place_temperature["temp_max"]
        min_temp = place_temperature["temp_min"]
        msg_body += "Current temperature: {} °C\n".format(current_temp)
        msg_body += "Maximum temperature: {} °C\n".format(max_temp)
        msg_body += "Minimum temperature: {} °C\n".format(min_temp)

        place_wind = place_weather.get_wind()
        wind_speed = place_wind["speed"]
        wind_kts_speed = round(wind_speed * 1.943844)
        if "deg" in place_wind.keys():
            wind_deg = place_wind["deg"]
            wind_direction = degToCompass(wind_deg)
            msg_body += "Wind: {} m/s (~{}kts), {} ({}°)\n".format(
                wind_speed, wind_kts_speed, wind_direction, wind_deg)
        else:
            msg_body += "Wind: {} m/s (~{}kts)\n".format(wind_speed,
                                                         wind_kts_speed)

        place_pressure = place_weather.get_pressure()["press"]
        msg_body += "Pressure: {} hpa\n".format(place_pressure)

        place_humidity = place_weather.get_humidity()
        msg_body += "Humidity: {} %\n".format(place_humidity)

        place_sunrise = place_weather.get_sunrise_time("date")
        localtime_sunrise = place_sunrise.replace(
            tzinfo=pytz.utc).astimezone(brazil_tz)
        msg_body += "Sunrise: {}\n".format(
            localtime_sunrise.strftime("%H:%M:%S"))

        place_sunset = place_weather.get_sunset_time("date")
        localtime_sunset = place_sunset.replace(
            tzinfo=pytz.utc).astimezone(brazil_tz)
        msg_body += "Sunset: {}\n".format(
            localtime_sunset.strftime("%H:%M:%S"))

    whatsapp_client = Client(twilio_sid, auth_token)
    whatsapp_client.messages.create(
        body=msg_body,
        from_="whatsapp:" + contact_info.twilio_sandbox,
        to="whatsapp:" + contact_info.number
    )
