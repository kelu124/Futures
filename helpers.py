import requests 
from bs4 import BeautifulSoup
import os
import glob
import pandas as pd
import hashlib

import OAI

import numpy as np

from lxml import html
from bs4 import BeautifulSoup
import trafilatura
import io


def get_cache(BASE_URL):

    page_url = "https://"+BASE_URL+"/archive"

    page_sourced = requests.get(page_url).content 

    html_content = BeautifulSoup(page_sourced, "html.parser")
    # #main > div.archive-page.typography.use-theme-bg > div > div > div.portable-archive-list > div:nth-child(19) > div.post-preview-content > a.post-preview-title.newsletter
    links = html_content.findAll('a', class_="pencraft")
    print(len(links)) 
    pages = [i.get('href') for i in links if (not (i.get('href') is None))]

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


def pages_content(dfpath):
    df = pd.read_parquet(dfpath)
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.11 (KHTML, like Gecko) Chrome/23.0.1271.64 Safari/537.11',
    'Accept-Charset': 'utf-8',
    'Connection': 'keep-alive'}
    session = requests.Session()
    DICO = {}

    for ix, row in df.sample(frac=1).iterrows():
        #print(row["url"])
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
                print(row["url"],"error.")
                pass
            print(row["hash"],"saved.")
        else:
            0




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

def txtRead(filename):
    with io.open(filename,'r',encoding='utf8') as f:
        txt= f.read()
    return txt

def createSeeds():
    STEP1 = "Acting as a Futurist, process the following text as a signal in a TABLE, first column a short 5–7 word summary of the signal, second column what kind of change is this (from what to what) 5–10 word summary, third column what might be different in 10 years time 5–10 word summary, fourth column What’s one driving force, or motivation, behind this change? 5–10 word summary:\n\n"

    STEP2 = "Process the following text, and give back only the top 10 most relevant keywords for the text, as a Python list (looking like KEYWORDS = ['keyword1', 'keyword2']). Then, on a new line, provide a list of the top three themes or categories the text belongs to (looking like THEMES = ['theme1', 'theme2']). On another new line, add a paragraph starting with 'Summary:'  which  summarizes the text in 4 to 5 sentences. \n\n"

    STEP3 = "Process the following text, and give this text a title, which should not be longer than 6 words, in the form 'TITLE: title of the article'.\n\n"
    df = pd.read_parquet('data/articles.parquet.gzip')
    df = df[(df.LEN > 1500) & (df.LEN < 30000)]
    h = OAI.Helper("local_seeds") 

    for ix, row in df.sample(len(df)).iterrows():
        ID, txt = row.file_name, row.content
        CACHE1 = ".cache/"+str(ID)
        CACHE2 = ".cache_keywords/"+str(ID)
        CACHE3 = ".cache_title/"+str(ID)
        #print(row.file_name)
        if ix < 100000:
            if not os.path.isfile(CACHE1):
                table = h.ask(STEP1,txt,src="localSeedsStep1")
                with open(CACHE1, 'w', encoding='utf-8') as f:
                    f.write(table)
            if not os.path.isfile(CACHE2):
                table = h.ask(STEP2,txt,src="localSeedsStep2")
                with open(CACHE2, 'w', encoding='utf-8') as f:
                    f.write(table)
            if not os.path.isfile(CACHE3):
                table = h.ask(STEP3,txt,src="localSeedsStep3")
                with open(CACHE3, 'w', encoding='utf-8') as f:
                    f.write(table)       

    SEEDS = list(glob.glob(".cache_title/*"))

    allSeeds = []
    for seed in SEEDS: 
        try:
            ID = seed.split("/")[-1]
            txt = txtRead(seed) 
            txt = txt.replace("\n\n","\n")
            SUMMARY = txt.replace("TITLE:","").split("\n")[0].strip()
            allSeeds.append([ID,SUMMARY])
        except:
            print("Error with:",seed)
    DDTitle = pd.DataFrame(allSeeds)
    DDTitle.columns = ["src","title"]
    DDTitle.to_parquet("data/titles.parquet.gzip",compression='gzip')
    return DDTitle



def do_signals():
    SEEDS = list(glob.glob(".cache/*"))

    allSeeds = []
    for seed in SEEDS:
        try:
            DF = pd.read_csv(seed,sep="|")[1:].dropna(axis=1)
            DF["src"] = seed.split("/")[-1]
            allSeeds.append(DF)
        except:
            print("Error with:",seed)

    allSeeds = [x for x in allSeeds if len(x.columns) == 5]


    cleanSeeds =[]
    for seed in allSeeds:
        seed.columns = ["Signal","Change","10y horizon","Driving force","src"]
        cleanSeeds.append(seed)
    srcFiles = pd.read_parquet('data/urls.parquet.gzip')
    srcFiles.columns = ["origin","url","src"]
    allDf = pd.concat(cleanSeeds,axis=0,ignore_index=True) 
    allDf.to_parquet("data/signals.parquet.gzip",compression="gzip")
    return allDf



def do_meta():
    SEEDS = list(glob.glob(".cache_keywords/*"))
    srcFiles = pd.read_parquet('data/urls.parquet.gzip')
    srcFiles.columns = ["origin","url","src"]
    allSeeds = []
    for seed in SEEDS:
        try:
            txt = txtRead(seed)
            txt.replace("\n\n","\n")
            SUMMARY = txt.split("\nSummary:")[-1].replace("\n"," ").strip()
            C = txt.split("\n")
            TH = [x[8:].replace("'","").replace("[","").replace("]","") for x in C if "THEMES = " in x][0].strip().split(",")
            TH = [x.strip() for x in TH]
            KW = [x[10:].replace("'","").replace("[","").replace("]","") for x in C if "KEYWORDS = " in x][0].strip().split(",")
            KW = [x.strip() for x in KW]
            ID = seed.split("/")[-1]
            allSeeds.append([ID,KW,TH,SUMMARY])
        except:
            print("Error with:",seed)
    META = pd.DataFrame(allSeeds)
    META.columns = ["src","keywords","themes","summary"]
    META = META.merge(srcFiles,on="src",how="left")
    META.origin = META.origin.apply(lambda x: x.split("/")[-1])
    #META = META.drop(columns=['origin'])
    print(len(META))
    META.to_parquet("data/metatags.parquet.gzip",compression="gzip")
    META