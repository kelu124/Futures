import os
import glob
import pandas as pd
import random
import json
import OAI
import openai, re
import time
from langchain.document_loaders import DataFrameLoader
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
from langchain.vectorstores import Chroma

import pandas as pd

import string
LETTERS = string.ascii_uppercase

from dotenv import load_dotenv
load_dotenv()

import pandas as pd
import os

from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI

from langchain.globals import set_llm_cache
from langchain.cache import SQLiteCache

set_llm_cache(SQLiteCache(database_path="data/.langchain.db"))

llm = ChatOpenAI(model="gpt-4o-mini")
bigllm = ChatOpenAI(model="gpt-4o")

import re
    
INLINE_LINK_RE = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
FOOTNOTE_LINK_TEXT_RE = re.compile(r'\[([^\]]+)\]\[(\d+)\]')
FOOTNOTE_LINK_URL_RE = re.compile(r'\[(\d+)\]:\s+(\S+)')


from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI

from langchain.globals import set_llm_cache
from langchain.cache import SQLiteCache

set_llm_cache(SQLiteCache(database_path="data/.langchain.db"))

from langchain_openai import OpenAIEmbeddings
from langchain.embeddings import CacheBackedEmbeddings
from langchain.cache import SQLiteCache

underlying_embeddings = OpenAIEmbeddings(
    openai_api_key=os.getenv("OAI")
)

store = SQLiteCache(database_path="data/.embedding.langchain.db")

if 0:
    embeddings = CacheBackedEmbeddings.from_bytes_store(
        underlying_embeddings, store, namespace=underlying_embeddings.model
    )
else:
    embeddings = underlying_embeddings


from helpers_nonllm import find_md_links, get_cache, download_substack_pages

from helpers_nonllm import  getlinks, getdraftlinks, pages_content

from helpers_nonllm import do_selenium, download_pages, txtRead, intersection





def createSeeds():
    STEP1 = "Acting as a Futurist, process the following text as a signal in a TABLE, first column a short 5–7 word summary of the signal, second column what kind of change is this (from what to what) 5–10 word summary, third column what might be different in 10 years time 5–10 word summary, fourth column What’s one driving force, or motivation, behind this change? 5–10 word summary:\n\n"

    STEP2 = "Process the following text, and give back only the top 10 most relevant keywords for the text, as a Python list (looking like KEYWORDS = ['keyword1', 'keyword2']). Then, on a new line, provide a list of the top three themes or categories the text belongs to (looking like THEMES = ['theme1', 'theme2']). On another new line, add a paragraph starting with 'Summary:'  which  summarizes the text in 4 to 5 sentences. \n\n"

    STEP3 = "Process the following text, and give this text a title, which should not be longer than 6 words, in the form 'TITLE: title of the article'.\n\n"
    df = pd.read_parquet('data/articles.parquet.gzip')
    df = df[(df.LEN > 1500) & (df.LEN < 30000)]
    if os.getenv("OAI") is not None:
        openai.api_key = os.getenv("OAI")
        print ("OPENAI_API_KEY is ready")
    else:
        print ("OPENAI_API_KEY environment variable not found")



    h = OAI.Helper("local_seeds") 

    for ix, row in df.sample(len(df)).iterrows():
        ID, txt = row.file_name, row.content
        CACHE1 = ".cache/"+str(ID)
        CACHE2 = ".cache_keywords/"+str(ID)
        CACHE3 = ".cache_title/"+str(ID)
        #print(row.file_name)
        if ix < 100000:
            if not os.path.isfile(CACHE1):
                table = h.ask(STEP1,txt,src="localSeedsStep1",v="gpt-4o-mini")
                with open(CACHE1, 'w', encoding='utf-8') as f:
                    f.write(table)
            if not os.path.isfile(CACHE2):
                table = h.ask(STEP2,txt,src="localSeedsStep2",v="gpt-4o-mini")
                with open(CACHE2, 'w', encoding='utf-8') as f:
                    f.write(table)
            # @TODO llm invoke
            if not os.path.isfile(CACHE3):
                table = h.ask(STEP3,txt,src="localSeedsStep3",v="gpt-4o-mini")
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
    META = META[~META.origin.isna()]
    META.origin = META.origin.apply(lambda x: x.split("/")[-1])
    #META = META.drop(columns=['origin'])
    print(len(META))
    META.to_parquet("data/metatags.parquet.gzip",compression="gzip")
    META


