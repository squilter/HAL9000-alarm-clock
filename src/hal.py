#Copyright (c) 2014, squilter
#Some code copied from Devon, dev@esologic.com http://www.esologic.com/?p=634

import getopt
import sys
import string
import time
import os
import feedparser
import subprocess
import signal
import datetime
import urllib2
import ConfigParser

from time import mktime
from datetime import date
import RPi.GPIO as GPIO
import gdata.calendar.service
import gdata.service
import atom.service
import gdata.calendar
import gdata.calendar
import atom
from feed.date.rfc3339 import tf_from_timestamp #also for the comparator

def blink(pin):
        GPIO.output(pin,GPIO.HIGH)
        time.sleep(2)
        GPIO.output(pin,GPIO.LOW)
        
#Do we have internet?
def internet_on():
    try:
        response=urllib2.urlopen('http://8.8.8.8',timeout=1)
        return True
    except urllib2.URLError as err: pass
    return False
    
def days_until_school_ends():
    today = datetime.date.today()
    schoolends = datetime.date(2014,6,19)#jun19
    return (schoolends-today).days
    
def get_todays_events(calendar_service):
    query = gdata.calendar.service.CalendarEventQuery('default', 'private', 'full')
    today=str(date.today())
    tomorrow=str(date.today()+datetime.timedelta(days=1))
    query.start_min = today
    query.start_max = tomorrow
    feed = calendar_service.CalendarQuery(query)
    to_return=""
    for i, an_event in enumerate(feed.entry):
        for a_when in an_event.when:
            to_return.append(an_event.title.text ,"at",time.strftime('%H:%M',time.localtime(tf_from_timestamp(a_when.start_time))))
    return to_return

def time_to_wake(calendar_service,text_query="wake"):
    print "polling calendar"
    query = gdata.calendar.service.CalendarEventQuery('default', 'private', 'full', text_query)
    today=str(date.today())
    tomorrow=str(date.today()+datetime.timedelta(days=1))
    query.start_min = today
    query.start_max = tomorrow
    feed = calendar_service.CalendarQuery(query)
    for i, an_event in enumerate(feed.entry):
        for a_when in an_event.when:
            print "wake scheduled for: " + time.strftime('%H:%M',time.localtime(tf_from_timestamp(a_when.start_time)))
            if time.strftime('%d-%m-%Y %H:%M',time.localtime(tf_from_timestamp(a_when.start_time))) == time.strftime('%d-%m-%Y %H:%M'):
                print "That's now!"
                return True
            else:
                pass #the "wake" event's start time != the system's current time
    return False

def wake_up():
    #play tracking sound (beeping.  For wake up). stop and continue on button push
    alarmsound = subprocess.Popen("mplayer /home/pi/HAL/sounds/trackingbeep.wav",shell=True)
    while alarmsound.poll()==None:
        time.sleep(0.1)
        if GPIO.input(12):
            os.kill(alarmsound.pid+1,signal.SIGINT)
            break
        
    #if internet is down, say "i don't have that information" and end
    if not internet_on():
        subprocess.Popen("mplayer /home/pi/HAL/sounds/donthaveinfo.wav",shell=True)
        GPIO.output(11,GPIO.LOW)
        GPIO.cleanup()
        return
        
    #prepare a message to be read
    message = ""
    
    #get login info from conf file
    config=ConfigParser.RawConfigParser()
    config.read("./logins.conf")
    
    #get all info and append to message
    
    #emails - Read emails from last 10 hours.  Don't bother checking more than the 5 most recent ones.
    HALUSERNAME = config.get("hal", "login")
    HALKEY = config.get("hal","password")
    response = feedparser.parse("https://" + HALUSERNAME + ":" + HALKEY + "@mail.google.com/gmail/feed/atom")
    unread_count = int(response["feed"]["fullcount"]) 
    now = datetime.datetime.now()
    for i in range(0,5):
        then= datetime.datetime.fromtimestamp(mktime(response['items'][i].updated_parsed))
        if (now-then) < datetime.timedelta(hours=10):
            message += response['items'][i].title + ",\n"#comma seems to add a delay between messages.  Multiple commas doesn't make it better though.
            
    #calendar
    message+=get_todays_events(calendar_service)
    
    #days until school ends.
    message += str(days_until_school_ends()) + " Days until summer,"
    
    #remove " character to prevent shell injection
    message = message.replace("\""," ")
    
    #Help with hal's speech impediments
    message = message.replace("Metrorail Alert","Red Line Delays")
    
    #read message. Interrupt if button pushed.
    print message
    speaking_process = subprocess.Popen("flite \""+ message +"\"",shell=True)
    while speaking_process.poll()==None:
        time.sleep(0.1)
        if GPIO.input(12):
            os.kill(speaking_process.pid+1,signal.SIGINT)
            break

#configuration stuffs:!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!1
#prepare button
button=12
GPIO.setmode(GPIO.BOARD)
GPIO.setup(button,GPIO.IN)
#Turn on eye
eye=11
GPIO.setmode(GPIO.BOARD)
GPIO.setup(eye, GPIO.OUT)
#Calendar configs
config=ConfigParser.RawConfigParser()
config.read("./logins.conf") 
SEBUSERNAME = config.get("seb", "login")
SEBKEY = config.get("seb","password") 
calendar_service = gdata.calendar.service.CalendarService()
calendar_service.email = SEBUSERNAME+"@gmail.com" #your email
calendar_service.password = SEBKEY #your password
calendar_service.source = 'Google-Calendar_Python_Sample-1.0'
calendar_service.ProgrammaticLogin()

light=False#True means lamp is on, False is off
lamp=22
GPIO.setup(lamp, GPIO.OUT)
GPIO.output(lamp,GPIO.LOW)
switch=12
GPIO.setup(switch,GPIO.IN)
led=11
GPIO.setup(led, GPIO.OUT)
while 1:
    for _ in range(105):
        if GPIO.input(switch) and light:
            GPIO.output(lamp,GPIO.LOW)
            blink(led)
            light=False
        if GPIO.input(switch) and not light:
            GPIO.output(lamp,GPIO.HIGH)
            blink(led)
            light=True
        time.sleep(0.15)
    if time_to_wake(calendar_service):
        wake_up()
