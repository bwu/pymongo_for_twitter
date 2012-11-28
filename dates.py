#!/path/to/python

import datetime
from datetime import date, timedelta, datetime, tzinfo
import pytz
from pytz import timezone

# Convert from UTC time to Eastern time
def convertToEST(time):
	try:
		eastern = timezone('US/Eastern')
		utc = pytz.utc
		new_time = utc.normalize(utc.localize(time)).astimezone(eastern)
		return new_time
	except ValueError:
		eastern = timezone('US/Eastern')
		utc = pytz.utc
		new_time = time.astimezone(eastern)
		return new_time	

# Convert from UTC time to Eastern time from a time naive of tzinfo
def convertToESTFromNaive(time):
	eastern = timezone('US/Eastern')
	utc = pytz.utc
	new_time = utc.normalize(utc.localize(time)).astimezone(eastern)
	return new_time

# Return todays date in the format YYYY-MM-DD
def returnToday():
	today = convertToESTFromNaive(datetime.now()).strftime("%Y-%m-%d")
	return today

# Return todays date in the format YYYY-MM-DD, HH:MM:SS
def returnNow():
	now = convertToESTFromNaive(datetime.now()).strftime("%Y-%m-%d, %H:%M:%S")
	return now

# Function that creates an array of dates, enter the dates in the form "mm/dd/yy"
def createDates(start_date, end_date):
	try:
		# variables and constants used to create the date list
		converted_start = datetime.strptime(start_date, '%m/%d/%y').date()
		converted_end = datetime.strptime(end_date, '%m/%d/%y').date()
		elapsed = converted_end - converted_start
		timedel = elapsed.days
		dates = []
		
		# turn the start and end date into a list
		i = 0
		while i < timedel + 1:
			date = converted_start.strftime("%m/%d/%y")
			dates.append(date)
			converted_start += timedelta(1)
			i += 1
		return dates
		
	except KeyboardInterrupt:
		# Print the error and exit
		print "Keyboard Interrupt!"
		sys.exit()
	
	except:
		# Print other error:
		print "Fail! createDates failed. Details - "
		print "  ", sys.exc_info()[:2]