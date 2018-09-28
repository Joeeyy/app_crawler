#coding=utf-8
import json
import threading
import requests
from lxml import etree
import pymysql
from queue import Queue
import time

proxies = {"http": "http://127.0.0.1:8118","https": "http://127.0.0.1:8118",}
alphabet = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','*']

cgInfoFile = "./cgInfoFile.txt"
base_url = "https://itunes.apple.com/"
targetCategory = "App Store"
targetCountry = "cn"

db_name="app_store"
table_name = "app_names_cn_4"
host = "localhost"
user = ""
pwd = ""

Boom=False
crawlThreadNum = 0
processFile = "process.json"
failed_requests=[]
failed_sqls=[]

def clean_name(name):
	name = name.replace('\\','\\\\')
	name = name.replace('\"','\\\"')
	name = name.replace('\'','\\\'')

	return name

class ioThread(threading.Thread):
	def __init__(self, name, dataQueue):
		super(ioThread, self).__init__()
		self.name = name
		self.dataQueue = dataQueue
		self.db = pymysql.connect(host, user, pwd, db_name)
		self.cursor = self.db.cursor()

	def run(self):
		
		while not Boom:
			#print("%s %d"%(self.name,self.dataQueue.qsize()))
			#print(crawlThreadNum, self.dataQueue.qsize(), self.dataQueue.empty())
			if crawlThreadNum == 0 and self.dataQueue.empty():
				print("%s crawlThread done, and no data wait for write, exit."%self.name)
				break
			try:
				t = self.dataQueue.get(timeout=10)
				for each in t[0]:
					each = clean_name(each)
					sql = 'insert into %s(app_name, genre_id) values("%s", %s)'%(table_name,each,t[1])
					try:
						self.cursor.execute(sql)
					except:
						failed_sqls.append(sql)
				self.db.commit()
			except:
				pass
			
		print("%s stopped"%self.name)
		self.db.close()
		f = open("failed_sqls.txt",'a')
		for each in failed_sqls:
			f.write(each+"\n")
		f.close()

class crawlThread(threading.Thread):
	def __init__(self, name, crawl_dict, genre_dict, dataQueue, lock):
		super(crawlThread, self).__init__()
		self.name = name
		self.crawl_dict = crawl_dict
		self.genre_dict = genre_dict
		self.lock = lock
		self.dataQueue = dataQueue

	def run(self):
		for genre_name, genre_id in self.genre_dict.items():
			for a in alphabet:
				apd = False
				while not apd:
					if self.crawl_dict[genre_name][a]['done']:
						print("%s genre done"%self.name)
						break
					with self.lock:
						current_page = self.crawl_dict[genre_name][a]['current_page']
						if current_page == 0:
							current_page += 1
							self.crawl_dict[genre_name][a]['current_page'] += 1
						self.crawl_dict[genre_name][a]['current_page'] += 1
					url = base_url + targetCountry + "/genre/id" + genre_id + "?mt=8"+"&letter=%s"%a + "&page=%d"%current_page
					apd = self.parseAUrl(url, genre_id)
					if apd == None:
						with self.lock:
							self.crawl_dict[genre_name][a]['current_page'] -= 1
						continue
					if apd:
						with self.lock:
							self.crawl_dict[genre_name][a]['current_page'] -= 1
							self.crawl_dict[genre_name][a]['done'] = True
		Boom = True
		
		global crawlThreadNum
		if crawlThreadNum == 1:
			print("last crawl thread: %s going to exit."%self.name)
			thread_processFile = self.name+"_"+processFile
			f = open(thread_processFile,'w')
			f.write(json.dumps(self.crawl_dict))
			f.close()
			f = open('failed_requests.txt')
			for each in failed_requests:
				f.write("%s %s\n"%(each[1],each[0]))
			f.close()
		with self.lock:
			crawlThreadNum -= 1



	def parseAUrl(self, url="",genre_id=0):
		if url=="":
			return None
		print(self.name, url)

		try:
			response = requests.get(url,proxies=proxies, timeout=60)
		except:
			print("%s Error occurred."%self.name)
			failed_requests.append((url,genre_id))
			return None

		status_code = response.status_code
		html_text = response.text
	
		print("%s status_code: %d"%(self.name,status_code))

		html = etree.HTML(html_text)
		# 主信息块，分为左中右三块。
		leftCol_texts = html.xpath('//div[@id="selectedcontent"]/div[@class="column first"]/ul/li/a/text()')
		#leftCol_hrefs = html.xpath('//div[@id="selectedcontent"]/div[@class="column first"]/ul/li/a/@href')
		middleCol_texts = html.xpath('//div[@id="selectedcontent"]/div[@class="column"]/ul/li/a/text()')
		rightCol_texts = html.xpath('//div[@id="selectedcontent"]/div[@class="column last"]/ul/li/a/text()')
		if len(leftCol_texts)==0:
			return True
		else:
			self.dataQueue.put((leftCol_texts,genre_id))

		if len(middleCol_texts)==0:
			return True
		else:
			self.dataQueue.put((middleCol_texts,genre_id))
		if len(rightCol_texts)==0:
			return True
		else:
			self.dataQueue.put((rightCol_texts,genre_id))
			return False


