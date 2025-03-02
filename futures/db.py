import os
import glob
import pandas as pd
import random
import json
import openai, re
import time

from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import DataFrameLoader
#from langchain.vectorstores import Chroma
from langchain.chains import LLMChain, StuffDocumentsChain
from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain.embeddings import OpenAIEmbeddings
from langchain.chat_models import ChatOpenAI
#from langchain.vectorstores import Chroma
from langchain_chroma import Chroma
import pandas as pd

import string
LETTERS = string.ascii_uppercase



import pandas as pd
import os



from dotenv import load_dotenv
load_dotenv()





class DB:

    def __init__(self, ai, basepath="./DB/"):
        self.ai = ai
        self.basepath = basepath
        self.embeddings = ai.embeddings
        self.srcArticles = ai.srcArticles
        self.srcSummaries = ai.srcSummaries
        self.srcSeeds = ai.srcSeeds
        self.srcMetas = ai.srcMetas

    def createDB(self):

        df = pd.read_parquet(self.srcArticles)
        df.columns = ["src","content","origin","LEN"]
        df = df[(df.LEN > 1500) & (df.LEN < 30000)].reset_index(drop=True)
        titles = pd.read_parquet(self.srcSummaries)
        df = df.merge(titles, on="src",how="left")
        mt = pd.read_parquet(self.srcMetas )
        mt = mt[["themes","category","keywords","url","src"]]
        df = df.merge(mt,on="src",how="left")

        df["source"] = df.url
        for x in df.columns:
            df[x] = df[x].astype(str)
        df_loader = DataFrameLoader(df, page_content_column="content")

        df_document = df_loader.load()
        text_splitter = CharacterTextSplitter(separator='\n\n',chunk_size=2000, chunk_overlap=200)
        chunked_documents = text_splitter.split_documents(df_document)

        # @TODO self.underlying_embeddings to be replaced with self.embeddings
        if not os.path.isfile(self.basepath+"chroma.sqlite3"):
            print("# VectorDB: start a new DB")
            self.vectordb = Chroma.from_documents(
                documents=[chunked_documents[0]],
                embedding=self.ai.underlying_embeddings,
                persist_directory=self.base_path
            )
            #vectordb.persist()
        else:
            print("# VectorDB: continue on the DB")
            self.vectordb = Chroma(persist_directory=self.basepath, embedding_function=self.ai.underlying_embeddings)
            print("- VectorDB: ",len(self.vectordb.get()["ids"]),"elements already stored.")
            LSDOCS = self.vectordb.get()["documents"]

        print("- VectorDB: adding",len(chunked_documents),"documents.")

        if self.vectordb:
            LSDOCS = self.vectordb.get()["documents"]
        else:
            LSDOCS = []
            
        for doc in chunked_documents:
            if not doc.page_content in LSDOCS:
                self.vectordb.add_documents(
                    documents=[doc], 
                    embedding=self.embeddings, 
                    persist_directory=self.basepath
                )
                time.sleep(0.2)
            else:
                pass
        LSDOCS = self.vectordb.get()["documents"]

        return self.vectordb


    def getClosest(self, txt,n=6):
        B = self.vectordb.similarity_search(txt, n)
        L = []
        X = []
        for b in list(B):
            L.append([b.metadata["src"], b.metadata["title"]])
            X.append(b.metadata["src"])
        return X
