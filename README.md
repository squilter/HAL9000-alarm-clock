HAL9000-alarm-clock
===================
WORK IN PROGRESS!  Released under BSD 2-clause license.

This alarm clock wakes me up in the morning and tells me some useful information.
It will tell me about metro/bus delays, traffic, weather, today's calendar events...
The alarm can be set by creating an event called "wake" in your calendar.  

It is based on hardware created here:
https://learn.adafruit.com/hal-9000-replica/overview

It was then mounted above my bed and was given a raspberry pi.  The pi has wifi and USB audio (internal audio created background noise) thru a usb hub.
It is also connected to HAL's button, HAL's LED and my lamp (thru a powerswitch tail v2).

HAL has his own email address.  Whenever the alarm goes off, HAL will read the subject line of any emails from the past 12 hours (no more than 5 emails). This makes it easy to set up any new reminders (especially with IFTTT)*.
HAL polls for "wake" events on my personal calendar, so he also has access to my main gmail account, specified in "logins.conf".

*NOTE: right now, HAL pipes phrases it wants to say into a shell command ("flite <message>").  This makes it susceptible to shell injection if somebody knows HAL's email.  The " character is removed to mitigate this, but i'll admit that this is a pretty big problem.  Please do recommend suggestions.
