import json

configfile = "config.json"

def getdata(name):
    with open(configfile, "r") as conf:
        return json.load(conf)[name]