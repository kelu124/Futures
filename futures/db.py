import os
import time
# import glob
import pandas as pd
# import random
# import json
# import openai, re
from langchain.text_splitter import CharacterTextSplitter
from langchain.document_loaders import DataFrameLoader
# from langchain.vectorstores import Chroma
# from langchain.chains import LLMChain, StuffDocumentsChain
# from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
# from langchain.embeddings import OpenAIEmbeddings
# from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
# from langchain.vectorstores import Chroma
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain.retrievers.self_query.base import SelfQueryRetriever
import futures.db_desc as dbdesc
from dotenv import load_dotenv
load_dotenv()


class DB:

    def __init__(self, ai, basepath="./DB/"):
        self.ai = ai
        self.basepath = basepath
        self.embeddings = ai.underlying_embeddings
        print(self.embeddings)
        self.srcArticles = ai.srcArticles
        self.srcSummaries = ai.srcSummaries
        self.srcSeeds = ai.srcSeeds
        self.srcMetas = ai.srcMetas
        self.metadata_field_info = dbdesc.metadata_field_info
        self.selfQueryllm = ChatOpenAI(model="gpt-4o-mini", temperature=0)

    def createDB(self):

        df = pd.read_parquet(self.srcArticles)
        df.columns = ["src", "content", "origin", "LEN"]
        df = df[(df.LEN > 1500) & (df.LEN < 30000)].reset_index(drop=True)
        titles = pd.read_parquet(self.srcSummaries)
        df = df.merge(titles, on="src", how="left")
        mt = pd.read_parquet(self.srcMetas)
        mt = mt[["themes", "category", "keywords", "url", "src"]]
        df = df.merge(mt, on="src", how="left")

        df["source"] = df.url
        for x in df.columns:
            df[x] = df[x].astype(str)
        df_loader = DataFrameLoader(df, page_content_column="content")

        df_document = df_loader.load()
        text_splitter = CharacterTextSplitter(
            separator="\n\n", chunk_size=2000, chunk_overlap=200
        )
        chunked_documents = text_splitter.split_documents(df_document)

        # @TODO self.underlying_embeddings to be replaced with self.embeddings
        if not os.path.isfile(self.basepath + "chroma.sqlite3"):
            print("# VectorDB: start a new DB")
            self.vectordb = Chroma.from_documents(
                documents=[chunked_documents[0]],
                embedding=self.ai.underlying_embeddings,
                persist_directory=self.basepath,
            )
            # vectordb.persist()
        else:
            print("# VectorDB: continue on the DB")
            self.vectordb = Chroma(
                persist_directory=self.basepath, embedding_function=self.ai.underlying_embeddings
            )
            print(
                "- VectorDB: ",
                len(self.vectordb.get()["ids"]),
                "elements already stored.",
            )
            LSDOCS = self.vectordb.get()["documents"]

        print("- VectorDB: adding", len(chunked_documents), "documents.")

        if self.vectordb:
            LSDOCS = self.vectordb.get()["documents"]
        else:
            LSDOCS = []

        for doc in chunked_documents:
            if not doc.page_content in LSDOCS:
                self.vectordb.add_documents(
                    documents=[doc],
                    embedding=self.ai.underlying_embeddings,
                    persist_directory=self.basepath,
                )
                time.sleep(0.2)
            else:
                pass
        LSDOCS = self.vectordb.get()["documents"]

        return self.vectordb

    def getArticles(self, topic, k):
        self.document_content_description = "Curation of articles"
        self.selfQR = SelfQueryRetriever.from_llm(
            self.selfQueryllm,
            self.vectordb,
            self.document_content_description,
            self.metadata_field_info,
            verbose=True,
            search_kwargs={"k": k},
        )
        return self.selfQR.invoke(input="Give me articles about " + topic)

    def getSummary(self, topic, k):
        docs = self.getArticles(topic, k)
        context = "Below is a list of summaries of articles, one per bullet point.\n\n"
        for doc in docs:
            summary = doc.metadata["summary"]
            context += "* " + summary + "\n"
        context += "You are a journalist writing a digest of a series of articles.\n"
        context += "Write a short page that captures the overlapping themes of these articles, and summarize them in a structure that follows the themes (up to 7 big themes).\n"
        context += "Don't include any mention of summaries or original articles, the piece should be read by itself and independant."
        context += "Your tone of voice is that of a journalist at NY Times, profesionnal, to the point. Keep sentences structure simple and clear.\n"
        context += "Include each and every article, as much as you can. Also, avoid bulletpoints. Don't include an introduction sentence (something like 'the articles this month'.. should be avoided at all costs), nor a conclusion part (ending with 'overall, these articles ..'. This should be avoided at all cost too.). The language should avoid flowery language or fancy language, it should be written in a way a 20yo non technical person can read it."

        return self.selfQueryllm.invoke(context).content, [
            x.metadata["src"] for x in docs
        ]

    def find_similar_sentences(
        self,
        query: str,
        df: pd.DataFrame,
        column_name: str,
        top_k: int = 5,
    ):
        """
        Find the most similar sentences to the input query from a dataframe column.

        Args:
            query (str): The input query sentence.
            df (pd.DataFrame): The dataframe containing the sentences.
            column_name (str): The name of the column containing the sentences.
            top_k (int): Number of similar sentences to return.

        Returns:
            List[str]: List of the top_k most similar sentences.
        """

        # Create documents from dataframe
        documents = []
        for i, row in df.iterrows():
            if pd.notna(row[column_name]) and isinstance(row[column_name], str):
                doc = Document(page_content=row[column_name], metadata={"index": i})
                documents.append(doc)
        # Create vector store
        vectorstore = FAISS.from_documents(documents, self.ai.underlying_embeddings)
        # Perform similarity search
        results = vectorstore.similarity_search(query, k=top_k)
        # Extract and return the text of similar sentences
        similar_sentences = [doc.page_content for doc in results]

        return similar_sentences

    def getCards(self, docs, topic="", top_k=5):
        seeds = pd.read_parquet(self.ai.srcSeeds)
        seeds = seeds[seeds.src.isin(docs)]
        if len(topic):
            txts = self.find_similar_sentences(
                topic, seeds, column_name="description", top_k=10
            )
            print(len(txts))
            seeds = seeds[seeds.description.isin(txts)]
            print(len(seeds))
        seeds = seeds[seeds.columns[0:-2]].reset_index(drop=True)

        behav = pd.read_parquet(self.ai.srcEmergingBehav)
        behav = behav[behav.src.isin(docs)]
        if len(topic):
            txts = self.find_similar_sentences(
                topic, behav, column_name="description", top_k=10
            )
            behav = behav[behav.description.isin(txts)]
        behav = behav[["name", "description"]].reset_index(drop=True)

        issue = pd.read_parquet(self.ai.srcEmergingIssue)
        issue = issue[issue.src.isin(docs)]
        if len(topic):
            txts = self.find_similar_sentences(
                topic, issue, column_name="description", top_k=10
            )
            issue = issue[issue.description.isin(txts)]
        issue = issue[["name", "description"]].reset_index(drop=True)

        techs = pd.read_parquet(self.ai.srcEmergingTechs)
        techs = techs[techs.src.isin(docs)]
        if len(topic):
            txts = self.find_similar_sentences(
                topic, techs, column_name="description", top_k=10
            )
            techs = techs[techs.description.isin(txts)]
        techs = techs[["name", "description"]].reset_index(drop=True)

        concerns = pd.read_parquet(self.ai.srcEmergingConcerns)
        concerns = concerns[concerns.src.isin(docs)]
        if len(topic):
            txts = self.find_similar_sentences(
                topic, concerns, column_name="description", top_k=10
            )
            concerns = concerns[concerns.description.isin(txts)]
        concerns = concerns[["name", "description"]].reset_index(drop=True)

        return seeds, behav, issue, techs, concerns

    def writeOracleTopic(self, topic, k=30):
        """Writes about a topic, picking 30 articles, 5 cards of each"""
        topic = "AI in infrastructure companies"
        txt, lst = self.getSummary(topic, k)
        a, b, c, d, e = self.getCards(lst, topic=topic, top_k=5)
        MD = "# *Topic*: " + topic + "\n\n"
        MD += "# Summary\n\n" + txt + "\n\n"
        MD += "# Seeds\n\n" + a.to_markdown() + "\n\n"
        MD += "# Concerns\n\n" + e.to_markdown() + "\n\n"
        MD += "# Behaviors\n\n" + b.to_markdown() + "\n\n"
        MD += "# Issues\n\n" + c.to_markdown() + "\n\n"
        MD += "# Technologies\n\n" + d.to_markdown() + "\n\n"
        MD += "# Links\n\n"
        titles = pd.read_parquet(self.srcSummaries)
        for lx in list(set(lst)):
            # print(lx)
            title = titles[titles["src"] == lx].iloc[0]["title"]
            MD += "\n* [" + title + "](https://futures.kghosh.me/" + lx + ")"
        return MD

    def getClosest(self, txt, n=6):
        B = self.vectordb.similarity_search(txt, n)
        L = []
        X = []
        for b in list(B):
            L.append([b.metadata["src"], b.metadata["title"]])
            X.append(b.metadata["src"])
        return X
