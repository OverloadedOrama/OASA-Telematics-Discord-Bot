import requests
import datetime #for schedules
import json
from staticmap import StaticMap, CircleMarker, IconMarker, Line

API_ENDPOINT = "https://telematics.oasa.gr/api/"

# https://github.com/panosmz/oasatelematics
def telematics_request(query: str):
    req = requests.post(API_ENDPOINT + query)

    if req.text == 'null':
        # even though server returns null,
        # IT STILL RETURNS A 200 STATUS CODE FOR SOME REASON.
        req.status_code = 404

    try:
        req.raise_for_status()

    except (requests.exceptions.HTTPError,
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout):

        return []

    return req.json()


#Will be using webGetLines, webGetRoutes
def GetRouteCodes(busName):
	with open("webGetLines.json") as json_file:
		json_response = json.load(json_file)
	#json_response = telematics_request('?act=webGetLines')
	lineCode = ""
	for resp in json_response:
		if resp["LineID"] == busName:
			lineCode = resp["LineCode"]
			break

	if lineCode == "": #if bus has not been found
		return None
	json_response = telematics_request(f'?act=webGetRoutes&p1={lineCode}')
	routeCodes = []
	routeDescr = []
	routeTypes = []
	for resp in json_response:
		routeCodes.append(resp["RouteCode"])
		routeDescr.append(resp["RouteDescr"])
		routeTypes.append(resp["RouteType"])
		#if resp["LineCode"] == lineCode:

	return routeCodes, routeDescr, routeTypes


#Will be using webGetStops
def GetStopCode(stopName, routeCode):
	json_response = telematics_request(f'?act=webGetStops&p1={routeCode}')
	stop = ""
	for resp in json_response:
		if resp["StopDescr"] == stopName or resp["StopDescrEng"] == stopName:
			stop = resp["StopCode"]
			break

	return stop

#Will be using getStopNameAndXY
def GetStopNameGR(stopcode):
	json_response = telematics_request(f'?act=getStopNameAndXY&p1={stopcode}')
	nameGR = json_response[0]["stop_descr"]
	return nameGR

#Will be using webGetLinesWithMLInfo, getScheduleDaysMasterline
def GetCodesForSchedule(busName):
	#get bus linecode
	with open("webGetLinesWithMLInfo.json") as json_file:
		json_response = json.load(json_file)
	#json_response = telematics_request('?act=webGetLinesWithMLinfo')
	lineCode = ""
	mlCode = ""
	sdc_code = ""
	for resp in json_response:
		if resp["line_id"] == busName:
			lineCode = resp["line_code"]
			mlCode = resp["ml_code"]
			sdc_code = resp["sdc_code"]
			break
	if lineCode is not "":
		json_response = telematics_request(f'?act=getScheduleDaysMasterline&p1={lineCode}')
		sdc_code = ""
		sdc_code0 = ""
		sdc_code1 = ""
		sdc_code2 = ""
		day = datetime.datetime.today().weekday()
		sdc_code0 = json_response[0]["sdc_code"]
		if len(json_response) > 1:
			sdc_code1 = json_response[1]["sdc_code"]
			if len(json_response) > 2:
				sdc_code2 = json_response[2]["sdc_code"]

		if day == 5: #Saturday
			sdc_code = sdc_code1
		elif day == 6: #Sunday
			sdc_code = sdc_code2
		else: #Any other day
			sdc_code = sdc_code0

		return lineCode, mlCode, sdc_code, sdc_code0, sdc_code1, sdc_code2
	else:
		return None, None, None, None, None, None

