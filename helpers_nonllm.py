import requests 
from bs4 import BeautifulSoup
import os
import glob
import pandas as pd
import hashlib
import random
import json

import OAI

import numpy as np

from lxml import html
from bs4 import BeautifulSoup
import trafilatura
import io

import os, openai, datetime, hashlib, re
import time

import pandas as pd

import string
LETTERS = string.ascii_uppercase

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import os


import re
    
INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
FOOTNOTE_LINK_TEXT_RE = re.compile(r'\[([^\]]+)\]\[(\d+)\]')
FOOTNOTE_LINK_URL_RE = re.compile(r'\[(\d+)\]:\s+(\S+)')



def find_md_links(md):
    """ Return dict of links in markdown """

    links = list(INLINE_LINK_RE.findall(md))
    footnote_links = dict(FOOTNOTE_LINK_TEXT_RE.findall(md))
    footnote_urls = dict(FOOTNOTE_LINK_URL_RE.findall(md))

    for key in footnote_links.keys():
        links.append((footnote_links[key], footnote_urls[footnote_links[key]]))

    return links

def get_cache(BASE_URL,moar=[]):

    page_url = "https://"+BASE_URL+"/archive"

    page_sourced = requests.get(page_url).content 

    html_content = BeautifulSoup(page_sourced, "html.parser")
    # #main > div.archive-page.typography.use-theme-bg > div > div > div.portable-archive-list > div:nth-child(19) > div.post-preview-content > a.post-preview-title.newsletter
    links = html_content.findAll('a', class_="pencraft")
    print(len(links)) 
    pages = [i.get('href') for i in links if (not (i.get('href') is None))]
    if len(moar):
        for x in moar:
            pages.append(x)
    pages = [ i for i in pages  if "https://"+BASE_URL+"/p/" in i ]
    pages = list(set([ i for i in pages  if not i.endswith("comments") ]))
    len(pages), pages

    return pages

def download_substack_pages(pages):
    for page in pages:
        name = page.split("/")[-1]

        if not os.path.exists(".cache/"+name):
            page_sourced = requests.get(page).content 
            html_content = BeautifulSoup(page_sourced, "html.parser")
            content = html_content.findAll('div', class_="body markup")

            with open(".cache/"+name, 'w') as f:
                f.write(str(content))
            print(name,"saved")
        else:
            print(name,"exists.")
    return 1


def txtRead(filename):
    with io.open(filename,'r',encoding='utf8') as f:
        txt= f.read()
    return txt

def intersection(lst1, lst2):
    lst3 = [value for value in lst1 if value in lst2]
    return lst3

def download_pages(archivepath='.archive'):
    files = os.listdir(archivepath)
    file_names = []
    for name in files:
        if not ('type' in name):
            file_names.append(name)
    # Read existing files
    D = pd.read_parquet('data/articles.parquet.gzip')
    DONE = list(D.file_name)
    articles = []
    errors = []
    for file_name in file_names:
        if file_name not in DONE:
            with io.open(f'.archive/{file_name}', mode="r", encoding="utf-8") as f:
                try:
                    mytree = html.fromstring("".join(f.readlines()))
                except Exception as e:
                    print(file_name,e)
                    errors.append(file_name)
                    continue
                try:
                    content = trafilatura.extract(mytree)
                    articles.append((file_name, content))
                except Exception as e:
                    print(file_name,e)
                    errors.append(file_name)
    NEW = pd.DataFrame(articles, columns = ['file_name', 'content'])
    NEW["LEN"] = NEW["content"].apply(lambda x: len(str(x)))
    df = pd.concat([NEW,D]).reset_index(drop=True)
    df.to_parquet('data/articles.parquet.gzip',compression="gzip")
    return df

def do_selenium():
    df = pd.read_parquet('data/articles.parquet.gzip')
    strs = ["detected unusual","enable JS", "nable Javascript","Checking your browser","mettre à jour votre navigateur","nable JavaScript","Adobe Acrobat JavaScript","please click the box below to","site connection is secure","Optica Publishing Group","switch to a supported browser"]
    df = df[df['content'].astype(str).str.contains("|".join(strs))]
    df.to_parquet("data/to_process_selenium.parquet.gzip",compression="gzip")
    return "data/to_process_selenium.parquet.gzip"



def getlinks():
    URLs = []
    cached_pages = glob.glob(".cache/*")
    for page in cached_pages:
        with open(page) as fp:
            html_content = BeautifulSoup(fp, 'html.parser')  
        content = html_content.findAll('a')
        content = [i.get('href') for i in content if (not (i.get('href') is None))]
        for link in content:
            URLs.append([page,link])

    df = pd.DataFrame(URLs)
    df.columns = ["page","url"]
    df = df.drop_duplicates(subset=["url"])
    df["url"] = df.url.apply(lambda x: str(x).encode('utf-8'))

    df["hash"] = df.url.apply(lambda x: hashlib.md5(str(x).encode('utf-8')).hexdigest())
    df.to_parquet("data/urls.parquet.gzip",  engine='pyarrow', compression='gzip')
    return df



def getdraftlinks():
    URLs = []
    cached_drafts = glob.glob("drafts/*")
    for page in cached_drafts:
        with open(page) as fp:
            md = fp.read()
        content = [x[1] for x in find_md_links(md) if len(x[1])]
        #print(page,content)
        for link in content:
            URLs.append([page,link])

    df = pd.DataFrame(URLs)
    df.columns = ["page","url"]
    df = df.drop_duplicates(subset=["url"])
    df["url"] = df.url.apply(lambda x: str(x).encode('utf-8'))

    df["hash"] = df.url.apply(lambda x: hashlib.md5(str(x).encode('utf-8')).hexdigest())
    DF = pd.read_parquet("data/urls.parquet.gzip")
    df = pd.concat([DF,df]).drop_duplicates(subset="hash")
    df.to_parquet("data/urls.parquet.gzip",  engine='pyarrow', compression='gzip')
    return df

def pages_content(dfpath):
    df = pd.read_parquet(dfpath)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept-Charset': 'utf-8',
    'Connection': 'keep-alive'}
    session = requests.Session()
    DICO = {}
    with open("errors.log", "r") as log:
        errors = [x.strip() for x in log.read().split("\n") if len(x.strip())]
    for ix, row in df.sample(frac=1).iterrows():
        #print(row["url"])
        if str(row["url"]) not in errors:
            if not os.path.exists(".archive/"+row["hash"]+".type"):
                try:
                    response = session.head(row["url"], timeout=10, headers=headers)
                    contentType = response.headers['content-type']
                except:
                    contentType = "error"
                with open(".archive/"+row["hash"]+".type", "w") as f:
                    f.write(contentType)
                #print(row["hash"],row["url"],contentType)
                
            if not os.path.exists(".archive/"+row["hash"]):
                try:
                    r = requests.get(row["url"], timeout=10, headers=headers)
                    with open(".archive/"+row["hash"], "wb") as f:
                        f.write(r.content)
                except:
                    print(str(row["url"]),"error.")
                    with open("errors.log", "a") as log:
                        log.write(str(row["url"])+"\n")
                    pass
                print(row["hash"],"saved.")
            else:
                0

