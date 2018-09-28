# App_Crawler

## Target

To crawl all the information of the apps in App Store. For current demand, I crawled apps of iPhone in App Store of China.

## Solution

Here, I write a python crawler. I make the crawling by the following steps:

### 0x00 Get cgInfo (information of categories and genres)

Get all categories and genres of a certain App Store (iPhone App Store of China, for current situation). This information is provided at this link: [https://affiliate.itunes.apple.com/resources/documentation/genre-mapping/](https://affiliate.itunes.apple.com/resources/documentation/genre-mapping/), but note that API provided at the former link offers information of the USA's App Store by default. And I've queried Apple about this, but no answer got until now.
You will get a json format data if you request the [API](https://itunes.apple.com/WebObjects/MZStoreServices.woa/ws/genres) at the former link. That's something like that following:
```
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

```
**For example:**
```
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
```
You can also get a real example from [here](https://raw.githubusercontent.com/Joeeyy/app_crawler/master/cgInfoFile.txt)
It offers us information of all categories in iTunes Store, and App Store or Mac App Store is a part of iTunes Store. Our target category here is "App Store", and its' id is 36.

### 0x01 Get genres of a certain category

Using cgInfo got from the first step, we can get genres of a certain category, note that some genres may have subgenres (although not considered yet).

### 0x02 Crawling stage

We can get apps sorted by alphabet at the folloing link: [https://itunes.apple.com/cn/genre/id6005?mt=8&letter=A&page=1](https://itunes.apple.com/cn/genre/id6005?mt=8&letter=A&page=1) .
There are four parts we need to pay attention to in the former link.
1. cn: This is a tow-lettter country code. You can find more details about that [here](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
2. id6005: id6005 here is a genre in App Store category, which means Social Networking.
3. letter=A: This parameter sets the initial letter of an app name, and all possible cases is as follows: [A-Z, *]
4. page=1: Page number of a html, which is uncertain while crawling.
All four parts here can be considered as essential parameters of our crawler. I'm crawling the apps from outer categories into inner pages ( [1] > [2] > [3] > [4] ). 

For now, we can get a series of links which contains plenty of apps information, and our following task is to parse those links. It's an easy task, and not worthy of a word. After you got those information you need, you can use them as you wish.

## Single and Multi Thread
Single thread version: [here](https://github.com/Joeeyy/app_crawler/blob/master/app_crawler.py) 

Multi-thread version: [here](https://github.com/Joeeyy/app_crawler/blob/master/mul_app_crawler.py)

### Details about multi-thread crawler

Use a special json format file to implement synchronization between threads, like the following:
```
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
```

## Other things

1. For anonymous identity while requesting, you can use proxies.
2. Contect me at <[joeeeee@foxmail.com](joeeeee@foxmail.com)> if you have any suggestions. 
