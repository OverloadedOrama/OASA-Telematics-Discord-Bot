# -*- coding: utf8 -*-
import discord
from discord.ext.commands import Bot
from discord.ext import commands
import sys #for OASA exception
import requests #for OASA exception
import OASA_Scraper as OASA


client = commands.Bot(command_prefix = "")
@client.event
async def on_message(message):
        if message.author == client.user:
                return

        msgUpper = message.content.upper()
        chan = message.channel
        #Serious stuff
        if msgUpper.startswith("OASA") or msgUpper.startswith("ΟΑΣΑ"):
                args = message.content.split(" ")
                if len(args) == 2:
                        await chan.trigger_typing()
                        busName = args[1].upper()
                        routeCode = ""

                        try:
                                routeCodes, routeDescr, routeTypes = OASA.GetRouteCodes(busName)
                        except requests.exceptions.ConnectionError:
                                await chan.send("Connection error when trying to get the route code(s)")
                                return
                        except TypeError:
                                await chan.send("Δε βρήκα λεωφορείο {} φίλε/φίλη/φιλί :kiss: μου".format(busName))
                                return

                        if len(routeCodes) == 1:
                                routeCode = routeCodes[0]
                        else:
                                await chan.send("Ποια διαδρομή του λεωφορείου {} σε ενδιαφέρει;\n\n{} (1)\n{} (2)".format(busName, routeDescr[0],routeDescr[1]))
                                def int_check(m):
                                        try:
                                                mint = int(m.content)
                                                return (mint == 1 or mint == 2) and message.author == m.author
                                        except ValueError:
                                                return False

                                        
                                direction = await client.wait_for("message", check=int_check)
                                await chan.trigger_typing()
                                direction = direction.content
                                directionInt = int(direction)
                                routeCode = routeCodes[directionInt-1]

                        try:
                                img = OASA.FindBusLocation(busName, routeCode)
                        except requests.exceptions.ConnectionError:
                                await chan.send("Connection error when trying to get the bus location")
                                return
                        except:
                                await chan.send(sys.exc_info())
                                return

                        #if img is None:
                        #        await chan.send("No bus is found right now, RIP")
                        #        return
                        img = "BusLocation.png"
                        await chan.send(file=discord.File(img))
                elif len(args) > 2:
                        await chan.trigger_typing()
                        busName = args[1].upper()
                        stop = " ".join(args[2:]).upper()
                        stopName = stop
                        routeType = "1" #1 from start or if it's cyclic, 2 from end
                        #print(stop)
                        #if stop.isalpha():
                        if any(c.isalpha() for c in stop):
                                try:
                                        routeCodes, routeDescr, routeTypes = OASA.GetRouteCodes(busName)
                                except requests.exceptions.ConnectionError:
                                        await chan.send("Connection error when trying to get the route code(s)")
                                        return
                                except TypeError:
                                        await chan.send("Δε βρήκα λεωφορείο {} φίλε/φίλη/φιλί :kiss: μου".format(busName))
                                        return

                                if len(routeCodes) == 1:
                                        try:
                                                stop = OASA.GetStopCode(stopName, routeCodes[0])
                                        except requests.exceptions.ConnectionError:
                                                await chan.send("Connection error when trying to get the stop code")
                                                return
                                else:
                                        await chan.send("Ποια διαδρομή του λεωφορείου {} σε ενδιαφέρει;\n\n{} (1)\n{} (2)".format(busName, routeDescr[0],routeDescr[1]))
                                        def int_check(m):
                                                try:
                                                        mint = int(m.content)
                                                        return (mint == 1 or mint == 2) and message.author == m.author
                                                except ValueError:
                                                        return False

                                        
                                        direction = await client.wait_for("message", check=int_check)
                                        await chan.trigger_typing()
                                        direction = direction.content
                                        #print(direction)
                                        try:
                                                if direction == "1":
                                                        stop = OASA.GetStopCode(stopName, routeCodes[0])
                                                        routeType = routeTypes[0]
                                                elif direction == "2":
                                                        stop = OASA.GetStopCode(stopName, routeCodes[1])
                                                        routeType = routeTypes[1]
                                                        #print(routeType)
                                        except requests.exceptions.ConnectionError:
                                                await chan.send("Connection error when trying to get the stop code")
                                                return
                        try:
                                if stop == "":
                                       await chan.send("Στάση {} εγώ πάντως δεν βρήκα. Μήπως κάναμε κανένα λαθάκι; ΗΛΙΘΙΕ".format(stopName))
                                       return
                                messageString = OASA.FindBus(busName,stop, routeType)
                                await chan.send(messageString)
                                #await chan.send("{}\nΑνυπομονώ για τα self-driving λεωφορεία, μπας και δούμε καμία προκοπή στο τομέα των μεταφορών.".format(messageString))
                        except requests.exceptions.ConnectionError:
                                await chan.send("Server took too long to respond and I got bored")
                        except:
                                await chan.send(sys.exc_info())
                else:
                        await chan.send("Δώσε όνομα λεωφορείο και κωδικό στάσης... Τι περιμένεις να γίνει αλλιώς; Πχ OASA 824 400160")

        if msgUpper.startswith("SCHEDUL") or msgUpper.startswith("ΔΡΟΜΟΛ"):
                args = message.content.split(" ")
                if len(args) == 1:
                        await chan.send("με φώτισες.... ΠΟΙΟ ΛΕΩΟΦΟΡΕΙΟ ΘΕΣ ΡΕ **ΠΑΠΑΡΟΜΥΑΛΕ**????")
                elif len(args) == 2:
                        await chan.trigger_typing()
                        busName = args[1].upper()
                        try:
                                messageString = OASA.GetAllSchedules(busName)
                                await chan.send(messageString)
                        except requests.exceptions.ConnectionError:
                                await chan.send("Server took too long to respond and I got bored")
                        except:
                                await chan.send(sys.exc_info())
                else:
                        await chan.send("Μονο ενα λεωφορειο δινουμε ρε **ΜΠΕΤΟΒΛΑΚΑ ΓΑΜΩ ΤΗ ΤΥΧΗ ΣΟΥ**")

#client.loop.create_task(reaction_message_send())
client.run("YourTokenHere")
