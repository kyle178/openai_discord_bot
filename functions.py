import config,json,requests

#all the functions that the api can call go in this file

def getweather(location):
    api_key = config.getdata("keys")["weather_api_key"]
    response = requests.get(f"http://api.weatherstack.com/current?access_key={api_key}&query={location}&units=m").json()
    weather_info = {
        "location": location,
        "temperature": response["current"]["temperature"],
        "weather description": response["current"]["weather_descriptions"]
    }
    return json.dumps(weather_info)

def getcryptoprice(name):
    response = requests.get(f"http://api.coincap.io/v2/assets/{name}/")
    return json.dumps(response.json())

def whatsmyname(bot):
    return bot.user.name