def createDB():
    if os.getenv("OAI") is not None:
        openai.api_key = os.getenv("OAI")
        print ("OPENAI_API_KEY is ready")
    else:
        print ("OPENAI_API_KEY environment variable not found")



    df = pd.read_parquet('data/articles.parquet.gzip')
    df.columns = ["src","content","LEN"]
    df = df[(df.LEN > 1500) & (df.LEN < 30000)].reset_index(drop=True)
    print(len(df),"articles of good lengths in the articles.parquet.gzip")
    titles = pd.read_parquet("data/titles.parquet.gzip")
    df = df.merge(titles, on="src",how="left")
    mt = pd.read_parquet("data/metatags.parquet.gzip")
    df = df.merge(mt,on="src",how="left")
    df.to_parquet("data/consolidated.parquet.gzip",compression="gzip")
    #df["text"] = df.content
    df["source"] = df.url
    for x in df.columns:
        df[x] = df[x].astype(str)
    df_loader = DataFrameLoader(df, page_content_column="content")

    df_document = df_loader.load()

    text_splitter = CharacterTextSplitter(separator='\n\n',chunk_size=2000, chunk_overlap=200)
    chunked_documents = text_splitter.split_documents(df_document)
    print(len(chunked_documents),"docs to add")

    base_path = "./DB/"
    if os.getenv("OAI") is not None:
        openai.api_key = os.getenv("OAI")
        print ("OPENAI_API_KEY is ready")
    else:
        print ("OPENAI_API_KEY environment variable not found")




    if not os.path.isfile(base_path+"chroma.sqlite3"):
        print("Start a new DB")
        vectordb = Chroma.from_documents(
            documents=[chunked_documents[0]],
            embedding=embeddings,
            persist_directory=base_path
        )
        vectordb.persist()
    else:
        print("Continue on the DB")
        vectordb = Chroma(persist_directory=base_path,embedding_function=embeddings)
        print(len(vectordb.get()["ids"]),"elements already stored.")
        LSDOCS = vectordb.get()["documents"]

    print("Already",len(vectordb.get()["documents"]),"documents.")
    print("Adding",len(chunked_documents),"documents.")

    if vectordb:
        LSDOCS = vectordb.get()["documents"]
    else:
        LSDOCS = []
        
    for doc in chunked_documents:
        # Check if the text already exists somewhere
        if not doc.page_content in LSDOCS:
            vectordb.add_documents(
                documents=[doc], 
                embedding=embeddings, 
                persist_directory=base_path
            )
            # Ugly hack to avoid reaching token per min limit 
            # So it sleeps 1s between page
            time.sleep(0.2)
            vectordb.persist()
        else:
            pass
            #print("Item already in the DB",doc.page_content[:100].replace("\n"," "))
    LSDOCS = vectordb.get()["documents"]
    vectordb.persist()
    print("Database filled in")
    return "DONE"



def getClosest(vectordb,txt):
    B = vectordb.similarity_search(txt,6)
    L = []
    X = []
    for b in list(B):
        #print(b.metadata["src"],b.metadata["title"])
        L.append([b.metadata["src"],b.metadata["title"]])
        X.append(b.metadata["src"])
    return X

def createPages_metaPrep(longtest=False):
    signals = pd.read_parquet("data/signals.parquet.gzip")
    metatags = pd.read_parquet("data/metatags.parquet.gzip")
    df = pd.read_parquet('data/articles.parquet.gzip')
    df.columns=  ["src","content","LEN"]
    df = df[(df.LEN > 1500) & (df.LEN < 30000)].reset_index(drop=True)
    titles = pd.read_parquet("data/titles.parquet.gzip")
    df = df.merge(titles,on="src",how="left")
    mt = pd.read_parquet("data/metatags.parquet.gzip")
    df = df.merge(mt,on="src",how="left")
    df.to_parquet("data/consolidated.parquet.gzip",compression="gzip")
    articles = intersection(metatags.src.unique(), signals.src.unique() )

    signals = signals[signals.src.isin(articles)]
    metatags = metatags[metatags.src.isin(articles)]
    len(articles)
    base_path = "./DB/"

    vectordb = Chroma(persist_directory=base_path,embedding_function=embeddings)
    print(len(vectordb.get()["ids"]),"elements already stored.")
    LSDOCS = vectordb.get()["documents"]
    metatags["closest"] = ""
    if longtest:
        metatags["closest"] = metatags["summary"].apply(lambda x: getClosest(vectordb,x))
        metatags.to_parquet("data/pages_metatags_with_closest.parquet.gzip", compression = "gzip")
    return df, signals

