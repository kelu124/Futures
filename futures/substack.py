import requests 
from bs4 import BeautifulSoup
import os
import glob
import pandas as pd
import hashlib
import random
import json

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


import pandas as pd
import os


import re
    
INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
FOOTNOTE_LINK_TEXT_RE = re.compile(r'\[([^\]]+)\]\[(\d+)\]')
FOOTNOTE_LINK_URL_RE = re.compile(r'\[(\d+)\]:\s+(\S+)')


from futures.commons import intersection, find_md_links, get_cache, txtRead



class SubstackManager:

    def __init__(self, basepath="./substack_cache/"):
        # Download cache
        self.cache_substackpages = basepath + "substack/"
        # Substack
        self.BASE_URL = "substack.kghosh.me"
        # All pages archives
        self.archivepath = basepath+'.archive/'
        # Dataframe out
        self.datastore ="data/"
        self.srcArticles = self.datastore + 'articles.parquet.gzip'
        self.srcURLs     = self.datastore + 'urls.parquet.gzip'

    def getPages(self):
        print("# Substack manager starts")
        pages = get_cache(self.BASE_URL, moar=["20241222","20241229","20241215"])
        self.download_substack_pages(pages)
        self.getlinks()
        self.getdraftlinks()
        self.pages_content()
        self.download_pages()

    def download_substack_pages(self, pages):
        for page in pages:
            name = page.split("/")[-1]
            if not os.path.exists(self.cache_substackpages+name):
                page_sourced = requests.get(page).content 
                html_content = BeautifulSoup(page_sourced, "html.parser")
                content = html_content.findAll('div', class_="body markup")

                with open(self.cache_substackpages+name, 'w') as f:
                    f.write(str(content))
                print("- Substack manager: ", name, "saved")
            else:
                print("- Substack manager: ", name, "exists")


    def getlinks(self):
        """Reads downloaded pages and gets URLs of interest to srcURLs"""
        # Extract pages from substack downloaded pages
        URLs = []
        cached_pages = glob.glob(self.cache_substackpages+"*")
        for page in cached_pages:
            with open(page) as fp:
                html_content = BeautifulSoup(fp, 'html.parser')  
            content = html_content.findAll('a')
            content = [i.get('href') for i in content if (not (i.get('href') is None))]
            for link in content:
                URLs.append([page, link])

        df = pd.DataFrame(URLs)
        df.columns = ["page", "url"]
        df = df.drop_duplicates(subset=["url"])
        df["url"] = df.url.apply(lambda x: str(x).encode('utf-8'))
        df["hash"] = df.url.apply(lambda x: hashlib.md5(str(x).encode('utf-8')).hexdigest())
        df.reset_index(drop=True).to_parquet(self.srcURLs,  engine='pyarrow', compression='gzip')
        return df


    def getdraftlinks(self, pathtodraft="drafts/"):
        """Reads draft pages and gets URLs of interest to srcURLs"""
        URLs = []
        cached_drafts = glob.glob(pathtodraft+"*")
        for page in cached_drafts:
            if "old" not in page:
                with open(page) as fp:
                    md = fp.read()
                content = [x[1] for x in find_md_links(md) if len(x[1])]
                for link in content:
                    URLs.append([page, link])

        df = pd.DataFrame(URLs)
        df.columns = ["page", "url"]
        df = df.drop_duplicates(subset=["url"])
        df["url"] = df.url.apply(lambda x: str(x).encode('utf-8'))

        df["hash"] = df.url.apply(lambda x: hashlib.md5(str(x).encode('utf-8')).hexdigest())
        DF = pd.read_parquet(self.srcURLs)
        df = pd.concat([DF, df]).drop_duplicates(subset="hash")
        df.reset_index(drop=True).to_parquet(self.srcURLs,  engine='pyarrow', compression='gzip')
        return df



    def do_selenium(self):
        # @TODO: never used
        df = pd.read_parquet('data/articles.parquet.gzip')
        strs = ["detected unusual","enable JS", "nable Javascript","Checking your browser","mettre à jour votre navigateur","nable JavaScript","Adobe Acrobat JavaScript","please click the box below to","site connection is secure","Optica Publishing Group","switch to a supported browser"]
        df = df[df['content'].astype(str).str.contains("|".join(strs))]
        df.to_parquet("data/to_process_selenium.parquet.gzip",compression="gzip")
        return "data/to_process_selenium.parquet.gzip"


    def pages_content(self):
        # "data/urls.parquet.gzip")
        print("# Saving links from the substack pages")
        df = pd.read_parquet(self.srcURLs)
        headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
        'Accept-Charset': 'utf-8',
        'Connection': 'keep-alive'}
        session = requests.Session()
        DICO = {}
        with open("errors.log", "r") as log:
            errors = [x.strip() for x in log.read().split("\n") if len(x.strip())]
        for ix, row in df.sample(frac=1).iterrows():
            if str(row["url"]) not in errors:
                if not os.path.exists(self.archivepath +row["hash"]+".type"):
                    try:
                        response = session.head(row["url"], timeout=10, headers=headers)
                        contentType = response.headers['content-type']
                    except:
                        contentType = "error"
                    with open(self.archivepath +row["hash"]+".type", "w") as f:
                        f.write(contentType)
                if not os.path.exists(self.archivepath +row["hash"]):
                    try:
                        r = requests.get(row["url"], timeout=10, headers=headers)
                        with open(self.archivepath +row["hash"], "wb") as f:
                            f.write(r.content)
                        print("- ",row["hash"],"saved.")
                    except:
                        try:
                            r = requests.get(row["url"].split("?")[0], timeout=10, headers=headers)
                            with open(self.archivepath +row["hash"], "wb") as f:
                                f.write(r.content)
                        except:
                            print(str(row["url"]),"error.")
                            with open("errors.log", "a") as log:
                                log.write(str(row["url"])+"\n")
                            pass
                    




    def download_pages(self):
        """Reads downloaded links and ultimately creates the articles parquet file"""
        files = os.listdir(self.archivepath)
        file_names = []
        for name in files:
            if not ('type' in name):
                file_names.append(name)
        # Read existing files
        try:
            D = pd.read_parquet(self.srcArticles)
            D = D[['file_name', 'content']]
        except:
            D = pd.DataFrame(columns = ['file_name', 'content'])

        DONE = list(D.file_name)
        articles = []
        errors = []
        for file_name in file_names:
            if file_name not in DONE:
                with io.open(self.archivepath + file_name, mode="r", encoding="utf-8") as f:
                    try:
                        mytree = html.fromstring("".join(f.readlines()))
                    except Exception as e:
                        #print(file_name,e)
                        errors.append(file_name)
                        continue
                    try:
                        content = trafilatura.extract(mytree)
                        articles.append((file_name, content))
                    except Exception as e:
                        #print(file_name,e)
                        errors.append(file_name)
        NEW = pd.DataFrame(articles, columns = ['file_name', 'content'])
        #NEW["LEN"] = NEW["content"].apply(lambda x: len(str(x)))
        df = pd.concat([NEW,D]).reset_index(drop=True)

        urls = pd.read_parquet(self.srcURLs)
        urls["origin"] = urls["page"].apply(lambda x: x.split(os.sep)[-1].replace(".md",""))
        urls.columns = ["page","url","file_name","origin"]
        urls = urls[["file_name","origin"]]
        df = df.merge(urls, on="file_name",how="left")
        df["LEN"] = df["content"].apply(lambda x: int(len(str(x))))
        #print(df)
        df.reset_index(drop=True).to_parquet(self.srcArticles, compression="gzip")

        return df
