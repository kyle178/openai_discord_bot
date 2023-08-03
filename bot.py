import openai
import json
import requests
import discord
import os
import traceback
import config
import functions as funcs
from discord.ext import commands

bot = commands.Bot(command_prefix="-", intents=discord.Intents.all())

openai.api_key = config.getdata("keys")["open_ai_key"]

model=config.getdata("model")

def run_conversation(msg, messages):
    functions = [
        {
            "name": "getweather",
            "description": "Gets the current weather of the desired location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "A town or city, e.g dundee scotland or perth in australia"
                    }
                }
            }
        },
        {
            "name": "getcryptoprice",
            "description": "Gets the current price of the desired cryptocurrency.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the cryptocurrency in lowercase, e.g bitcoin, ethereum"
                    }
                }
            }
        },
        {
            "name": "whatsmyname",
            "description": "Returns the name of the bot.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dummy_property": {
                        "type": "null"
                    }
                }
            }
        }
    ]

    message = {"role": "user", "content": msg}
    messages.append(message)
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        functions=functions,
        function_call="auto"
    )

    responce_message = response["choices"][0]["message"]

    if responce_message.get("function_call"):
        available_functions = {
            "getweather": funcs.getweather,
            "getcryptoprice": funcs.getcryptoprice,
            "whatsmyname": funcs.whatsmyname
        }
        functionname = responce_message["function_call"]["name"]
        functiontocall = available_functions[functionname]
        function_args = json.loads(responce_message["function_call"]["arguments"])

        if functionname == "getweather":
            functionresponse = functiontocall(function_args["location"])
        elif functionname == "getcryptoprice":
            functionresponse = functiontocall(function_args["name"])
        elif functionname == "whatsmyname":
            functionresponse = functiontocall(bot)
            
        messages.append(responce_message)
        messages.append(
            {
                "role": "function",
                "name": functionname,
                "content": functionresponse
            }
        )
        second_response = openai.ChatCompletion.create(
            model=model,
            messages=messages
        )
        second_response_message = second_response["choices"][0]["message"]
        return [second_response_message, messages]
    else:
        message = {
            "role": response["choices"][0]["message"]["role"],
            "content": response["choices"][0]["message"]["content"]
        }
        messages.append(message)
        return [responce_message, messages]

@bot.event
async def on_ready():
    print(f"{bot.user.name} has started succesfully.")
    await bot.change_presence(activity=discord.Game(name="-ask"))

def readMessageHistory(guildid):
    if not os.path.exists("history"):
        os.mkdir("history")
    else:
        pass
    try:
        with open(os.path.join("history", f"{guildid}.json"), "r") as saveddata:
            return [0, json.load(saveddata)]
    except IOError as ioex:
        if ioex.errno == 2:
            return [1, []]#file does not exist
        else:
            return [2, traceback.print_exc()]#other ioerror
    except Exception as ex:
        return [3, []]#probably nothing in the json file exception

def updateMessageHistory(guildid, messages):
    if not os.path.exists("history"):
        os.mkdir("history")
    else:
        pass
    with open(os.path.join("history", f"{guildid}.json"), "w") as data:
        json.dump(messages, data, indent=1)

@bot.command(name="ask")
async def ask(ctx, *, prompt):
    guildid = ctx.guild.id
    message = ""
    try:
        async with ctx.typing():
            history = readMessageHistory(guildid)
            if history[0] == 0:
                print(f"Fetched history for guild id, {guildid}")
            elif history[0] == 1:
                updateMessageHistory(guildid, [])
                print(f"No history file for {guildid}, a file will now be created")
            elif history[0] == 3:
                print(f"No history saved for {guildid}")
            aidata = run_conversation(prompt, history[1])
            message = aidata[0]["content"]
            updateMessageHistory(guildid, aidata[1])
            print(f"Updated history for guild id, {guildid}")
        if len(message) >= 2000:
            print("Message length more that 2000, sending as text file")
            with open("message.txt", "w") as messagefile:
                messagefile.write(message)
            await ctx.send(file=discord.File("message.txt", f"{prompt}.txt"))
            os.remove("message.txt")
        else:
            await ctx.send(message)
    except Exception as ex:
        print("Error while trying to run prompt.", traceback.print_exc())
        await ctx.send("Error please try again or try a different prompt")

@bot.command(name="clear")
async def clear(ctx):
    guildid = ctx.guild.id
    print(f"Clearing history for guild id {guildid}")
    with open(os.path.join("history", f"{guildid}.json"), "w") as history:
        history.write("")
    await ctx.send("Cleared message history for this server.")

bot.run("MTA4MDk3NTAwNzM4OTMyMzM2NQ.Gb-4ix.az8WAhJMiHT_nw4cbIkVKDgPN1pBIp0z0sMSuY")