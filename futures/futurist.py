
import pandas as pd
import random
import json


from langchain.vectorstores import Chroma




from futures.fcts import getWeaksignals, getSummary, getMeta
from futures.fcts import getWeaksignals, getEmergingIssues, getEmergingBehaviors, getEmergingTechnologies

from futures.llm import LLM



class Futurist:

    def __init__(self, ai):
        #ai = LLM()
        self.ai = ai
        self.srcArticles = self.ai.srcArticles
        self.srcSummaries = self.ai.srcSummaries
        self.srcSeeds = self.ai.srcSeeds
        self.srcURLs = self.ai.srcURLs
        self.srcMetas = self.ai.srcMetas

    def createSeeds(self, minL=1500, maxL=30000, n=10):
        # Does the basics on the texts
        self.doProcessing(category="get_weaksignals", minL=1500, maxL=30000, n=n)
        self.doProcessing(category="get_summary", minL=1500, maxL=30000, n=n)

    def moreIntel(self, minL=1500, maxL=30000, n=10):
        # getEmergingIssues()  getEmergingTechnologies(): getEmergingBehaviors():
        self.doProcessing(category="get_weaksignals", minL=1500, maxL=30000, n=n)
        self.doProcessing(category="get_summary", minL=1500, maxL=30000, n=n)
        self.doProcessing(category="get_emergingbehaviors", minL=1500, maxL=30000, n=n)


    def doProcessing(self, category, minL=1500, maxL=30000, n=10):
        self.proccat = {}
        self.proccat["get_weaksignals"] = {"function": getWeaksignals(),
                                           "instruction": "Identify weak signals",
                                           "dataframe": self.ai.srcSeeds}
        self.proccat["get_summary"] = {"function": getSummary(),
                                           "instruction": "Do a summary",
                                           "dataframe": self.ai.srcSummaries}
        self.proccat["get_emergingissues"] = {"function": getEmergingIssues(),
                                           "instruction": "Identify emerging issues in this text",
                                           "dataframe": self.ai.srcEmergingIssue}
        self.proccat["get_emergingtechnologies"] = {"function": getEmergingTechnologies(),
                                           "instruction": "Identify emerging technologies in this text",
                                           "dataframe": self.ai.srcEmergingTechs}
        self.proccat["get_emergingbehaviors"] = {"function": getEmergingBehaviors(),
                                           "instruction": "Identify emerging behaviors in this text",
                                           "dataframe": self.ai.srcEmergingBehav}

                                                   
        texts = pd.read_parquet(self.srcArticles)
        texts = texts[(texts.LEN > minL) & (texts.LEN < maxL)]

        try:
            initIds = pd.read_parquet(self.proccat[category]["dataframe"]).src.unique()
        except:
            initIds = []
        # @ TODO probleme la ?
        print("IDs identifiees","\t",len(initIds),"\t",category)

        newItems = []

        for _, row in texts[:n].iterrows():
            if row["file_name"] not in initIds:
                try:
                    instructions = self.proccat[category]["instruction"]
                    function = self.proccat[category]["function"]
                    print(function)
                    result = self.ai.askTool(instructions, row["content"], function, category)
                    print(result)
                    result["src"] = row["file_name"]
                    newItems.append(result)
                except:
                    pass


        if len(newItems):
            newItems = pd.concat(newItems)
            if len(initIds):
                oldItems = pd.read_parquet(self.srcSummaries)
                newItems = pd.concat([newItems, oldItems])
                newItems.to_parquet(self.proccat[category]["dataframe"], compression="gzip")
            else:
                newItems.to_parquet(self.proccat[category]["dataframe"], compression="gzip")

        #return pd.read_parquet(self.proccat[category]["dataframe"])


    def doMeta(self,n=10):

        srcURLs = pd.read_parquet(self.srcURLs)
        srcURLs.columns = ["origin","url","src"]
        srcContent = pd.read_parquet(self.srcArticles)
        srcContent.columns = ["src","content","LEN"]
        #@ TODO add PDF filter on metas
        dfContent = srcURLs.merge(srcContent,on="src",how="left").dropna().reset_index(drop=True)

        try:
            meta_init = pd.read_parquet(self.srcMetas).src.unique()
        except:
            meta_init = []

        allMetas = []
        for ix, row in dfContent[0:n].iterrows():
            if not row["src"] in meta_init:
                meta = pd.DataFrame([json.loads(self.ai.askFunctions("Extract the metatags of this text", row["content"], getMeta(), "get_meta"))])
                meta["src"] = row["src"]
                allMetas.append(meta)


        if len(allMetas):
            META = pd.concat(allMetas)
            META = META.merge(dfContent, on="src", how="left")
            META = META[~META.origin.isna()]
            META.origin = META.origin.apply(lambda x: x.split("/")[-1])
            if len(meta_init):
                meta_init = pd.read_parquet(self.srcMetas)
                META = pd.concat([META, meta_init])

            META.to_parquet(self.srcMetas, compression="gzip")
            META
        META = pd.read_parquet(self.srcMetas)
        return META

    def writeStory(self, ids):
        try:
            df = pd.read_parquet(self.ai.srcConsolidated)
        except:
            return "No consolidated dataframe yet"
        try:
            stories_df = pd.read_parquet(self.ai.srcStories)
            stories_id = stories_df.origin.unique()
        except:
            stories_id = []

        stories = []
        for s in ids:
            if s not in stories_id:
                summaries = list( df[df.origin == s].summary )
                if len(summaries) > 6:
                    context = "* "+ "\n* ".join(summaries)

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

                    prompt  = "## Objective\n\n"
                    prompt += "You are a sci-fi writer, and you want to write a short story in one page or slightly less, that takes place in today world and seems very realistic.\n\n"
                    prompt += "You are given summaries of texts that contains elements (possibly forward-looking) that can feed this short story. Try and use each of the summaries, especially the 'innovative' parts.\n\n"
                    prompt += "You need to pick a theme for that story (which you don't need to tell me) and make it the backbone of the story.\n\nStart and give it a try! Don't forget to add at least a point in the story that comes from each  bullet point, but you can interleave the different points of course. Give me around one page that surprising short story - you don't need to give me any intro to it."
                    prompt += "\n\n## How to do it\n\n"+"* Change any reference to personal names so to anonymyse real persons names\n"
                    prompt += "* You will use a style mix of Terry Pratchett and Philip K Dick:\n\n"+STYLE
                    prompt += "\n\nStill, your style needs to be simple and readable by a 20yo, and keep a simple writing style.\n\n"
                    prompt += "\n\n## Summaries of texts\n\n"+ context
                    story = self.ai.ask(prompt)
                    title = self.ai.ask("Give a title to the short story below. Don't use quotes or any accompanying text:\n\n"+story)
            else:
                row = stories_df[stories_df.origin == s].iloc[0]
                story = row["story"]
                title = row["title"]
            stories.append([s,title,story])
        stories  = pd.DataFrame(stories,columns=["origin","title","story"])

        if len(stories):
            if len(stories_df):
                stories = pd.concat([stories_df,stories]).drop_duplicates()
            stories.to_parquet(self.ai.srcStories)


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