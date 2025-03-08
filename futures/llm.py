# Utils
import pandas as pd
import json
# Chats
# from langchain.chat_models import ChatOpenAI
from langchain_openai import ChatOpenAI
# Caching

from langchain.embeddings import CacheBackedEmbeddings
#from langchain.embeddings import OpenAIEmbeddings
from langchain_openai import OpenAIEmbeddings
import datetime
# Messages
from langchain.schema import HumanMessage
# Caching
from langchain.globals import set_llm_cache
from langchain.cache import SQLiteCache
# Load env
from dotenv import load_dotenv
load_dotenv()


class LLM:

    def __init__(self, llmcache="data/", llm_fast="gpt-4o-mini",
                 datastore="data/",
                 llm_highend="gpt-4o"):
        # Setting up the stores
        self.underlying_embeddings = OpenAIEmbeddings()
        set_llm_cache(SQLiteCache(database_path=llmcache+".langchain.db"))
        self.store = SQLiteCache(database_path=\
                                 llmcache+".embedding.langchain.db")
        # cached embeddings
        self.embeddings = CacheBackedEmbeddings.from_bytes_store(
            self.underlying_embeddings, self.store,
            namespace=self.underlying_embeddings.model
        )

        self.llm_fast = llm_fast
        self.llm_highend = llm_highend
        self.datastore = datastore
        self.ai = ChatOpenAI(model=llm_fast)
        self.bigllm = ChatOpenAI(model=llm_highend)

        self.srcArticles = self.datastore + 'articles.parquet.gzip'
        self.srcSummaries = self.datastore + 'summaries.parquet.gzip'
        self.srcSeeds = self.datastore + 'seeds.parquet.gzip'
        self.srcMetas = self.datastore + 'metas.parquet.gzip'
        self.srcURLs = self.datastore + 'urls.parquet.gzip'
        self.srcStories = self.datastore + 'stories.parquet.gzip'
        self.srcConsolidated = self.datastore + 'consolidated.parquet.gzip'

        self.srcEmergingTechs = self.datastore + 'mrg_tech.parquet.gzip'
        self.srcEmergingBehav = self.datastore + 'mrg_behav.parquet.gzip'
        self.srcEmergingIssue = self.datastore + 'mrg_issue.parquet.gzip'

    def ask(self, question):
        answer = self.ai.invoke(question)
        print("--- "+self.llm_fast +":\t",
              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return json.loads(answer.model_dump_json())["content"]

    def askFunctions(self, instructions, text, function, function_name):
        messages = [
            HumanMessage(content=f"""
            ## Instructions
            {instructions}

            ## Text
            {text}
            """)
        ]

        response = self.ai.invoke(
            messages,
            functions=function,
            function_call={"name": function_name}
        )
        print("--- Function call:\t",
              datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        return response.additional_kwargs["function_call"]["arguments"]

    def askTool(self, instructions, text, function, function_name):
        js = self.askFunctions(instructions, text, function, function_name)
        js = json.loads(js)
        KEYS = list(js.keys())
        if len(KEYS) == 1:
            k = list(js.keys())[0]
            return pd.DataFrame(js[k])
        else:
            #print(str(js))
            return pd.DataFrame.from_dict(js, orient='index').T

