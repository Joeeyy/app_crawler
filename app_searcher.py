#coding=utf-8
import requests
import pymysql
import json
import threading
from queue import Queue
import time

# Search API: http://itunes.apple.com/search?term=google&country=us&entity=software



proxies = {"http": "http://127.0.0.1:8118","https": "http://127.0.0.1:8118",}

'''
app_info database
'''
host = "localhost"
user = ""
pwd = ""
db_name = "app_store"
app_info_table = "app_info"
app_name_table = "app_names_cn_4"

# thread
search_thread_num = 0
remaining_app_num = 99999999
boom = False # if task finished, then boom.
readUp = False # if read task is finished
searchUp = False # is search task is finished
searchThreads = []

def check_c(s):
	s = s.replace('\\','\\\\')
	s = s.replace('\'','\\\'')
	s = s.replace('\"','\\\"')
	return s

# thread to read app names from database
class readThread(threading.Thread):
	def __init__(self,threadName,nameQueue):
		super(readThread, self).__init__()
		self.threadName = threadName
		self.nameQueue = nameQueue

	def run(self):
		global boom
		global readUp
		global remaining_app_num
		print("%s: start runs, going to read app names..."%self.threadName)
		app_names = ()
		sql = "select distinct app_name from %s"%app_name_table
		db = pymysql.connect(host,user,pwd,db_name)
		cursor = db.cursor()
		remaining_app_num = cursor.execute(sql)
		app_names = cursor.fetchall()
		db.close()
		if remaining_app_num == 0:
			boom = True
			return
		for app_name in app_names:
			self.nameQueue.put(app_name)
		readUp = True
		print("%s: app names read up, exit."%self.threadName)


# thread to write searching results to app info database
class writeThread(threading.Thread):
	def __init__(self,threadName,infoQueue):
		super(writeThread, self).__init__()
		self.threadName = threadName
		self.infoQueue = infoQueue

	def run(self):
		print("%s: write thread starts..."%self.threadName)
		global boom

		failed_sqls = []
		conn = pymysql.connect(host,user,pwd,db_name)
		cursor = conn.cursor()
		while not boom:
			if search_thread_num == 0 and self.infoQueue.empty():
				boom = True
				break
			try:
				#print("%s %d"%(self.threadName, self.infoQueue.qsize()))
				t = self.infoQueue.get(timeout=60)
				app_id = t[0]
				app_name = t[1]
				app_url = t[2]
				icon_url = t[3]
				bundle_id = t[4]
				update_time = t[5]
				artist_name = t[6]
				artist_id = t[7]
				origin_name = t[8]
				sql = "insert into %s(app_id, app_name, app_url, icon_url, bundle_id, update_time, artist_name, artist_id, origin_name) values(%s,'%s','%s','%s','%s','%s','%s',%s,'%s')"%(app_info_table, app_id, app_name, app_url, icon_url, bundle_id, update_time, artist_name, artist_id,origin_name)
				try:
					cursor.execute(sql)
					conn.commit()
				except:
					failed_sqls.append(sql)
					print("[FAILURE] %s"%sql)

			except:
				pass
		conn.close()
		# record failed sqls
		f = open("failed_sqls.txt",'w')
		for each in failed_sqls:
			f.write(each+"\n")
		f.close()
		print("%s: writeThread exited."%self.threadName)

# thread to make searching reuqests
class searchThread(threading.Thread):
	def __init__(self,threadName, searchEntity, searchCountry, searchLimit, nameQueue, infoQueue, lock):
		super(searchThread, self).__init__()
		self.threadName = threadName
		self.searchEntity = searchEntity
		self.searchCountry = searchCountry
		self.searchLimit = searchLimit
		self.nameQueue = nameQueue
		self.infoQueue = infoQueue
		self.lock = lock

	def run(self):
		global searchUp
		global readUp
		global search_thread_num
		global proxies

		failed_requests = []

		while not boom:
			time.sleep(3)
			if readUp and self.nameQueue.empty():
				searchUp = True
				break
			try:
				with self.lock:
					searchTerm = self.nameQueue.get(timeout=10)
			except:
				continue
			api = "http://itunes.apple.com/search?term=%s&country=%s&entity=%s&limit=%d&attribute=allTrackTerm"%(searchTerm[0], self.searchCountry, self.searchEntity, self.searchLimit)
			print("%s: %s "%(self.threadName,api), end='')
			try:
				response = requests.get(api,proxies=proxies,timeout=60)
			except:
				failed_requests.append(api)
				print("Rquest Fail")
				continue
			response_text = response.text
			#print("%s: %s"%(self.threadName, response_text))

			try:
				results = json.loads(response_text)
			except:
				failed_requests.append(api)
				print("Json Fail")
				continue
			if not results.__contains__('resultCount'):
				failed_requests.append(api)
				print("Unhandled Json Fail")
				continue
			if results['resultCount'] == 0:
				app_id=0
				app_name=""
				app_url=""
				icon_url=""
				bundle_id=""
				update_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
				artist_name=""
				artist_id=0
				origin_name = check_c(searchTerm[0])
			else:
				num = results['resultCount']
				targetIndex = -1
				for i in range(num):
					if results['results'][i]['trackName'] == searchTerm[0]:
						targetIndex = i
						break

				if targetIndex != -1:
					app_id = results['results'][i]['trackId']
					app_name = results['results'][i]['trackName']
					app_url = results['results'][i]['trackViewUrl']
					icon_url = results['results'][i]['artworkUrl512']
					bundle_id = results['results'][i]['bundleId']
					update_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
					artist_name = results['results'][i]['artistName']
					artist_id = results['results'][i]['artistId']
					#format check
					app_name = check_c(app_name)
					artist_name = check_c(artist_name)
					origin_name = check_c(searchTerm[0])
				else:
					app_id=0
					app_name=""
					app_url=""
					icon_url=""
					bundle_id=""
					update_time = time.strftime('%Y-%m-%d %H:%M:%S',time.localtime())
					artist_name=""
					artist_id=0
					origin_name = check_c(searchTerm[0])
			self.infoQueue.put((app_id, app_name, app_url, icon_url, bundle_id, update_time, artist_name, artist_id, origin_name))
			print("Success")

		# exit
		with self.lock:
			search_thread_num -= 1
		# write failed request to file of this thread own
		f = open("%s_failed_requests.txt"%self.threadName,'w')
		for each in failed_requests:
			f.write(each+"\n")
		f.close()



		

def main():
	print("App Searcher...")
	global search_thread_num

	search_entitiy = "software"
	search_country = "cn"
	search_limit = 200

	nameQueue = Queue()
	infoQueue = Queue()

	lock = threading.Lock()

	read_bot = readThread("readThread", nameQueue)
	read_bot.start()

	write_bot = writeThread("writeThread", infoQueue)
	write_bot.start()

	for i in range(1):
		threadName = "searchThread-%d"%i
		thread = searchThread(threadName, search_entitiy, search_country, search_limit, nameQueue, infoQueue, lock)
		thread.start()
		searchThreads.append(thread)
		search_thread_num += 1

	read_bot.join()
	for thread in searchThreads:
		thread.join()
	write_bot.join()



	#print (api)
	#response = requests.get(api)
	

if __name__ == '__main__':
	main()