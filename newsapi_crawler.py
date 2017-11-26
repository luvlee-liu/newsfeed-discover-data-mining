#!/usr/bin/env python 
import requests
import sys
import os
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
from tqdm import tqdm
from functools import reduce
from newspaper import Article
from keywordextraction import *

MAX_NUM_NEWS = -1 # max number of news to crawl, -1 is unlimited
NEWS_API_KEY = os.environ['NEWS_API_KEY'] # GET APIKEY from system environment variables
SOURCE_URL   = 'https://newsapi.org/v2/sources?language={0}&country={1}&apiKey={2}'.format('en', 'us', NEWS_API_KEY)
    
file_path = './news.csv'
black_list=['crypto-coins-news', 'axios', 'buzzfeed','reddit-r-all','wired-de','gruenderszene','handelsblatt',
'spiegel-online','the-hindu','der-tagesspiegel','abc-news-au',
'mtv-news','the-times-of-india','wirtschafts-woche']

white_list=[]

def getSources():
    response = requests.get(SOURCE_URL).json()
    sources = []
    for source in response['sources']:
        sources.append(source['id'])
    return sources

def mapping():
    d = {}
    response = requests.get(SOURCE_URL).json()
    for s in response['sources']:
        d[s['id']] = s['category']
    return d

def category(source, m):
    try:
        return m[source]
    except:
        return 'N/A'

def getArticle(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return article
    except:
        return None

def downloadFullText(df):
    total = len(df.index)
    for i, row in df.iterrows():
        url = row['url']
        print("download %d/%d: %s" % (i+1, total, url))
        article = getArticle(url)
        if article:
            fullText = article.text
            df.at[i ,'fulltext'] = fullText.rstrip()

def extractKeywords(df):
    total = len(df.index)
    for i, row in df.iterrows():
        text = row['fulltext']
        if text == None or text == '':
            text = row['description']
        # extract top k keywords and named entities
        preload = True
        classifier_type = 'logistic'
        keyword_classifier = get_keywordclassifier(preload,classifier_type)['model']
        top_k_keywords = 20
        keywords = []
        named_entities = []
        try:
            keywords_obj = extract_keywords(text, keyword_classifier, top_k_keywords, preload)  
            keywords = keywords_obj['keywords']
            named_entities = keywords_obj['named_entities']
        except:
            pass

        df.at[i, 'keywords'] = "\n".join(keywords)
        df.at[i, 'named_entities'] = "\n".join(named_entities)
        print("article:%d\nExtracted top-%d keywords: %s \n Named_entities: %s \n\n" % (i, top_k_keywords, ",".join(keywords), ",".join(named_entities) ))
        
def cleanData(df):
    df.drop_duplicates('url', inplace=True)

    for i, row in df.iterrows():
        if pd.isnull(row['source']):
            print("ERROR: stopped clean at ", i)
            break
        if row['source'] in black_list:
            print('drop due to blacklist: ', row['title'])
            df.drop(i, inplace=True)
        if pd.isnull(row['description']):
            if 'fulltext' in df.columns and row['fulltext']:
                if len(row['fulltext']) > 600:
                    row['description'] = row['fulltext'][:300]
                else:
                    print('drop due to short fulltext:', row['title'])
                    df.drop(i, inplace=True)
            else:
                print('drop due to no description:', row['title'])
                df.drop(i, inplace=True)

def getDailyNews(file_path):
    sources = getSources()
    url = 'https://newsapi.org/v2/top-headlines?sources={0}&apiKey={1}'
    responses = []
    fetch_counter = 0
    for i, source in tqdm(enumerate(sources)):
        if source in black_list:
            continue
        try:
            u = url.format(source, NEWS_API_KEY)
            response = requests.get(u)
            r = response.json()
            for article in r['articles']:
                fetch_counter += 1
                article['source'] = source
            responses.append(r)
            if MAX_NUM_NEWS > 0 and fetch_counter >= MAX_NUM_NEWS:
                break
        except:
            continue
    
    news = pd.DataFrame(reduce(lambda x,y: x+y ,map(lambda r: r['articles'], responses)))
    news = news.dropna()
    news = news.drop_duplicates()
    d = mapping()
    news['category'] = news['source'].map(lambda s: category(s, d))
    news['scraping_date'] = datetime.now()

    # deduplicate by url
    news = news.drop_duplicates('url')

    try:
        # merge with csv
        aux = pd.read_csv(file_path)
        news = news[~new.url.isin(aux.url.values.tolist())]
        with open(file_path, 'a') as f:
            news.to_csv(f, header=False, encoding='utf-8', index=False)

    except:
        # aux = pd.DataFrame(columns=list(news.columns))
        news.to_csv(file_path, encoding='utf-8', index=False)

    return news

if __name__ == '__main__':
    if not NEWS_API_KEY:
        print("visit https://newsapi.org/ to get API key")
        exit()

    if len(sys.argv) > 1:
        file_path = sys.argv[1]
    print("Save to ", file_path)

    df = getDailyNews(file_path)
    print('getDailyNews Done')

    df = pd.read_csv(file_path)
    print("Total article: %d " % (len(df.index)))

    downloadFullText(df)
    print('Download FullText Done')

    cleanData(df)
    print('Clean data Done')
    
    extractKeywords(df)
    print('Extract Keywords Done')
    
    print("Total article: %d " % (len(df.index)))
    df.to_csv(file_path, index=False)
