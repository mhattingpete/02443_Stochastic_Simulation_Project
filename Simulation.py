import numpy as np
import heapq

Status = {True:"Idle",False:"Busy"}
ActiveStatus = {True:"Active",False:"Inactive"}

class Server:
	def __init__(self,id):
		self.id = id
		self.idle = True

	def setIdle(self):
		self.idle = True

	def setBusy(self):
		self.idle = False
		
	def __repr__(self):
		return "Server {} is {}".format(self.id,Status[self.idle])


class ArrivalProcess:
	def __init__(self,id):
		self.id = id
		self.active = True
		self.idle = False
		
	def setActive(self):
		self.active = True
	
	def setInactive(self):
		self.active = False
		
	def setIdle(self):
		self.idle = True
		
	def setBusy(self):
		self.idle = False
		
	def __repr__(self):
		return "ArrivalProcess {}, is {} and {}".format(self.id,ActiveStatus[self.active],Status[self.idle])


class Queue:
	def __init__(self,size=None):
		self.size = size
		self.Q = []
		self.Qlen = []
		self.Qtime = []
		
	def isempty(self):
		if self.Q:
			return False
		else:
			return True
	
	def depositToQueue(self,arrtime):
		#arrtime is the arrival time
		if arrtime:
			if (self.size is None) or (self.size >= len(self.Q)+1 and self.size > 0):
				self.Q.append(arrtime)
				self.Qlen.append([arrtime,len(self.Q)])
				return True
			else:
				return False
	
	def drawFromQueue(self,Time):
		#Time is current time
		q0 = self.Q.pop(0)
		self.Qtime.append(Time-q0)
		if self.Q:
			self.Qlen.append([Time,len(self.Q)])
		else:
			self.Qlen.append([Time,0])
	
	def generateQueueTime(self,num=1):
		if self.queueTime:
			return self.queueTime(num)
		else:
			return 0
		
	def __repr__(self):
		size = self.size if self.size is not None else "Inf"
		return "Queue with size {} and current load is {}".format(size,len(self.Q))


class Simulation:
	def __init__(self,num_servers,interarrival,service,stateGen=None,superpositions=1,queue_size=None):
		# Number of servers
		self.num_servers = num_servers
		self.servers = [Server(i) for i in range(num_servers)]
		
		# Queue
		# if queue_size is none then queue is infinite
		self.queue = Queue(queue_size)
		
		# function that generates interarrival times
		self.interarrivalGen = interarrival
		
		# function that generates service times
		self.serviceGen = service
		
		# if stateGen tuple is given then split into stateGenOnToOff and stateGenOffToOn
		if stateGen:
			stateGenOnToOff,stateGenOffToOn = stateGen
			self.stateGenOnToOff = stateGenOnToOff
			self.stateGenOffToOn = stateGenOffToOn
			
			# generate initial state change times
			init_states = self.generateState(superpositions)
			self.stateGen = True
		else:
			# if stateGen is none then we don't use IPP but PP instead
			init_states = []
			self.stateGen = False
		
		# number of arrival processes
		self.superpositions = superpositions
		
		# define arrival processes
		self.arrivalprocesses = [ArrivalProcess(i) for i in range(superpositions)]
		
		# set initial clock
		self.clock = 0.0
		
		# create event list
		self.events = []
		
		# get initial arrivals
		init_arrivals = self.generateInterarrival(superpositions)
		
		# add state changes to event list
		for indx,e in enumerate(init_states):
			heapq.heappush(self.events,(e,('StateChange',indx)))
		
		# add arrivals to event list
		for indx,e in enumerate(init_arrivals):
			heapq.heappush(self.events,(e,('Arrival',indx,e)))
			
		# statistics to be gathered
		self.num_arrivals = 0
		self.enqueued = 0
		self.num_departed = 0
		self.num_blocked = 0
		self.arrivalTimes = []
		self.serviceActivityTimes = []
		self.serviceTime = np.min(init_arrivals)
		
	# find idle servers
	def serversIdle(self):
		for i,s in enumerate(self.servers):
			if s.idle:
				return i
		return None

	# advance time one step, get and handle next event
	def advanceTime(self):
		# get next event
		#print(self.events)
		event = heapq.heappop(self.events)
		# set clock to next event time
		self.clock = event[0]
		# get event type
		event_type = event[1][0]
		# get index from event (either the index of the server of arrival process)
		indx = event[1][1]
		if event_type == 'StateChange':
			if self.stateGen:
				self.handleStateChange(indx)
		elif event_type == 'Arrival':
			old_arrivaltime = event[1][2]
			self.handleArrivalEvent(indx,old_arrivaltime)
		elif event_type == 'Service':
			self.handleDepartEvent(indx)
			
	# handle state change event
	def handleStateChange(self,indx):
		arrivalProcess = self.arrivalprocesses[indx]
		if arrivalProcess.active == False:
			arrivalProcess.setActive()
			statetime = self.generateState(currentState=arrivalProcess.active)[0]
			heapq.heappush(self.events,(statetime+self.clock,('StateChange',indx)))
			if arrivalProcess.idle:
				arrivaltime = self.generateInterarrival()[0]
				heapq.heappush(self.events,(arrivaltime+self.clock,('Arrival',indx,arrivaltime)))
				arrivalProcess.setBusy()
		else:
			arrivalProcess.setInactive()
			statetime = self.generateState(currentState=arrivalProcess.active)[0]
			heapq.heappush(self.events,(statetime+self.clock,('StateChange',indx)))

	# handle arrival event
	def handleArrivalEvent(self,indx,old_arrivaltime):
		self.num_arrivals += 1
		arrivalProcess = self.arrivalprocesses[indx]
		arrivalProcess.setIdle()
		if arrivalProcess.active == False:
			pass
		else:
			self.arrivalTimes.append(old_arrivaltime)
			arrivaltime = self.generateInterarrival()[0]
			serverIndx = self.serversIdle()
			if serverIndx is not None:
				servicetime = self.generateService()[0]
				heapq.heappush(self.events,(servicetime+self.clock,('Service',serverIndx)))
				heapq.heappush(self.events,(arrivaltime+self.clock,('Arrival',indx,arrivaltime)))
				self.servers[serverIndx].setBusy()
			else:
				if self.queue.depositToQueue(self.clock):
					self.enqueued += 1
				else:
					self.num_blocked += 1
				heapq.heappush(self.events,(arrivaltime+self.clock,('Arrival',indx,arrivaltime)))

	# handle service event - which is actually a departure
	def handleDepartEvent(self,indx):
		self.servers[indx].setIdle()
		self.num_departed += 1
		if self.queue.isempty() == False:
			timeQueued = self.queue.drawFromQueue(self.clock)
			self.servers[indx].setBusy()
			servicetime = self.generateService()[0]
			heapq.heappush(self.events,(servicetime+self.clock,('Service',indx)))
		else:
			self.serviceActivityTimes.append(self.clock-self.serviceTime)
			self.serviceTime = self.clock
			
	# generate next interarrival time
	def generateInterarrival(self,num=1):
		return self.interarrivalGen(num)

	# generate next service time
	def generateService(self,num=1):
		return self.serviceGen(num)
	
	# generate next state change time
	def generateState(self,num=1,currentState=1):
		if currentState == 1:
			return self.stateGenOnToOff(num)
		else:
			return self.stateGenOffToOn(num)