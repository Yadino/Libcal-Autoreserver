# Version 2.2 - Smart Nestor log in that works in pre-logged in states
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
import datetime
import time
import getpass

#====================== CONFIG: ====================

TEST = False # Put False to make the script work
VERBAL = True # Put True to get more verbal output
REFRESH_RATE = 5	 # Exactly what it sounds like, in seconds, dont make lower than 1
LOAD_WAIT = 2 # How long to wait for page to load, increase if connection is slow

# REQUIRED FIELDS - use "" around each value
phone = "0699999999"
s_number = "s9999999"

# Nestor password field - Leave empty ("") to securely input your password every time you run the code, or fill in your password here if you're lazy to automate the process (less secure)
nestor_password = "replace with your Nestor password"

# WHEN AND WHERE TO MAKE THE RESERVATION
# "8:30am", "1:00pm" or "6:00pm"
c_time = "1:00pm"

# OCT, NOV, DEC and so on, just look at the way its written on the little calendar symbol
c_month = "JUN"

# number of the day of month (1-31)
c_day = "15"

# "1st", "2nd" or "3rd", leave empty ("") for no preference
floor = ""

#==================== CONFIG END =====================

# TODO: Randomize wait time, Add GUI, Put in exe and mac equivalent, Add time limit option, Add delayed start option?, Add timer to ignore list

def screenshot(driver):
	# note- doesnt work lol
	# Take a screenshot because wtf
	scrnsht_name = "screenshot_"+ str(datetime.datetime.now()) +".png"
	driver.get_screenshot_as_file(scrnsht_name)
	print "================ screenshot taken: ", scrnsht_name


if TEST:
	phone = "TEST" # Won't send form this way

if nestor_password == "":
	print("Please fill in your nestor password and press Enter.\nMake sure that you type the password in correctly because you can't see what you type!")
	nestor_password = getpass.getpass('Password:')

options = webdriver.ChromeOptions()
options.add_argument("--start-maximized")
driver = webdriver.Chrome(chrome_options=options)

start_time = datetime.datetime.now()
interation_count = 0
pass_fail_count = 0
ignore_list = dict() # a list of "fake" ribbons of places that had already been reserved

print "Script started with details: ", s_number, phone
print "Start time: ", start_time
if TEST:
	print "=================NOTE: DRY RUN! TEST IS SET TO VALUE: TRUE=====================\n"

