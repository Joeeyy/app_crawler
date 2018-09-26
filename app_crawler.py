#coding=utf8
import requests
import json

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
			rssUrls:
			chartUrls:
			subgenres:
		}
	}
	'''
	
	category_dict = getCategories(cg_json)
	targetCategory_id = category_dict[targetCategory]
	## genre url: "https://itunes.apple.com/cn/genre/id6005?mt=8&letter=A"
	#aUrl = base_url + targetCountry + "/genre/id" + targetCategory_id +"?mt=8"
	#print(aUrl)
	for key in cg_json.keys():
		for k in cg_json[key].keys():
			if k == "name" or k == "id" or k == "url":
				print(k,cg_json[key][k])
			else:
				print(k)
		print('----------------------')
	

	

if __name__ == '__main__':
	main()