#Will be using getDailySchedule and getSchedLines
def GetNextSchedule(busName, routeType):
	lineCode, mlCode, sdc_code, sdc_code0, sdc_code1, sdc_code2 = GetCodesForSchedule(busName)

	#Daily Schedules
	json_response = telematics_request(f'?act=getDailySchedule&line_code={lineCode}')
	if not json_response["go"] and not json_response["come"]:
		json_response = telematics_request(f'?act=getSchedLines&p1={mlCode}&p2={sdc_code}&p3={lineCode}')
	day = datetime.datetime.today().weekday()
	now = datetime.datetime.now()
	curYear = now.year
	curMonth = now.month
	curDay = now.day
	sched = None
	message = ""
	startOrEnd = ""
	sde_start = "sde_start{}".format(routeType)
	if routeType == "1":
		startOrEnd = "go"
	else:
		startOrEnd = "come"

	for resp in json_response[startOrEnd]:
		sched_string = resp[sde_start].replace("1900-01-01","{}-{}-{}".format(curYear,curMonth,curDay))
		sched = datetime.datetime.strptime(sched_string,"%Y-%m-%d %H:%M:%S")

		if sched > now: #true if it's the next schedule
			#message = "{}:{}:{}".format(sched.hour,sched.minute,sched.second)
			message = sched.strftime("%H:%M")
			break

	if message == "": #no more schedules for today, look for tomorrow
		if day == 4: #Friday
			if sdc_code1:
				sdc_code = sdc_code1 #get Saturday's code
			else:
				sdc_code = sdc_code0
		elif day == 5: #Saturday
			if sdc_code2:
				sdc_code = sdc_code2 #get Sunday's code
			else:
				sdc_code = sdc_code0
		else: #Sunday
			sdc_code = sdc_code0 #get Monday's code

		json_response = telematics_request(f'?act=getSchedLines&p1={mlCode}&p2={sdc_code}&p3={lineCode}')
		routes = json_response[startOrEnd]
		if not routes:
			if startOrEnd == "come":
				routes = json_response["go"]
			else:
				routes = json_response["come"]
		if not routes:
			return "Failed to find routes."
		firstSched = routes[0][sde_start]
		if "1900-01-01" in firstSched:
			message = firstSched.replace("1900-01-01 ","")
		elif "1900-01-02" in firstSched:
			message = firstSched.replace("1900-01-02 ","")
		elif "1900-01-03" in firstSched:
			message = firstSched.replace("1900-01-03 ","")
		message = message[:-3]

	return message

#Will be using getDailySchedule and getSchedLines
def GetAllSchedules(busName):
	lineCode, mlCode, sdc_code, sdc_code0, sdc_code1, sdc_code2 = GetCodesForSchedule(busName)
	if lineCode is None:
		return "Λεωφορείο {} δε βρήκα. Με έχετε κουράσει με τις **ΜΑΛΑΚΙΕΣ ΣΑΣ**.".format(busName)
	#for 218: ml_code = 287, sdc_code = 54 (for weekdays), line_code = 1035

	message = ""
	#Daily Schedules
	json_response = telematics_request(f'?act=getDailySchedule&line_code={lineCode}')
	if not json_response["go"] and not json_response["come"]:
		json_response = telematics_request(f'?act=getSchedLines&p1={mlCode}&p2={sdc_code}&p3={lineCode}')
		message += "Δεν βρέθηκαν δρομολόγια ημερήσιου προγραμματισμού, οπότε θα σου δώσω γενικά της ημέρας, τα οποία ίσως και να μην ισχύουν\n\n"
	#day = datetime.datetime.today().weekday()
	#now = datetime.datetime.now()
	#curYear = now.year
	#curMonth = now.month
	#curDay = now.day
	#sched = None
	message += json_response["go"][0]["line_descr"]
	message += "\n**Από αφετηρία:**\n"
	firstSched = json_response["go"][0]["sde_start1"].replace("1900-01-01 ","")
	schedHour = firstSched[:2]
	#schedHour = "05"

	for resp in json_response["go"]: #από αφετηρία
		sched_string = resp["sde_start1"]
		if "1900-01-01" in sched_string:
			sched_string = sched_string.replace("1900-01-01 ","")
		elif "1900-01-02" in sched_string:
			sched_string = sched_string.replace("1900-01-02 ","")
		elif "1900-01-03" in sched_string:
			sched_string = sched_string.replace("1900-01-03 ","")
		#sched_string = resp["sde_start1"].replace("1900-01-01 ","")
		#sched = datetime.datetime.strptime(sched_string,"%Y-%m-%d %H:%M:%S")
		sched_string = sched_string[:-3]

		if schedHour == sched_string[:2]: #check if it's the same hour
			message += sched_string + " "
		else:
			message += "\n" + sched_string + " "

		schedHour = sched_string[:2]
		#print(sched_string[:2])

	if json_response["come"]:
		firstSched = json_response["come"][0]["sde_start2"].replace("1900-01-01 ","")
		schedHour = firstSched[:2]
		message += "\n\n**Από τέρμα:**\n"

		for resp in json_response["come"]: #προς αφετηρία (από τέρμα δηλαδή)
			sched_string = resp["sde_start2"]
			if "1900-01-01" in sched_string:
				sched_string = sched_string.replace("1900-01-01 ","")
			elif "1900-01-02" in sched_string:
				sched_string = sched_string.replace("1900-01-02 ","")
			elif "1900-01-03" in sched_string:
				sched_string = sched_string.replace("1900-01-03 ","")
			sched_string = sched_string[:-3]

			if schedHour == sched_string[:2]: #check if it's the same hour
				message += sched_string + " "
			else:
				message += "\n" + sched_string + " "

			schedHour = sched_string[:2]
			#print(sched_string[:2])

	return message

