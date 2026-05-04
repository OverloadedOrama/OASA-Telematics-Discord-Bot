# -*- coding: utf8 -*-
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import sys #for OASA exception
import requests #for OASA exception
import OASA_Scraper as OASA

TOKEN = "YourTokenHere"
command_prefix = ""
oasa_help_message = """**__Commands__**

ΟΑΣΑ *bus line* 👉 Shows the bus line's route and real time data of the busses' locations.

ΟΑΣΑ *bus line* *stop name or stop code* 👉 Shows real time data of the time it takes for the nearest bus to arrive at the stop (stop code is preferred because of OASA's limited creativity (duplicate stop names)).

schedule *bus line* 👉 Shows the bus line's timetable.
"""

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_message(message):
        if message.author == client.user:
                return

        msgUpper = message.content.upper()
        chan = message.channel
        if msgUpper.startswith(command_prefix + "OASA") or msgUpper.startswith(command_prefix + "ΟΑΣΑ"):
                args = message.content.split(" ")
                if len(args) == 1:
                        await chan.send("Δώσε όνομα λεωφορείο και κωδικό στάσης... Τι περιμένεις να γίνει αλλιώς; Πχ OASA 824 400160\n" + oasa_help_message)
                        return
                await chan.typing()
                busName = args[1].upper()
                if ListInString(["HELP", "ΒΟΗΘ"], busName):
                        await chan.send(oasa_help_message)
                        return

                try:
                        routeCodes, routeDescr, routeTypes = OASA.GetRouteCodes(busName)
                except requests.exceptions.ConnectionError:
                        await chan.send("Connection error when trying to get the route code(s)")
                        return
                except TypeError:
                        await chan.send("Δε βρήκα λεωφορείο {} φίλε/φίλη/φιλί :kiss: μου".format(busName))
                        return

                routeCode, direction = await getRouteCode(chan, routeCodes, routeDescr, busName, message)
                if routeCode == -1:
                        return
                if len(args) == 2:  # Grab the map
                        try:
                                img = OASA.FindBusLocation(busName, routeCode)
                        except requests.exceptions.ConnectionError:
                                await chan.send("Connection error when trying to get the bus location")
                                return
                        except:
                                await chan.send(sys.exc_info())
                                return

                        img = "BusLocation.png"
                        await chan.send(file=discord.File(img))

                elif len(args) > 2: # Asking about a specific stop
                        stop = " ".join(args[2:]).upper()
                        stopName = stop
                        routeType = routeTypes[direction - 1] # 1 from start or if it's cyclic, 2 from end
                        if any(c.isalpha() for c in stop):
                                stop = OASA.GetStopCode(stopName, routeCode)
                        if stop == "":
                                await chan.send("Στάση {} εγώ πάντως δεν βρήκα. Μήπως κάναμε κανένα λαθάκι; ΗΛΙΘΙΕ".format(stopName))
                                return
                        print(busName, " ", stop, " ", routeType)
                        try:
                                messageString = OASA.FindBus(busName, stop, routeType)
                                await chan.send(messageString)
                        except requests.exceptions.ConnectionError:
                                await chan.send("Server took too long to respond and I got bored")
                        except:
                                await chan.send(sys.exc_info())
                        

        elif msgUpper.startswith(command_prefix + "SCHEDUL") or msgUpper.startswith(command_prefix + "ΔΡΟΜΟΛ"):
                args = message.content.split(" ")
                if len(args) == 1:
                        await chan.send("με φώτισες.... ΠΟΙΟ ΛΕΩΟΦΟΡΕΙΟ ΘΕΣ ΡΕ **ΠΑΠΑΡΟΜΥΑΛΕ**????\n" + oasa_help_message)
                elif len(args) == 2:
                        await chan.typing()
                        busName = args[1].upper()
                        try:
                                messageString = OASA.GetAllSchedules(busName)
                                await chan.send(messageString)
                        except requests.exceptions.ConnectionError:
                                await chan.send("Server took too long to respond and I got bored")
                        except:
                                await chan.send(sys.exc_info())
                else:
                        await chan.send("Μονο ενα λεωφορειο δινουμε ρε **ΜΠΕΤΟΒΛΑΚΑ ΓΑΜΩ ΤΗ ΤΥΧΗ ΣΟΥ**\n" + oasa_help_message)


# Check if a string is in one of the strings of a given list.
def ListInString(theList, theString):
        for word in theList:
                if word in theString:
                        return True
        return False


async def getRouteCode(chan, routeCodes, routeDescr, busName, message):
        if len(routeCodes) == 1:
                routeCode = routeCodes[0]
                return routeCode, 1
        else:
                route_msg = "Ποια διαδρομή του λεωφορείου {} σε ενδιαφέρει;\n\n".format(busName)
                i = 1
                for route in routeDescr:
                        route_msg += route + " ({})\n".format(i)
                        i += 1
                await chan.send(route_msg)

                def check_if_same_author(m):
                        return message.author == m.author


                direction = await client.wait_for("message", check = check_if_same_author)
                await chan.typing()
                direction = direction.content
                try:
                        directionInt = int(direction)
                        if len(routeCodes) >= directionInt:
                                routeCode = routeCodes[directionInt - 1]
                                return routeCode, directionInt
                        await chan.send("Μάθε να μετράς πρώτα ΑΝΘΡΩΠΑΚΙ... και μετά μίλα μου. Γκέγκε;")
                        return -1, -1
                except ValueError:
                        await chan.send("Ακούσε να δεις ΑΝΘΡΩΠΑΚΙ. Δεν θα με τρολάρεις ΕΣΥ ΕΜΕΝΑ, ΚΑΤΑΛΑΒΕΣ;")
                        return -1, -1


client.run(TOKEN)