# cgInfo here is a json_str
def read_cgInfo():
	f = open(cgInfoFile,'r')
	cgInfo = f.read()
	f.close()
	
	return cgInfo

# returns a dict, in which cate_name is the key, and id is the value
def getCategories(cg_json=None):
	category_dict = {}
	if cg_json == None:
		return category_dict

	for key in cg_json.keys():
		category_dict[cg_json[key]['name']] = key

	return category_dict

# returns a dict, in which genre_name is the key, and id is the value
def getGenres(cg_json=None, category_dict=None, target=""):
	genre_dict = {}
	if cg_json==None or category_dict==None or target == "":
		return genre_dict
	if not category_dict.__contains__(target):
		return genre_dict
	for key in cg_json[category_dict[target]]['subgenres'].keys():
		genre_dict[cg_json[category_dict[target]]['subgenres'][key]['name']] = key

	return genre_dict

def createCrawlDict(genre_dict):
	'''
	crawl_dict = {
		genre: {
			'A': {
				current_index = num
				done: False # done, when crawl finished
			}
			'B': {
	
			}
			...
		}
	
	}
	'''
	crawl_dict = {}
	for genre in genre_dict:
		crawl_dict[genre]={}
		for a in alphabet:
			crawl_dict[genre][a]={}
			crawl_dict[genre][a]['done']=False
			crawl_dict[genre][a]['current_page']=0
	return crawl_dict

def main():
	print("multi-thread app crawler of apple app store ...")
	dataQueue = Queue()

	cg_json_str = read_cgInfo()
	cg_json = json.loads(cg_json_str)

	category_dict = getCategories(cg_json)
	targetCategory_id = category_dict[targetCategory]

	genre_dict = getGenres(cg_json, category_dict, targetCategory)
	crawl_dict = createCrawlDict(genre_dict)

	crawlThreads = []
	lock = threading.Lock()
	for i in range(10):
		threadName = "crawlThread-%d"%i
		thread = crawlThread(threadName, crawl_dict, genre_dict, dataQueue, lock)
		thread.start()
		crawlThreads.append(thread)
		global crawlThreadNum
		crawlThreadNum = len(crawlThreads)

	ioThreads = []
	for i in range(1):
		threadName = "ioThread-%d"%i
		thread = ioThread(threadName, dataQueue)
		thread.start()
		ioThreads.append(thread)

	for thread in crawlThreads:
		thread.join()
	#crawlByCategory(genre_dict)
	
	for thread in ioThreads:
		thread.join()
	

if __name__ == '__main__':
	main()
