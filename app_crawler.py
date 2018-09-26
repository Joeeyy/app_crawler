#coding=utf8
import requests
import json
from lxml import etree
import threading

'''
[官方分类显示列表](https://affiliate.itunes.apple.com/resources/documentation/genre-mapping/)
	[app search](http://itunes.apple.com/search?term=google&country=us&entity=software)
	param 1: term，搜索关键词
	param 2: country, 搜索的市场
	param 3: entity, 限定为software

	爬虫思路：获取所有分类（genre），按照分类中字母顺序爬取。爬取到的app应该只是名字，注意记录重复的情况。
	然后根据名称查询到app具体内容。主要是bundle id，图标也是考虑内容之一。
'''

'''
本爬虫目标位app_store中的app信息，由于app_store隶属于itunes_store，这里是用的是itunes_store提供的文档进行开发。
itunes_store按照类目分为以下若干类（见链接：https://affiliate.itunes.apple.com/resources/documentation/genre-mapping/）。
分类级别如下：
目录(category) -> 分类(genre) -> 子类(subgenre)
分类包括分类名（genre_name），分类id（genre_id）
分类结构化内容可以由https://itunes.apple.com/WebObjects/MZStoreServices.woa/ws/genres得到。
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
			page = 10
			# by page
			while page>0:
				pa_genre_url = a_genre_url + "&page=%d"%page
				page = page - 1
				
				# here we've got the target url, pa_genre_url
				# next steps, we need to study the structure of the target html
				# confirm this page contains valid content first
				# fetch and parse content from the url
				parseAUrl(pa_genre_url)

def parseAUrl(url=""):
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
	leftCol_hrefs = html.xpath('//div[@id="selectedcontent"]/div[@class="column first"]/ul/li/a/@href')
	middleCol_texts = html.xpath('//div[@id="selectedcontent"]/div[@class="column"]/ul/li/a/text()')
	middleCol_hrefs = html.xpath('//div[@id="selectedcontent"]/div[@class="column"]/ul/li/a/@href')
	rightCol_texts = html.xpath('//div[@id="selectedcontent"]/div[@class="column last"]/ul/li/a/text()')
	rightCol_hrefs = html.xpath('//div[@id="selectedcontent"]/div[@class="column last"]/ul/li/a/@href')
	if len(leftCol_texts)==0:
		print("no element.")
	else:
		print(len(leftCol_texts))
	for each in leftCol_texts:
		print(each)




def main():
	print("app crawler of apple app store ...")
	cg_json_str = read_cgInfo()
	cg_json = json.loads(cg_json_str)
	'''
	{
		category_id:{
			name:
			id:
			url:
			rssUrls: {'': ''}
			chartUrls: {'': ''}
			subgenres: {'': {
				name: 
				id: 
				url: 
				rssUrls: {'': ''}
				chartUrls: {'': ''}
				# and for some cases, Games for example, there is still a subgenres
			}}
		}
	}

	example: 
	{
		36:{
			name: TV Shows,
			id: 32
			url: https://itunes.apple.com/us/genre/tv-shows/id32
			rssUrls: {
				'topTvEpisodes':
				'topTvEpisodeRentals':
				'topTvSeasons':
			}
			chartUrls: {
				'tvEpisodeRentals': 
				'tvSeasons':
				'tvEpisodes':
			}
			sugenres: {
				'4003':{}
				'4004':{}
				...
			}
		}
		...
	}
	'''
	
	category_dict = getCategories(cg_json)
	targetCategory_id = category_dict[targetCategory]
	## genre url: "https://itunes.apple.com/cn/genre/id6005?mt=8&letter=A"
	#aUrl = base_url + targetCountry + "/genre/id" + targetCategory_id +"?mt=8"
	#print(aUrl)
	'''
	1. 按照category来，访问到链接如：https://itunes.apple.com/cn/genre/id6005?mt=8，其中'id6005'应该是一个category
	2. 对于每个category，按照字典顺序遍历，字典[a-z,#]，在[1]中链接后追加如letter=A便可以实现
	3. 对于每个字典，进行页数遍历，在[2]中链接基础上增加page=1即可实现，通过页面中指定区域是否含有内容标记是否对该字典中字母的内容爬取完毕。
	这一步主要是对app名称信息的爬取。
	'''
	genre_dict = getGenres(cg_json, category_dict, targetCategory)
	
	# 爬取进度记录，（到哪个国家，到哪个category，）到哪个genre，到哪个alphabet，到哪个page
	crawlByCategory(genre_dict)

	

	

if __name__ == '__main__':
	main()