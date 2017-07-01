import os
import redis
import time
import sys
import serial
import pygame

#SERVER = '10.42.0.1'
SERVER = '169.254.212.95'
PATH = "/home/pi/wall-counter/assets/"

TOPIC = 'buttons'

strPort1 = '/dev/ttyACM0'
#strPort1 = '/dev/ttyACM1'

ser = serial.Serial(strPort1, 9600)


global r, pubsub, tokens, screen


WIDTH = 1280
HEIGHT = 720

IMG_WIDTH = 400
IMG_HEIGHT = 500

L_WIDTH = ((WIDTH / 2) - 400) / 2 
R_WIDTH = L_WIDTH + (WIDTH / 2)

images = []

global counting, start_time, r_counter, l_counter

for i in range(10):
	fn = PATH + '/ENG0' + str(i) + '.png'
	images.append(pygame.image.load(fn))

img_rp = pygame.image.load(PATH + "ENGRP.png")
img_rp = pygame.transform.scale(img_rp,(1280,720))

img_ready = pygame.image.load(PATH + "ENGGR.png")
img_ready = pygame.transform.scale(img_ready,(1280,720))

img_start = pygame.image.load(PATH + "ENGST.jpg")
img_start = pygame.transform.scale(img_start,(1280,720))

img_finish = pygame.image.load(PATH + "ENGFN.jpg")
img_finish = pygame.transform.scale(img_finish,(1280,720))



def showLogo():
	BASE_CMD = "sudo fbi -T 1 --noverbose -a "

	cmd = BASE_CMD + PATH + 'bb.jpg'
	os.system(cmd)

def pygame_init():
	global screen

	pygame.init()

	screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)



def connect_redis():
	global r, pubsub
	print 'Attempting connection'
	r = redis.Redis(host=SERVER)
	print r.get('name')
	pubsub = r.pubsub()

	return True

def connect():
	print 'Connecting to Button Board'
	connected = False

	while not connected:

		try:
			connect_redis()
			connected = True
		except KeyboardInterrupt:
			raise
		except:
			e = sys.exc_info()

			print "Cannot Connect", e
			time.sleep(1)
	
	return True

def waitForStart():
	global screen, tokens
	tokens = 0
	
	screen.blit(img_rp, (0, 0))
	pygame.display.flip()
	pubsub.subscribe(TOPIC)

	start_pressed = False

	while not start_pressed:
		for item in pubsub.listen():
			print item
			if item['type'] == 'message':
				print item['data']
				if item['data'] == 'S':
					start_pressed = True
					pubsub.unsubscribe()
		time.sleep(0.01)


def waitForValid():
	global screen, tokens, r
	r.publish('tokens','F')
	screen.blit(img_finish, (0, 0))
	pygame.display.flip()
	pubsub.subscribe(TOPIC)

	valid = False

	while not valid:
		for item in pubsub.listen():
			print item
			if item['type'] == 'message':
				print item['data']
				if item['data'] == 'V':
					valid = True
					pubsub.unsubscribe()
		time.sleep(0.01)
	tokens = 0
	ser.write('V')


def sendStart():
	global screen
	screen.blit(img_ready, (0, 0))
	pygame.display.flip()
	print 'Sending Start to Arduino'
	ser.write("S")


def showTokens(num):
	global screen, r, tokens
	print num, "tokens available"
	tokens = num
	r.publish('tokens', tokens)
	displayNum(tokens)

def displayNum(duration):
	r_counter = duration % 10
	duration /= 10
	l_counter = duration % 10
	print duration, l_counter, r_counter  
	counting = True
	l_image = images[l_counter]
	r_image = images[r_counter]

	screen.fill((255, 255, 255))
	screen.blit(l_image, (L_WIDTH, 50))
	screen.blit(r_image, (R_WIDTH, 50))
	pygame.display.flip()


def readSerial():
	global screen
	finished = False
	while not finished:
		try:
			line = ser.readline().strip()
			
			if line[0] == 'F':
				print line
				finished = True
				#screen.blit(img_finish, (0, 0))
				#pygame.display.flip()


			if line[0] == 't':
				print line
				tokens = line.split(":")
				showTokens(int(tokens[1]))
			#print line
			if line[0] == 'c':
				print line
				token = int(line.split(":")[1])
				if token == 0:
					screen.blit(img_start, (0, 0))
					pygame.display.flip()
				else:
					displayNum(token)
			print line.strip()	


		except KeyboardInterrupt:
			raise
		except:
			e = sys.exc_info()

			print "something messed up", e
			time.sleep(1)

readSerial()
connect()
showLogo()
pygame_init()
while 1:
	waitForStart()
	sendStart()
	readSerial()
	waitForValid()


