import pandas as pd
import random
import json
from futures.commons import intersection


class PagesWriter:

    def __init__(self, db):
        self.db = db
        self.srcArticles = self.db.ai.srcArticles
        self.srcSummaries = self.db.ai.srcSummaries
        self.srcSeeds = self.db.ai.srcSeeds
        self.srcURLs = self.db.ai.srcURLs
        self.srcMetas = self.db.ai.srcMetas
        self.datastore = self.db.ai.datastore
        self.srcMetaProximities = self.datastore +\
            "metas_proximity.parquet.gzip"
        self.srcConsolidated = self.datastore +\
            "consolidated.parquet.gzip"
        self.srcPages = "./docs/"

    def createPages_metaPrep(self, longtest=False):
        signals = pd.read_parquet(self.db.ai.srcSeeds)
        metatags = pd.read_parquet(self.db.ai.srcMetas)
        df = pd.read_parquet(self.db.ai.srcArticles)
        df.columns = ["src", "content", "LEN"]
        df = df[(df.LEN > 1500) & (df.LEN < 30000)].reset_index(drop=True)
        df.to_parquet(self.srcConsolidated, compression="gzip")
        articles = intersection(metatags.src.unique(), signals.src.unique())

        signals = signals[signals.src.isin(articles)]
        metatags = metatags[metatags.src.isin(articles)]
        vectordb = self.db.vectordb
        print(len(vectordb.get()["ids"]),"elements already stored.")
        LSDOCS = vectordb.get()["documents"]
        # @TODO : add metatags for distance
        metatags["closest"] = ""
        if longtest:
            metatags["closest"] = metatags["summary"].apply(\
                lambda x: db.getClosest(vectordb, x))
            metatags.to_parquet(self.srcMetaProximities, compression="gzip")
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