#Will be using getStopArrivals, webRoutesForStop
def FindBus(busName, stop, routeType):
	json_response = telematics_request(f'?act=webRoutesForStop&p1={stop}')
	routeCodes = [] #2 values, one for regular and one for night shift
	btimes = []
	message = ""
	if json_response: #if the stop exists
		stopName = GetStopNameGR(stop)
		for resp in json_response: #loop through all routes in that stop
			if resp["LineID"] == busName:
				#routeCode = resp["RouteCode"]
				routeCodes.append(resp["RouteCode"])
				#break


		if routeCodes: #if routeCode has been found
			json_response = telematics_request(f'?act=getStopArrivals&p1={stop}')
			if json_response: #true when buses are coming in that stop
				for resp in json_response:
					if resp["route_code"] == routeCodes[0]:
						btimes.append(resp["btime2"])

					if len(routeCodes) > 1: #if there are night shifts
						if resp["route_code"] == routeCodes[1]:
							if not btimes: #if btimes is empty
								btimes.append(resp["btime2"])
							elif btimes[-1] is not resp["btime2"]: #so it won't count both times if they're the same
								btimes.append(resp["btime2"])
				if btimes:
					allMinutes = ", ".join(map(str, btimes))
					message = "Το λεωφορείο {} θα περάσει από την στάση {} σε {} λεπτά".format(busName, stopName, allMinutes)
				else: #bus has been found but it's not coming now
					nextSched = GetNextSchedule(busName, routeType)
					message = "Lmao, θα περιμένεις λιγάκι μάλλον γιατί το {} δε περνάει από την στάση {} αυτή τη στιγμή.\n\nΕπόμενο δρομολόγιο: {}".format(busName, stopName,nextSched)
			else: #no bus at all is coming now
				nextSched = GetNextSchedule(busName, routeType)
				message = "Lmao, θα περιμένεις λιγάκι μάλλον γιατί ΚΑΝΕΝΑ ΛΕΩΦΟΡΕΙΟ δε περνάει από την στάση {} αυτή τη στιγμή.\n\nΕπόμενο δρομολόγιο: {}".format(stopName,nextSched)

		else: #meaning the bus has not been found
			message = "Λεωφορείο {} στη στάση {} δε βρήκα. Μήπως γράψαμε κάτι λάθος; Ε;".format(busName, stopName)
	else:
		message = "Δε βρέθηκε στάση {} ρε. Που τα σκέφτεστε αυτά;".format(stop)

	return message

#Will be using getBusLocation
def FindBusLocation(busName, routeCode):
	#routeCode = "2006"
	json_response = telematics_request(f'?act=getBusLocation&p1={routeCode}')
	#busCoordinateList = []
	stopCoordinateList = []
	#zoomValue = 14
	m = StaticMap(1200, 1200)
	if json_response:
		for resp in json_response:
			CS_LNG = float(resp["CS_LNG"])
			CS_LAT = float(resp["CS_LAT"])
			marker = IconMarker([CS_LNG,CS_LAT], "BusMarker.png", 17,62)
			m.add_marker(marker)
			#busCoordinateList.append([CS_LNG,CS_LAT])

		#for coordinate in busCoordinateList:
			#marker = CircleMarker(coordinate, '#4286f4', 12)

			#zoomValue -= 1

	json_response = telematics_request(f'?act=webGetStops&p1={routeCode}')
	for resp in json_response:
		StopLng = float(resp["StopLng"])
		StopLat = float(resp["StopLat"])
		stopCoordinateList.append([StopLng,StopLat])

	#for coordinate in stopCoordinateList:
	#	marker = CircleMarker(coordinate, '#4286f4', 12)
	#	m.add_marker(marker)

	firstStop = CircleMarker(stopCoordinateList[0], '#37fc4b', 12) #first stop
	lastStop = CircleMarker(stopCoordinateList[-1], '#f45c42', 12) #last stop
	m.add_marker(firstStop)
	m.add_marker(lastStop)

	line = Line(stopCoordinateList,'#4286f4',4) #draw a line through all stops, which is basically the route itself
	m.add_line(line)

	mapImg = m.render()
	mapImg.save("BusLocation.png")
	return mapImg
	#else:
	#	return None
