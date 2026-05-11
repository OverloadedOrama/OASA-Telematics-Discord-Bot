# -*- coding: utf8 -*-
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import sys # for OASA exception
import requests # for OASA exception
import OASA_Scraper as OASA

TOKEN = "YourTokenHere"
command_prefix = ""
oasa_help_message = """📘 Commands

OASA <bus line>
👉 Shows the route of the bus line and real-time locations of the buses.

OASA <bus line> <stop name | stop code>
👉 Shows real-time arrival times for buses at a specific stop.
⚠️ Using the stop code is recommended as some stops may have the same name.

schedule <bus line>
👉 Shows the timetable for the selected bus line.
"""

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

@client.event
async def on_ready():
        print('Logged in as')
        print(client.user.name)
        print(client.user.id)
        print('------')
        await client.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Τα εξαφανισμένα λεωφορεία"))

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
                        lineCodes, lineDescr, mlCodes, sdc_codes = OASA.GetLineCodesWithMLInfo(busName)
                        if len(lineCodes) == 0:
                                await chan.send("Δε βρήκα κάποια γραμμή για το λεωφορείο {} φίλε/φίλη/φιλί :kiss: μου".format(busName))
                                return
                except requests.exceptions.ConnectionError:
                        await chan.send("Connection error when trying to get the line code(s)")
                        return
                except:
                        await chan.send(sys.exc_info())
 
                lineCode, lineIndex = await getLineCode(chan, lineCodes, lineDescr, busName, message)
                mlCode = mlCodes[lineIndex]
                try:
                        routeCodes, routeDescr, routeTypes = OASA.GetRouteCodes(busName, lineCode)
                except requests.exceptions.ConnectionError:
                        await chan.send("Connection error when trying to get the route code(s)")
                        return
                except TypeError:
                        await chan.send("Δε βρήκα διαδρομή για το λεωφορείο {} φίλε/φίλη/φιλί :kiss: μου".format(busName))
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
                                stop_codes, route_stop_orders = OASA.GetStopCode(stopName, routeCode)
                                stop = await getStopCode(chan, stop_codes, route_stop_orders, busName, message)
                                
                        if stop == "" or stop == "None":
                                await chan.send("Στάση {} εγώ πάντως δεν βρήκα. Μήπως κάναμε κανένα λαθάκι; ΗΛΙΘΙΕ".format(stopName))
                                return

                        try:
                                messageString = OASA.FindBusAtStop(busName, stop, routeType, lineCode, mlCode)
                                await chan.send(messageString)
                        except requests.exceptions.ConnectionError:
                                await chan.send("Server took too long to respond and I got bored")
                        except:
                                await chan.send(sys.exc_info())
                        

        elif msgUpper.startswith(command_prefix + "SCHEDUL") or msgUpper.startswith(command_prefix + "ΔΡΟΜΟΛ"):
                args = message.content.split(" ")
                if len(args) == 1:
                        await chan.send("με φώτισες.... ΠΟΙΟ ΛΕΩΟΦΟΡΕΙΟ ΘΕΣ ΡΕ **ΠΑΠΑΡΟΜΥΑΛΕ**????\n" + oasa_help_message)
                        return
                elif len(args) > 2:
                        await chan.send("Μονο ενα λεωφορειο δινουμε ρε **ΜΠΕΤΟΒΛΑΚΑ ΓΑΜΩ ΤΗ ΤΥΧΗ ΣΟΥ**\n" + oasa_help_message)

                await chan.typing()
                busName = args[1].upper()
                try:
                        lineCodes, lineDescr, mlCodes, sdc_codes = OASA.GetLineCodesWithMLInfo(busName)
                        if len(lineCodes) == 0:
                                await chan.send("Δε βρήκα κάποια γραμμή για το λεωφορείο {} φίλε/φίλη/φιλί :kiss: μου".format(busName))
                                return
                except requests.exceptions.ConnectionError:
                        await chan.send("Connection error when trying to get the line code(s)")
                        return
                except:
                        await chan.send(sys.exc_info())
                lineCode, lineIndex = await getLineCode(chan, lineCodes, lineDescr, busName, message)
                mlCode = mlCodes[lineIndex]
                try:
                        messageString = OASA.GetAllSchedules(busName, lineCode, mlCode)
                        await chan.send(messageString)
                except requests.exceptions.ConnectionError:
                        await chan.send("Server took too long to respond and I got bored")
                except:
                        await chan.send(sys.exc_info())


