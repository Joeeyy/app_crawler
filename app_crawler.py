#coding=utf8
import requests
import json
from lxml import etree
import pymysql

'''
[官方分类显示列表](https://affiliate.itunes.apple.com/resources/documentation/genre-mapping/)
	[app search](http://itunes.apple.com/search?term=google&country=us&entity=software)
	param 1: term，搜索关键词
	param 2: country, 搜索的市场
	param 3: entity, 限定为software

	爬虫思路：获取所有分类（genre），按照分类中字母顺序爬取。爬取到的app应该只是名字，注意记录重复的情况。
	然后根据名称查询到app具体内容。主要是bundle id，图标也是考虑内容之一。
'''

proxies = {"http": "http://127.0.0.1:8118","https": "http://127.0.0.1:8118",}
genre_service_url = "https://itunes.apple.com/WebObjects/MZStoreServices.woa/ws/genres"
# category url: "https://itunes.apple.com/cn/genre/ios/id36?mt=8"
# genre url: "https://itunes.apple.com/cn/genre/id6005?mt=8&letter=A"
base_url = "https://itunes.apple.com/"

cgInfoFile = "./cgInfoFile.txt"
# 在进行真正的爬取工作之前，应该根据getCategories()确定存在的目录，爬取指定的目录，这里关注app store，然后需要获取app store对应的category id。
targetCategory = "App Store"
# 两个字母表示的国家代码，具体参阅https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2
targetCountry = "cn"
targetPlatform = "ios"
# 按照app名称的字母顺序进行遍历。
alphabet = ['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','Y','Z','*']

'''
MySQL related things
'''
db="app_store"
table_name = "app_names_cn"
host = "localhost"
user = ""
pwd = ""

db = pymysql.connect(host, user, pwd, db)
cursor = db.cursor()


#cg: categories and genres
def fetch_cgInfo():
	response = requests.get(genre_service_url)
	print('status code: %d\nresponse encoding: %s'%(response.status_code, response.encoding))
	
	f = open(cgInfoFile, 'w')
	f.write(response.text)
	f.close()

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

# crawl by category
def crawlByCategory(genre_dict=None):
	if genre_dict == None:
		return None

	# get genre name
	for genre_name, genre_id in genre_dict.items():
		print("crawling genre: %s"%genre_name)
		genre_url = base_url + targetCountry + "/genre/id" + genre_id +"?mt=8"
		# get an element from alphabet
		for a in alphabet:
			a_genre_url = genre_url + "&letter=%s"%a
			page = 1
			apd = False # all page done
			# by page
			while not apd:
				pa_genre_url = a_genre_url + "&page=%d"%page
				page += 1
				# here we've got the target url, pa_genre_url
				# next steps, we need to study the structure of the target html
				# confirm this page contains valid content first
				# fetch and parse content from the url
				
				apd = parseAUrl(pa_genre_url, genre_id)

def parseAUrl(url="",genre_id=0):
	if url=="":
		return None
	print(url)
	response = requests.get(url,proxies=proxies)
	status_code = response.status_code
	html_text = response.text
	
	print("status_code: %d"%status_code)

	html = etree.HTML(html_text)
	# 主信息块，分为左中右三块。
	leftCol_texts = html.xpath('//div[@id="selectedcontent"]/div[@class="column first"]/ul/li/a/text()')
	#leftCol_hrefs = html.xpath('//div[@id="selectedcontent"]/div[@class="column first"]/ul/li/a/@href')
	middleCol_texts = html.xpath('//div[@id="selectedcontent"]/div[@class="column"]/ul/li/a/text()')
	#middleCol_hrefs = html.xpath('//div[@id="selectedcontent"]/div[@class="column"]/ul/li/a/@href')
	rightCol_texts = html.xpath('//div[@id="selectedcontent"]/div[@class="column last"]/ul/li/a/text()')
	#rightCol_hrefs = html.xpath('//div[@id="selectedcontent"]/div[@class="column last"]/ul/li/a/@href')
	if len(leftCol_texts)==0:
		return True
	else:
		for each in leftCol_texts:
			each = each.replace('\"','\\\"')
			each = each.replace('\'','\\\'')
			sql = 'insert into app_names_cn(app_name, genre_id) values("%s", %s)'%(each,genre_id)
			cursor.execute(sql)
	if len(middleCol_texts)==0:
		db.commit()
		return True
	else:
		for each in middleCol_texts:
			each = each.replace('\"','\\\"')
			each = each.replace('\'','\\\'')
			sql = 'insert into app_names_cn(app_name, genre_id) values("%s", %s)'%(each,genre_id)
			cursor.execute(sql)
	if len(rightCol_texts)==0:
		db.commit()
		return True
	else:
		for each in rightCol_texts:
			each = each.replace('\"','\\\"')
			each = each.replace('\'','\\\'')
			sql = 'insert into app_names_cn(app_name, genre_id) values("%s", %s)'%(each,genre_id)
			cursor.execute(sql)
		
		db.commit()
		return False

def main():
	print("app crawler of apple app store ...")
	cg_json_str = read_cgInfo()
	cg_json = json.loads(cg_json_str)
	
	category_dict = getCategories(cg_json)
	targetCategory_id = category_dict[targetCategory]
	genre_dict = getGenres(cg_json, category_dict, targetCategory)
	
	crawlByCategory(genre_dict)

if __name__ == '__main__':
	main()
	db.close()
