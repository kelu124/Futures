
import pandas as pd
import random
import json
import os

from langchain.vectorstores import Chroma




from futures.fcts import getWeaksignals, getSummary, getMeta, getEmergingConcerns
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
        self.doProcessing(category="get_emergingissues", minL=1500, maxL=30000, n=n)
        self.doProcessing(category="get_emergingtechnologies", minL=1500, maxL=30000, n=n)
        self.doProcessing(category="get_emergingbehaviors", minL=1500, maxL=30000, n=n)
        self.doProcessing(category="get_emergingconcerns", minL=1500, maxL=30000, n=n)

    def doProcessing(self, category, minL=1500, maxL=30000, n=10):
        self.proccat = {}
        print("# Doing",category,"processing")
        self.proccat["get_weaksignals"] = {"function": getWeaksignals(),
                                           "instruction": "Identify weak signals",
                                           "dataframe": self.ai.srcSeeds}
        self.proccat["get_summary"] = {"function": getSummary(),
                                           "instruction": "Do a summary",
                                           "dataframe": self.ai.srcSummaries}
        self.proccat["get_emergingissues"] = {"function": getEmergingIssues(),
                                           "instruction": "Identify emerging issues in this text",
                                           "dataframe": self.ai.srcEmergingIssue}
        self.proccat["get_emergingconcerns"] = {"function": getEmergingConcerns(),
                                           "instruction": "Identify emerging concerns in this text",
                                           "dataframe": self.ai.srcEmergingConcerns}
        self.proccat["get_emergingtechnologies"] = {"function": getEmergingTechnologies(),
                                           "instruction": "Identify emerging technologies in this text",
                                           "dataframe": self.ai.srcEmergingTechs}
        self.proccat["get_emergingbehaviors"] = {"function": getEmergingBehaviors(),
                                           "instruction": "Identify emerging behaviors in this text",
                                           "dataframe": self.ai.srcEmergingBehav}

                                                   
        texts = pd.read_parquet(self.srcArticles)
        texts = texts[(texts.LEN > minL) & (texts.LEN < maxL)]

        namefile = self.proccat[category]["dataframe"]
        try:
            initIds = pd.read_parquet(namefile).src.unique()
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
                    #print(function)
                    result = self.ai.askTool(instructions, row["content"], function, category)
                    #print(result)
                    result["src"] = row["file_name"]
                    newItems.append(result)
                except:
                    pass

        

        if len(newItems):
            #print("* Saving to",)
            newItems = pd.concat(newItems)
            if len(initIds):
                oldItems = pd.read_parquet(namefile)
                newItems = pd.concat([newItems, oldItems])
        else:
            if len(initIds):
                oldItems = pd.read_parquet(namefile)
                newItems = oldItems

        #if any(["page_x","origin_x","page_y","origin_y"] in newItems.columns):
        #    newItems = newItems.rename(columns={"page_x": "page", "origin_x": "origin"})
        #    newItems.drop(['page_y', 'origin_y'], inplace = True, axis=1)

        newItems.reset_index(drop=True).to_parquet(namefile, compression="gzip")

        #return pd.read_parquet(self.proccat[category]["dataframe"])


    def doMeta(self, minL=1500, maxL=30000, n=10):
        print("# Doing metas processing")
        srcURLs = pd.read_parquet(self.srcURLs)
        srcURLs.columns = ["path","url","src"]
        srcContent = pd.read_parquet(self.srcArticles)
        srcContent.drop([x for x in list(srcContent.columns) if "n_" in x], axis=1, inplace=True)

        srcContent = srcContent[(srcContent.LEN > minL) & (srcContent.LEN < maxL)]

        #print(srcContent)
        srcContent.columns = ["src","content","LEN","origin"]
        #@ TODO add PDF filter on metas
        dfContent = srcURLs.merge(srcContent,on="src",how="left").dropna().reset_index(drop=True)
        #print(dfContent)
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
            META.origin = META.origin.apply(lambda x: str(x).split("/")[-1])
            if len(meta_init):
                meta_init = pd.read_parquet(self.srcMetas)
                META = pd.concat([META, meta_init])
            META = META.reset_index(drop=True)
            META["LEN"] = META["content"].apply(lambda x: int(len(str(x))))
            META.to_parquet(self.srcMetas, compression="gzip")
        META = pd.read_parquet(self.srcMetas)
        return META


    def writeStory(self, ids):
        """Takes dictionnary, title plus list of articles"""
        
        try:
            df = pd.read_parquet(self.ai.srcSummaries)
        except:
            return "No consolidated dataframe yet"
        try:
            stories_df = pd.read_parquet(self.ai.srcStories)
            stories_id = stories_df.src.unique()
            #print(stories_id)
        except:
            stories_id = []
        #print(stories_id)
        TODO = [x for x in list(ids.keys()) if ((x not in stories_id) and x)]
        if len(TODO):
            print("# Writing stories for",TODO)
        stories = []
        for s in ids.keys():
            #print("- Checking story for", s)
            if s != None :
                #print("- Story for", s)
                if s not in stories_id:
                    print("- Doing story for", s)
                    summaries = list(df[df.src.isin(ids[s])].summary)
                    if len(summaries) > 6:
                        context = "* " + "\n* ".join(summaries)

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
                        print("* Pas assez de résumés")
                else:
                    row = stories_df[stories_df.src == s].iloc[0]
                    story = row["story"]
                    title = row["title"]
                stories.append([s,title,story])
        stories  = pd.DataFrame(stories,columns=["src","title","story"])
        #print(stories)
        if len(stories):
            if len(stories_id):
                stories = pd.concat([stories_df,stories]).drop_duplicates()
            stories = stories.reset_index(drop=True)
            stories.to_parquet(self.ai.srcStories)

    def getLinksPerArticle(self):
        articles = {}
        summaries = list(pd.read_parquet(self.srcSummaries).src.unique())
        df = pd.read_parquet(self.ai.srcArticles)
        df = df[df.file_name.isin(summaries)]
        for orig in df.origin.unique():
            if len(str(orig)):
                articles[orig]=list(df[df.origin == orig].file_name)
        return articles
    
    def writeAllStories(self):
        articles = self.getLinksPerArticle()
        #print(articles)
        story = self.writeStory(articles)

    def getStory(self, id):
        df = pd.read_parquet(self.ai.srcStories)
        df = df[df.src == id]
        if len(df):
            return "## "+df["title"].iloc[0]+"\n\n"+df["story"].iloc[0]
        else:
            return "No story for this ID"
        