# Check if a string is in one of the strings of a given list.
def ListInString(theList, theString):
        for word in theList:
                if word in theString:
                        return True
        return False


async def getLineCode(chan, lineCodes, lineDescr, busName, message):
        if len(lineCodes) == 1:
                lineCode = lineCodes[0]
                return lineCode, 0
        else:
                line_msg = "Ποια εναλλακτική γραμμή του λεωφορείου {} σε ενδιαφέρει;\n\n".format(busName)
                for i, line in enumerate(lineDescr):
                        line_msg += line + " ({})\n".format(i + 1)
                await chan.send(line_msg)

                def check_if_same_author(m):
                        return message.author == m.author

                line = await client.wait_for("message", check = check_if_same_author)
                await chan.typing()
                line = line.content
                try:
                        lineInt = int(line)
                        if len(lineCodes) >= lineInt:
                                lineCode = lineCodes[lineInt - 1]
                                return lineCode, lineInt - 1
                        await chan.send("Μάθε να μετράς πρώτα ΑΝΘΡΩΠΑΚΙ... και μετά μίλα μου. Γκέγκε;")
                        return -1, -1
                except ValueError:
                        await chan.send("Ακούσε να δεις ΑΝΘΡΩΠΑΚΙ. Δεν θα με τρολάρεις ΕΣΥ ΕΜΕΝΑ, ΚΑΤΑΛΑΒΕΣ;")
                        return -1, -1


async def getRouteCode(chan, routeCodes, routeDescr, busName, message):
        if len(routeCodes) == 1:
                routeCode = routeCodes[0]
                return routeCode, 1
        else:
                route_msg = "Ποια διαδρομή του λεωφορείου {} σε ενδιαφέρει;\n\n".format(busName)
                for i, route in enumerate(routeDescr):
                        route_msg += route + " ({})\n".format(i + 1)
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

async def getStopCode(chan, stop_codes, route_stop_orders, busName, message):
        if len(stop_codes) == 0:
                return ""
        elif len(stop_codes) == 1:
                return stop_codes[0]
        else:
                stop_msg = "Βρέθηκαν πολλές στάσεις με το ίδιο όνομα στην ίδια λεωφορειακή γραμμή {}. Ποια από όλες σε ενδιαφέρει;\n\n".format(busName)
                for i, stop_order in enumerate(route_stop_orders):
                        stop_msg += "Η {}η με κωδικό στάσης {} ({})\n".format(stop_order, stop_codes[i], i + 1)
                await chan.send(stop_msg)

                def check_if_same_author(m):
                        return message.author == m.author

                chosen_stop = await client.wait_for("message", check = check_if_same_author)
                await chan.typing()
                chosen_stop = chosen_stop.content
                try:
                        chosen_stop_int = int(chosen_stop)
                        if len(stop_codes) >= chosen_stop_int:
                                stop_code = stop_codes[chosen_stop_int - 1]
                                return stop_code
                        await chan.send("Μάθε να μετράς πρώτα ΑΝΘΡΩΠΑΚΙ... και μετά μίλα μου. Γκέγκε;")
                        return -1
                except ValueError:
                        await chan.send("Ακούσε να δεις ΑΝΘΡΩΠΑΚΙ. Δεν θα με τρολάρεις ΕΣΥ ΕΜΕΝΑ, ΚΑΤΑΛΑΒΕΣ;")
                        return -1

client.run(TOKEN)
