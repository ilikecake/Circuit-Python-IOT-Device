'''MIT License

Copyright (c) 2024 ilikecake

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

from adafruit_datetime import time as time_obj
import time

#TODO: Handle both time and datetime


class timer:
    def __init__(self):
        #TODO: Read all data from the config file into private variables
        self._OutputList = []
        self._EventList = [{"time": time_obj(0, 0)}]

    def AddOutput(self, OutputToAdd):
        #TODO: check if output is already in the list, make sure output is a string.
        if not isinstance(OutputToAdd, str):
            raise TypeError("Output name must be a string")
        
        if OutputToAdd not in self._OutputList:
            self._OutputList.append(OutputToAdd)
            self._OutputList.sort() #TODO: I dont think I need this.
        else:
            #Not sure if we want to raise this error here. We could fail silently and eveything 
            #would probably work. However, attempting to add an output twice is probably an error
            #that the user would want to know about.
            raise ValueError(f"{OutputToAdd} is already in the list")
        
    def DisplayOutputs(self):
        print(self._OutputList)
        
    def AddEvent(self, EventToAdd):
        #Make sure the event has a 'time' key
        if not ('time' in EventToAdd):
            raise NameError("The key 'time' must be in the dictionary")
        
        #Check if there are keys in the event that dont correspond to outputs. If so, raise an error.
        UnknownItems = [k for k in EventToAdd.keys() if k not in self._OutputList]
        if len(UnknownItems) > 1:
            UnknownItems.remove('time')
            raise ValueError(f"Unknown item(s) in event: {UnknownItems}")
        
        #Make sure time is in the right format. We can support time or time_struct.
        if isinstance(EventToAdd['time'], time.struct_time):
            #We are given a time in time_struct format. Sorting of time_struct objects is not 
            #supported. Convert to a time object.
            TimeToAdd = time_obj(EventToAdd['time'].tm_hour, EventToAdd['time'].tm_min)
            EventToAdd['time'] = TimeToAdd
        elif not isinstance(EventToAdd['time'], time_obj):
            #We are not given either a time or time_struct object.
            raise TypeError('Time must be a time or time_struct object')
        
        for key in EventToAdd:
            if key != 'time':
                EventToAdd[key]['calc'] = False
                try:
                    #EventToAdd[key]['type'] #TODO: Catch bad event types here.
                    if EventToAdd[key]['type'] == 'ramp':
                        #TODO: This will do something wierd if start time and end time are on different days.
                        #Y is value, X is time. Calculate slope and intercept.
                        EventToAdd[key]['m'] = (EventToAdd[key]['EndValue'] - EventToAdd[key]['StartValue'])/((EventToAdd[key]['EndTime'].hour*60 + EventToAdd[key]['EndTime'].minute) - (EventToAdd[key]['StartTime'].hour*60 + EventToAdd[key]['StartTime'].minute))
                        EventToAdd[key]['b'] = EventToAdd[key]['StartValue'] - EventToAdd[key]['m']*(EventToAdd[key]['StartTime'].hour*60 + EventToAdd[key]['StartTime'].minute)
                except KeyError as e:
                    #str(e) will be the name of the nonexsistent key.
                    if str(e) == "type":
                        #There is an event at time 0 that is not calculated. Leave this alone.
                        raise ValueError(f"{key} must have a 'type' key")
        
        #TODO: Make sure that StartTime and event time are the same for ramp events.
        
        #Check to see if the event time we are trying to add is already in the list.
        #If so, update the current event with the new states.
        for event in self._EventList:
            if event['time'] == EventToAdd['time']:
                #TODO: Does this overwrite the time key?
                for key, value in EventToAdd.items():
                    event[key] = value
                #If we are updating an exsisting event, the list is already sorted.
                #Must call this to rebuild the calculated events.
                self.GenerateEventTable()
                return

        #If the event time is not currently in the list, add a new event and resort the list.
        self._EventList.append(EventToAdd)
        self._EventList.sort(key=lambda val: val['time'])
        
        #Must call this to rebuild the calculated events.
        self.GenerateEventTable()
    
    
    def RemoveEvent(self, EventToRemove):
        #Make sure the event has a 'time' key
        if not ('time' in EventToRemove):
            raise NameError("The key 'time' must be in the dictionary")
        
        #Check if there are keys in the event that don't correspond to outputs. If so, raise an 
        #error. Probably not needed for removing an event, but if this happens, it is probably an 
        #name error, so we should highlight that.
        UnknownItems = [k for k in EventToRemove.keys() if k not in self._OutputList]
        if len(UnknownItems) > 1:
            UnknownItems.remove('time')
            raise ValueError(f"Unknown item(s) in event: {UnknownItems}")
        
        #Make sure time is in the right format. We can support time or time_struct.
        if isinstance(EventToRemove['time'], time.struct_time):
            #We are given a time in time_struct format. Sorting of time_struct objects is not 
            #supported. Convert to a time object.
            TimeToAdd = time_obj(EventToRemove['time'].tm_hour, EventToRemove['time'].tm_min)
            EventToRemove['time'] = TimeToAdd
        elif not isinstance(EventToRemove['time'], time_obj):
            #We are not given either a time or time_struct object.
            raise TypeError('Time must be a time or time_struct object')
        
        #Look for the event in the list
        for event in self._EventList:
            if event['time'] == EventToRemove['time']:
                for eventName in EventToRemove:
                    #Remove keys from the event
                    if eventName is not 'time':
                        event.pop(eventName, None)
                if (len(event) < 2) and (event['time'] is not time_obj(0,0)):
                    #If all the keys for this event other than 'time' are removed. Remove the entire
                    #event from the list. Note that we don't want to do this for the 00:00 event.
                    self._EventList.remove(event)
        
        #Must call this to rebuild the calculated events.
        self.GenerateEventTable()
                
    '''
    Covenience function to output the event table in a human readable format.
     - ShowCalc: Set to True to show calculated events in the table
     - ShowRaw : Set to True to instead print the raw event list
    '''
    #TODO: Show AM/PM
    def ShowEventList(self, ShowCalc = False, ShowRaw = False):
        NameLength = 4
        ValLength = 7
        
        if ShowRaw:
            print(self._EventList)
        else:
            for event in self._EventList:
                for key in event:
                    if len(key) > NameLength:
                        NameLength = len(key)
            
            NameLength = NameLength+1
            EventNameStr = '{:<'+str(NameLength)+'}|'
            ValStr = '{: ^'+str(ValLength)+'}|'
            line = EventNameStr.format('time')
            
            for event in self._EventList:
                TimeStr = '{:02d}:{:02d}'.format(event['time'].hour, event['time'].minute)
                line = (line + ValStr).format(TimeStr)
            
            Seperator = ''
            for i in range (0, len(line)):
                Seperator = Seperator + '-'
            
            print(Seperator)
            print(line)
            print(Seperator)
            
            for output in self._OutputList:
                line = EventNameStr.format(output)
                for event in self._EventList:
                    if event[output]['type'] == 'value':
                        StrToAdd = ValStr.format(event[output]['value'])
                    elif event[output]['type'] == 'ramp':
                        StrToAdd = ValStr.format('R'+str(event[output]['StartValue']))
                    else:
                        raise ValueError(f"Unknown event type {event[output]['type']}")
                    
                    if event[output]['calc'] is True:
                        if ShowCalc:
                            line = line + StrToAdd
                        else:
                            line = line + ValStr.format(' ')
                    else:
                        line = line + StrToAdd
                    
                    #try:
                    #    if event[output]['calc'] is True:
                    #        if ShowCalc:
                    #            line = line + ValStr.format(event[output]['value'])
                    #        else:
                    #            line = line + ValStr.format(' ')
                    #    elif event[output]['type'] == 'ramp':
                    #        if ShowCalc:
                    #            line = line + ValStr.format(event[output]['StartValue'])
                    #        else:
                    #            line = line + ValStr.format(' ')
                    #    else:
                    #        #TODO: In the future we can probably add other if/else statements here to handle more complicated events.
                    #        line = line + ValStr.format(event[output]['value'])
                    #except KeyError:
                    #    line = line + ValStr.format(event[output]['value'])
                print(line)
                print(Seperator)
        
    def GenerateEventTable(self):
        #TODO: Handle if either the output list or event list is blank.
        #TODO: What do we do if something is in the output list but not in the event list, what about the opposite?
        #TODO: WHat if an output is in the output list but not in any events?
        
        #Find the last entry for each output. This becomes the starting state for each output.
        for Output in self._OutputList:
            #Step through each output on the list.
            
            #This block is meant to check if any events at time 0 are 'real'. If this is true, 
            # skip the rest of this loop.
            try:
                #if self._EventList[0][Output]['type'] != 'calc':
                if self._EventList[0][Output]['calc'] is False:
                    #There is an event at time 0 that is not calculated. Leave this alone.
                    continue
            except KeyError as e:
                #e is 'type' if the event exsists but does not have a 'type' key.
                #e is equal to Output if the output does not exsist.
                if str(e) == "type":
                    #There is an event at time 0 that is not calculated. Leave this alone.
                    continue                    
            
            #Step through each event in the table in reverse order. Look for the first real event.
            EventFound = False
            for event in reversed(self._EventList):
                try:
                    DictFound = event[Output]
                    if DictFound['calc'] is False:
                        #Found a non-calculated event. Copy it to time 0.
                        self._EventList[0][Output] = DictFound.copy()  
                        self._EventList[0][Output]['calc'] = True
                        EventFound = True
                        break
                except KeyError as e:
                    #e is 'type' if the event exsists but does not have a 'type' key.
                    #e is equal to Output if the output does not exsist.
                    if str(e) == "type":
                        #Output exsists, but does not have a 'type' key. This is a real event.
                        self._EventList[0][Output] = DictFound.copy()  
                        self._EventList[0][Output]['calc'] = True
                        EventFound = True
                        break
                    pass
                
            #Deal with the case where there is an output on the list but no events associated with it.
            if not EventFound:
                self._EventList[0][Output] = {"value": False}   #TODO: This sets to the state to false if there are no entries in the event table. Is this right?
                self._EventList[0][Output]['calc'] = True

        #Now that we have fully populated the time 0 event, we can step through all the rest of
        # the events and determine what all the outputs should be at that time. We add or update
        # events to each time so that we always have all outputs at each even. If we add an event
        # that is not given by the user, we give it type 'calc'.
        i = 0
        for event in self._EventList:
            if i > 0:
                for Output in self._OutputList:
                    try:
                        if event[Output]['calc'] is True:
                            #Event found, but it is a calculated event. Update it from the previous event.
                            event[Output] = self._EventList[i-1][Output].copy()
                            event[Output]['calc'] = True
                    except KeyError as e:
                        #e is 'type' if the event exsists but does not have a 'type' key.
                        #e is equal to Output if the output does not exsist.
                        if str(e) != "type":
                            #Event not found. Add a calculated event to make state determination easier.
                            event[Output] = self._EventList[i-1][Output].copy()
                            event[Output]['calc'] = True
            i = i+1
        
    def GetCurrentState(self, TheTime):
        if isinstance(TheTime, time.struct_time):
            #We are given a time in time_struct format. Convert to a time object.
            CurrentTime = time_obj(TheTime.tm_hour, TheTime.tm_min)
        elif not isinstance(TheTime, time_obj):
            #We are not given either a time or time_struct object.
            raise TypeError('Time must be a time or time_struct object')
        else:
            CurrentTime = TheTime
        
        #Find the index of the latest event in the past.
        i = 0
        for event in self._EventList:
            #Note: Even though we have a > instead of a >= here, if there is an event at 
            # CurrentTime, that event index will be used.
            if event['time'] > CurrentTime:
                break
            else:
                i = i+1
                
        #i is the index of the latest event in the past.
        i = i-1     
        
        ReturnState = {}
        for key in self._EventList[i]:
            if key == 'time':
                ReturnState['time'] = self._EventList[i]['time']
            elif self._EventList[i][key]['type'] == 'value':
                #Event type: value
                ReturnState[key] = self._EventList[i][key]['value']
            elif self._EventList[i][key]['type'] == 'ramp':
                if CurrentTime >= self._EventList[i][key]['EndTime']:
                    ReturnState[key] = self._EventList[i][key]['EndValue']
                else:
                    ReturnState[key] = self._EventList[i][key]['m']*(CurrentTime.hour*60 + CurrentTime.minute)+self._EventList[i][key]['b']
            else:
                raise ValueError(f"Unknown event type {self._EventList[i-1][key]['type']}")
                
        return ReturnState
        
        