from typing import List
from pathlib import Path
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import ChatPromptTemplate
from langchain.schema import StrOutputParser
from langchain_community.document_loaders import (
    PyMuPDFLoader,
)
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores.chroma import Chroma
from langchain.indexes import SQLRecordManager, index
from langchain.schema import Document
from langchain.schema.runnable import Runnable, RunnablePassthrough, RunnableConfig
from langchain.callbacks.base import BaseCallbackHandler
from langchain_community.document_loaders import Docx2txtLoader
from langchain.text_splitter import CharacterTextSplitter
from chainlit.input_widget import Select
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction
from langchain.storage import LocalFileStore
from langchain.embeddings import CacheBackedEmbeddings

import chainlit as cl
import os, glob

from langchain_core.globals import set_llm_cache
from langchain.cache import SQLiteCache
set_llm_cache(SQLiteCache(database_path=".chainlit/.langchain_cache.db"))

from typing import Optional

from dotenv import load_dotenv

if os.path.isfile(".env"):
    load_dotenv(".env")
else:
    print("No local .env file")
print("Key: ",os.getenv("OPENAI_API_KEY"))

#from literalai import LiteralClient
#lai = LiteralClient()
#lai.instrument_openai()


underlying_embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OPENAI_API_KEY"))


store = LocalFileStore("./cache/")

embeddings_model = CacheBackedEmbeddings.from_bytes_store(
    underlying_embeddings, store, namespace=underlying_embeddings.model
)

PDF_STORAGE_PATH = "../data/docs"


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("probono", "probono"):
        return cl.User(
            identifier="Probono", metadata={"role": "user", "provider": "credentials"}
        )
    else:
        return None
    


base_path = "../DB/"
if os.path.isfile(base_path + "chroma.sqlite3"):
    print("Loading from local files")
    doc_search = Chroma(
        persist_directory=base_path, embedding_function=embeddings_model
    )
else:
    print("ERROR")

model = ChatOpenAI(model_name="gpt-4o-mini", streaming=True)


@cl.on_chat_start
async def on_chat_start():

    settings = await cl.ChatSettings(
        [
            Select(
                id="details",
                label="Do you want to see the sources of the answers",
                values=["No","Yes"],
                initial_index=1,
            )
        ]
    ).send()
    cl.user_session.set("details", settings["details"])

    template = """Answer the question based only on the following context:

    {context}

    Question: {question}
    """
    prompt = ChatPromptTemplate.from_template(template)

    def format_docs(docs):
        return "\n\n".join([d.page_content for d in docs])

    retriever = doc_search.as_retriever(search_kwargs={"k": 10})

    runnable = (
        {"context": retriever | format_docs, "question": RunnablePassthrough()}
        | prompt
        | model
        | StrOutputParser()
    )

    cl.user_session.set("runnable", runnable)
    await setup_agent(settings)

@cl.on_settings_update
async def setup_agent(settings):
    cl.user_session.set("details", settings["details"])

@cl.on_message
async def on_message(message: cl.Message):
    runnable = cl.user_session.get("runnable")  # type: Runnable
    msg = cl.Message(content="")

    class PostMessageHandler(BaseCallbackHandler):
        """
        Callback handler for handling the retriever and LLM processes.
        Used to post the sources of the retrieved documents as a Chainlit element.
        """

        def __init__(self, msg: cl.Message):
            BaseCallbackHandler.__init__(self)
            self.msg = msg
            self.sources = set()  # To store unique pairs

        def on_retriever_end(self, documents, *, run_id, parent_run_id, **kwargs):
            for d in documents:
                self.sources.add(d.metadata["title"])  # Add unique pairs to the set

        def on_llm_end(self, response, *, run_id, parent_run_id, **kwargs):
            if len(self.sources):
                print(len(self.sources))
                sources_text = "* "+"\n* ".join(
                    [x.split(os.sep)[-1].replace(".docx", "").strip() for x in self.sources]
                )
                if cl.user_session.get("details") == "Yes":
                    self.msg.elements.append(
                        cl.Text(name="Sources", content=sources_text, display="inline")
                    )

    async for chunk in runnable.astream(
        message.content,
        config=RunnableConfig(
            callbacks=[cl.LangchainCallbackHandler(), PostMessageHandler(msg)]
        ),
    ):
        await msg.stream_token(chunk)

    await msg.send()
