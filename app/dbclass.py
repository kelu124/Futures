import os

from langchain.storage import LocalFileStore
from langchain.embeddings import CacheBackedEmbeddings
from langchain.vectorstores import Chroma
from langchain.embeddings import OpenAIEmbeddings
from langchain.chains.query_constructor.base import AttributeInfo
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain_openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain.globals import set_llm_cache
from langchain.cache import SQLiteCache

STYLE = """* Master the Art of Footnotes: Treat them as your secret weapon. Use them to share amusing observations that pop into your head while telling the story. These asides should feel like you're whispering a clever joke to your reader without derailing the main narrative.
* Embrace the Pun-possible: Keep a sharp eye out for common phrases that could be twisted or taken literally in unexpected ways. If you spot a potential wordplay, don't resist it – Pratchett certainly wouldn't. But remember, the best puns aren't just groaners; they should also illuminate something about your story or characters.
* Wield Your Metaphors Like a Slightly Wobbly Sword: Craft comparisons that are simultaneously ridiculous and perfect. For example, don't just say someone is confused – say their thoughts are "as organized as a library after a tornado had decided to learn the Dewey Decimal System."
* Narrate Like a Clever Friend: Write as if you're telling the story to someone smart over a cup of tea, occasionally pausing to point out the absurdity of what you're describing. Let your narrator be wise, witty, and slightly world-weary, but never cynical.
* Turn Philosophy into Comedy: Take big, serious ideas – death, justice, belief, power – and examine them through the lens of everyday situations or minor absurdities. If you're writing about the nature of belief, maybe explore it through a character who accidentally starts a religion while trying to order pizza.
* Build Characters Who Are Sensibly Insane: Create people who operate on perfectly logical principles that just happen to be slightly askew from everyone else's reality. Their actions should make complete sense to them, even if they seem bizarre to others.
* Remember Pratchett's golden rule: the humor should serve the story, not the other way around. Each joke, pun, or amusing footnote should help reveal something about your world or characters.

AND THE MOST IMPORTANT

* Use information from the summaries to provide the reader with some actual insights into what the future might yield =)

"""

metadata_field_info = [
    AttributeInfo(
        name="LEN",
        description="length of the article",
        type="string or list[string]",
    ),
    AttributeInfo(
        name="author",
        description="curator of the article",
        type="string",
    ),
    AttributeInfo(
        name="keywords",
        description="Keywords characterizing the article",
        type="string",
    ),
    AttributeInfo(
        name="origin",
        description="Page where the article was curated",
        type="string",
    ),
    AttributeInfo(
        name="source",
        description="Original URL of the article",
        type="string",
    ),
    AttributeInfo(
        name="src",
        description="Unique identifier of the article",
        type="string",
    ),
    AttributeInfo(
        name="summary",
        description="Summary of the article",
        type="string",
    ),
    AttributeInfo(
        name="themes",
        description="List of the themes in the article",
        type="string",
    ),
    AttributeInfo(
        name="url",
        description="Original URL of the article",
        type="string",
    ),
    AttributeInfo(
        name="title",
        description="Title of the article",
        type="string",
    ),
]


class VectorDB:

    def __init__(
        self,
        dbpath="../DB/",
        embCache="../cache/",
        langchaindbpath="../data/.langchain.db",
        k=5,
    ):
        set_llm_cache(SQLiteCache(database_path=langchaindbpath))
        self.base_db_path = dbpath
        self.embCache = embCache
        self.underlying_embeddings = OpenAIEmbeddings(openai_api_key=os.getenv("OAI"))
        self.store = LocalFileStore(self.embCache)

        self.embeddings = CacheBackedEmbeddings.from_bytes_store(
            self.underlying_embeddings,
            self.store,
            namespace=self.underlying_embeddings.model,
        )

        if os.path.isfile(self.base_db_path + "chroma.sqlite3"):
            print("Loading from local files")
            self.vectordb = Chroma(
                persist_directory=self.base_db_path, embedding_function=self.embeddings
            )
        else:
            print("ERROR")

        self.simple_retriever = self.vectordb.as_retriever(search_kwargs={"k": k})

        self.document_content_description = "Curation of articles"

        self.selfQueryllm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
        self.creaLLM = ChatOpenAI(model="gpt-4o-mini", temperature=0.50)

        self.selfQR = SelfQueryRetriever.from_llm(
            self.selfQueryllm,
            self.vectordb,
            self.document_content_description,
            metadata_field_info,
            verbose=True,
            search_kwargs={"k": k},
        )

    def getArticles(self):
        IDS = self.vectordb.get()["ids"]
        origins = []
        for id in IDS:
            p = self.vectordb.get(ids=id)["metadatas"][0]["origin"]
            origins.append(p)
        return list(set(origins))

    def summarizeList(self, origin_list):
        docs = self.getList(origin_list)
        return self.summarizeDocuments(docs)

    def getList(self,origin_list):
        filteredlist = self.vectordb.as_retriever(
            search_kwargs={"k": 500, "filter": {"origin": {"$in": origin_list}}}
        )
        docs = filteredlist.invoke(input="Give me all the documents and articles")
        return docs 
    
    def summarizeDocuments(self, docs):
        context = "Below is a list of summaries of articles, one per bullet point.\n\n"
        for doc in docs:
            summary = doc.metadata["summary"]
            context += "* " + summary + "\n"
        context += "You are a journalist writing a digest of a series of artices.\n"
        context += "Write a short page that captures the overlapping themes of these articles, and summarize them in a structure that follows the themes (up to 7 big themes).\n"
        context += "Your tone of voice is that of a journalist at NY Times, profesional, to the point.\n"
        context += "Include each and every article, as much as you can. Also, avoid bulletpoints. Don't include an introduction sentence (something like 'the articles this month'.. should be avoided at all costs), nor a conclusion part (ending with 'overall, these articles ..'. This should be avoided at all cost too.). The language should avoid flowery language or fancy language, it should be written in a way a 20yo non technical person can read it."

        return self.selfllm.invoke(context).content
    

    def getStories(self, origin_list):
        docs =  self.getList(origin_list)
        if len(docs) > 6:
            context = ""
            for doc in docs:
                summary = doc.metadata["summary"]
                context += "* " + summary + "\n"
            prompt  = "## Objective\n\n"
            prompt += "You are a sci-fi writer, and you want to write a short story in one page or slightly less, that takes place in today world and seems very realistic.\n\n"
            prompt += "You are given summaries of texts that contains elements (possibly forward-looking) that can feed this short story. Try and use each of the summaries, especially the 'innovative' parts.\n\n"
            prompt += "You need to pick a theme for that story (which you don't need to tell me) and make it the backbone of the story.\n\nStart and give it a try! Don't forget to add at least a point in the story that comes from each  bullet point, but you can interleave the different points of course. Give me around one page that surprising short story - you don't need to give me any intro to it."
            prompt += "\n\n## How to do it\n\n"+"* Change any reference to personal names so to anonymyse real persons names\n* You will use a style mix of Terry Pratchett and Philip K Dick:\n\n"+STYLE
            prompt += "\n\n## Summaries of texts\n\n"+ context
            story = self.creaLLM.invoke(prompt).content
            title = self.creaLLM.invoke("Give a title to the short story below. Don't use quotes or any accompanying text:\n\n"+story).content

        return [title, story]
