import pandas as pd
import os

from langchain.chains.question_answering import load_qa_chain
from langchain_openai import ChatOpenAI

from langchain.globals import set_llm_cache
from langchain.cache import SQLiteCache

set_llm_cache(SQLiteCache(database_path="data/.langchain.db"))

def create_agent_chain(llm):
    chain = load_qa_chain(llm, chain_type="stuff")
    return chain

llm = ChatOpenAI(model="gpt-4o-mini")
bigllm = ChatOpenAI(model="gpt-4o")
chain = create_agent_chain(llm) #cached_underlying_embeddings_chroma

def get_llm_response(query,vectordb,temperature=0.1,k=10):
    matching_docs = vectordb.similarity_search(query,k)
    answer = chain.run(input_documents=matching_docs, question=query)

    return answer, matching_docs



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

def getStories():
    df = pd.read_parquet("data/consolidated.parquet.gzip")
    src = [x for x in list(df.origin.unique()) if str(x).startswith("202")]
    stories = []

    for s in src:
        print(s)
        REFS = list( df[df.origin == s].summary )
        if len(REFS) > 6:
            context = "* "+ "\n* ".join(REFS)

            prompt  = "## Objective\n\n"
            prompt += "You are a sci-fi writer, and you want to write a short story in one page or slightly less, that takes place in today world and seems very realistic.\n\n"
            prompt += "You are given summaries of texts that contains elements (possibly forward-looking) that can feed this short story. Try and use each of the summaries, especially the 'innovative' parts.\n\n"
            prompt += "You need to pick a theme for that story (which you don't need to tell me) and make it the backbone of the story.\n\nStart and give it a try! Don't forget to add at least a point in the story that comes from each  bullet point, but you can interleave the different points of course. Give me around one page that surprising short story - you don't need to give me any intro to it."
            prompt += "\n\n## How to do it\n\n"+"* Change any reference to personal names so to anonymyse real persons names\n"
            prompt += "* You will use a style mix of Terry Pratchett and Philip K Dick:\n\n"+STYLE
            prompt += "\n\nStill, your style needs to be simple and readable by a 20yo, and keep a simple writing style.\n\n"
            prompt += "\n\n## Summaries of texts\n\n"+ context
            story = llm.invoke(prompt).content
            title = llm.invoke("Give a title to the short story below. Don't use quotes or any accompanying text:\n\n"+story).content
            print(s,title)
            stories.append([s,title,story])

    STORY  = pd.DataFrame(stories,columns=["post","title","story"])
    STORY.to_parquet("data/stories.parquet.gzip")
    return STORY