def createPages_metaUse(df, signals):
    metatags = pd.read_parquet("data/pages_metatags_with_closest.parquet.gzip")
    metatags["kwsl"] = metatags["keywords"].apply(lambda lst: [x.lower().replace('"','') for x in lst])
    metatags = metatags.merge(df[["src","title"]],on="src",how="left")
    for ix, row in metatags.iterrows():
        try:
            ID = row["src"]
            TXT = "# __"+row["title"] +"__, from (["+row.origin+"](https://kghosh.substack.com/p/"+row.origin+").)\n\n"
            TXT += "__[External link]("+str(row.url)[2:-1]+")__\n\n"
            TXT += "\n\n## Summary\n\n"
            TXT += row["summary"] + "\n\n## Keywords\n\n"
            TXT += "* "+"\n* ".join(row["keywords"])
            TXT += "\n\n## Themes\n\n"
            TXT += "* "+"\n* ".join(row["themes"])
            TXT += "\n\n## Signals\n\n"    
            SIG = signals[signals.src == ID]
            TXT += SIG[list(SIG.columns)[:-1]].to_markdown(index=False)
            if 1:
                TXT += "\n\n## Closest\n\n"
                TXT += "* "+"\n* ".join([ "["+df.loc[df["src"] == x,"title"].iloc[0]+"]("+x+")" for x in row["closest"][1:]])
            with open("docs/"+ID+".md", "w") as f:
                f.write(TXT) 
        except:
            print("Error with",row["src"])
    allkw = []
    for kw in metatags.themes:# keywords: #as an alternative
        allkw = allkw+list(kw)
    KW = list(set(allkw))
    KW = list(set([x.capitalize().replace('"','') for x in KW]))
    KW = [x for x in KW if not x.isnumeric()]
    KW.sort()
    print(len(KW))
    random.shuffle(KW)
    KW[:10]
    h = OAI.Helper("local_seeds_classif") 
    with open("data/categories_small.csv","r") as f:
        ALL = f.read().split("\n")
    ALL.sort()
    ALL

    with open("data/categories_ax.json","r") as f:
        ax = json.loads(f.read())
    with open("data/categories_bx.json","r") as f:
        bx = json.loads(f.read())


    for ix, row in metatags.iterrows():
        if ix < 100000: # useless
            ax[row["src"]] = {}
            if row["src"] not in ax.keys():
                PROMPT = "You are given a text below. You need to pick the five most relevant themes of this text from the list of keywords below:\n\n* "+"\n*".join(ALL)+"\n\n\nAnswer only with 3 items of this list, separated by commas"
                ANS =  h.ask(PROMPT,row["summary"],src="tag",v="gpt-4o-mini")
                LST = [x.strip() for x in ANS.split(",") if x.strip() in ALL]
                ax[row["src"]] = LST
                for x in LST:
                    if x not in bx.keys():
                        bx[x] = []
                    bx[x].append(row["src"])

    ## Write Index
    INDEX  = "# Overview \n\n"
    INDEX += "This page tries to capture the information obtained in my [tech watch](https://substack.kghosh.me/). The different links and pages are captured below, trying to catalogue different weak signals." 


    for letter in LETTERS:
        kws = [x for x in list(bx.keys()) if x[0] == letter]

        if len(kws):
            INDEX += "\n\n## Letter '"+letter.upper()+"' \n\n"
            for kw in kws:
                INDEX += "\n### Category: __"+kw+"__: \n\n"
                lst = bx[kw] 
                for x in lst:
                    TITRE = df.loc[df.src == x,"title"].iloc[0]
                    INDEX += "* ["+TITRE+"]("+x+")\n"

    INDEX += "\n\n## Others\n\n"
    for x in ax:
        if len(ax[x]) == 0:
            TITRE = df.loc[df.src == x,"title"].iloc[0]
            INDEX += "* ["+TITRE+"]("+x+")\n"
    with open("docs/index.md", "w") as f:
        f.write(INDEX) 