# Infinite loop until exit
while True:
	
	interation_count+=1
	print "Refresh no.", interation_count, "    Time elapsed:", datetime.datetime.now() - start_time
	
	if REFRESH_RATE > LOAD_WAIT:
		time.sleep(REFRESH_RATE - LOAD_WAIT)	
	
	driver.get('https://libcal.rug.nl/calendar/studyplace/?cid=7564&t=g&d=0000-00-00&cal=7564&inc')
	
	time.sleep(LOAD_WAIT)
	
	# Clear ignore list every ~5 minutes, roughtly by calculating refresh rate cause I'm lazy
	if interation_count%20 == 0:
		ignore_list = dict() # TODO: rewrite this line for python3 if migrating
		print "IGNORE LIST CLEANED"

	# Get all (ribbons of cubes with) free places
	elems = driver.find_elements_by_class_name("s-lc-ribbon-top-right")
	# Set an ID for each cube that answer the criteria, the input is constant so they will stay the same
	cube_id=0
	for ribbon in elems:
		
		# Get the main cube thing element
		cube = ribbon.find_element_by_xpath("./../..")
		
		# Get date and time text elements
		month = cube.find_element_by_class_name("s-lc-evt-date-m").text
		day = cube.find_element_by_class_name("s-lc-evt-date-d").text
		hour = cube.find_element_by_class_name("s-lc-eventcard-heading-text").text
		
		# Check date and time to match out desired reservation time, simple substring search
		if (c_time not in hour) or (c_day not in day) or (c_month not in month):
			# time or date is not right, keep looking
			continue # next ribbon
				
		# Check floor
		title = cube.find_element_by_class_name("s-lc-eventcard-title")
		if floor not in title.text:
			print "found a spot with wrong floor, are you sure you want a specific floor?"
			if VERBAL:
				print "requested floor is", floor
				print "title text that didn't match: ", title.text
			continue # next ribbon
		
		# Get ribbon number
		ribbon_number = int(ribbon.find_element_by_xpath(".//span").text.replace(" SEATS LEFT","").replace(" SEAT LEFT",""))
		
		# Set an ID for each cube based on time, date and floor
		cube_id = month +" "+ day +" "+ hour +" "+ title.text
		
		# Before clicking, check the ignore list
		if cube_id in ignore_list:
			if ignore_list[cube_id] == ribbon_number:
				# ignore this cube because it's in the ignore list and the number of free spaces didn't change
				print("Ignored one cube on ignore list!")
				if VERBAL:
					print("Ignored cube ID: " + cube_id)
				continue # next ribbon
			# Number changed
			else: 
				# Remove the cube from ignore list and continue to book
				del ignore_list[cube_id]
		
		# Reservation matches
		print "\n\n=====FOUND A MATCH:======\n"
		print title.text, "\n"
		print "ON - ", month, day, hour, "\n\n========================="
		
		# Click on the reservation we found, will load a different page
		title.click()
		time.sleep(LOAD_WAIT) # sleep to make sure that the page is loaded

		# Check if spot still available on the newly loaded page
		try:
			begin_button = driver.find_element_by_id("s-lc-event-begin")
		except:
			print "clicked too late - fully booked message"
			# Spot is no longer available, go back and keep trying, sleep for longer to wait out the intrusion
			driver.execute_script("window.history.go(-1)")
			# Add cube_id to ignore list
			ignore_list[cube_id] = ribbon_number
			print("Cube added to ignore list")
			break # break from inner loop, continue to refresh page loop

		# NEW VERSION- this redirects to NESTOR LOGIN (old version- this makes form appear)
		begin_button.click()
		time.sleep(LOAD_WAIT) # sleep to make sure that the page is loaded - it will load the nestor login page
		
		# TODO: Test the edge case in which already logged in to nestor
		# Try logging in to nestor
		try:
			form_elem = driver.find_element_by_id("name-field")
			form_elem.send_keys("")
		except:
			print "Couldn't find Nestor log in form, assuming already logged"
			# now it will continue to the next block to try and fill in details, if any error occurred this will fail and the loop will restart
		else:
			# Log in to Nestor
			form_elem = driver.find_element_by_id("name-field")
			form_elem.send_keys(s_number)
		
			form_elem = driver.find_element_by_id("company-field")
			form_elem.send_keys(nestor_password)
		
			login_button = driver.find_element_by_class_name("rug-mb-s")
			login_button.click()
			
			# If we're still on the Nestor login page it's a problem
			#try:
			#	time.sleep(LOAD_WAIT)
			#	form_elem = driver.find_element_by_id("name-field")
			#	form_elem.send_keys("")
			#	print "\nWARNING - Couldn't log into Nestor, your password may be wrong, PLEASE DOUBLE CHECK YOUR PASSWORD!"
			#	pass_fail_count+=1
			#	if pass_fail_count>=3:
			#		print "Your s-number or password are wrong, or there is an error performing Nestor login, I tried logging in " + str(pass_fail_count) + " time and yet miserably failed each time, therefore I give up now"
			#		exit(1)
			#	pass
			#except:
			#	print "\nSuccessfully logged in to Nestor"
			#	pass
		
		time.sleep(LOAD_WAIT)
				
		# Check if form opened, sometimes the spot can be taken at the last moment
		try:
			form_elem = driver.find_element_by_id("phone")
			form_elem.send_keys("")
		except:
			print "clicked too late (?) - form filling not available anymore"
			# Spot is no longer available, go back and keep trying
			#driver.execute_script("window.history.go(-1)")
			
			# EXPERIMENT TO SEE IF WORKS
			break # break from inner loop, continue to refresh page loop

		
		
		# Fill in the form		
		form_elem = driver.find_element_by_id("phone")
		form_elem.send_keys(phone)
			
		form_elem = driver.find_element_by_id("q1")
		form_elem.send_keys(s_number)
		
		# Click register button
		reg_button = driver.find_element_by_id("s-lc-event-sub")
		reg_button.click()
		
		#TODO: check for success message
		print "\n\n=== RESERVED SUCCESSFULLY===\n"
		print "Details: ", s_number, phone
		print "Start time: ", start_time
		print "Time elapsed:", datetime.datetime.now() - start_time
		print "\n============================\n\n"
		exit(0)
	
	if VERBAL:
		if len(elems) > 0:
			print "found", len(elems), "time slots with free seats but none matched the criteria"
