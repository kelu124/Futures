import pandas as pd
import random
import json
from futures.commons import intersection
import os
import glob
import re

class PagesWriter:

    def __init__(self, db):
        self.db = db
        self.datastore = self.db.ai.datastore

        self.srcArticles = self.db.ai.srcArticles
        self.srcSummaries = self.db.ai.srcSummaries
        self.srcSeeds = self.db.ai.srcSeeds
        self.srcURLs = self.db.ai.srcURLs
        self.srcMetas = self.db.ai.srcMetas
        self.srcEmergingTechs = self.db.ai.srcEmergingTechs
        self.srcEmergingBehav = self.db.ai.srcEmergingBehav
        self.srcEmergingIssue = self.db.ai.srcEmergingIssue
        self.srcEmergingCncrn = self.db.ai.srcEmergingConcerns

        self.srcMetaProximities = self.datastore +\
            "metas_proximity.parquet.gzip"
        self.srcConsolidated = self.datastore +\
            "consolidated.parquet.gzip"
        self.srcPages = "./docs/"

    def createPages_metaPrep(self, longtest=False):
        signals = pd.read_parquet(self.db.ai.srcSeeds)
        metatags = pd.read_parquet(self.db.ai.srcMetas)
        df = pd.read_parquet(self.db.ai.srcArticles)
        df.columns = ["src", "content", "origin","LEN"]
        df = df[(df.LEN > 1500) & (df.LEN < 30000)].reset_index(drop=True)
        df.reset_index(drop=True).to_parquet(self.srcConsolidated, compression="gzip")
        articles = intersection(metatags.src.unique(), signals.src.unique())

        signals = signals[signals.src.isin(articles)]
        metatags = metatags[metatags.src.isin(articles)]

        metatags["closest"] = ""
        if longtest:
            vectordb = self.db.vectordb
            print("- vectordb:",len(vectordb.get()["ids"]),"elements stored.")
            LSDOCS = vectordb.get()["documents"]
            # @TODO : add metatags for distance
            metatags["closest"] = metatags["summary"].apply(\
                lambda x: self.db.getClosest(vectordb, x))
            metatags.reset_index(drop=True).to_parquet(self.srcMetaProximities, compression="gzip")
        return df, signals

    def createPages(self):
        # @TODO

        meta = pd.read_parquet(self.srcMetas).reset_index(drop=True)
        signals = pd.read_parquet(self.srcSeeds).reset_index(drop=True)
        summaries = pd.read_parquet(self.srcSummaries).reset_index(drop=True)
        df = pd.read_parquet(self.db.ai.srcArticles)
        techs = pd.read_parquet(self.srcEmergingTechs).reset_index(drop=True)
        behav = pd.read_parquet(self.srcEmergingBehav).reset_index(drop=True)
        issue = pd.read_parquet(self.srcEmergingIssue).reset_index(drop=True)
        cncrn = pd.read_parquet(self.srcEmergingCncrn).reset_index(drop=True)

        for _, row in meta.iterrows():

            ID = row["src"]
            fn = "docs/"+ID+".md"
            if not os.path.isfile(fn):
                try:
                    S = summaries[summaries.src == ID]["title"].iloc[0]
                    origin = str(df[df.file_name == ID]["origin"].iloc[0])
                    TXT = "# __"+S +"__, (from page ["+origin.replace("d","")+"](https://kghosh.substack.com/p/"+origin.replace("d","")+").)\n\n"

                
                    TXT += "__[External link]("+str(row.url)[2:-1]+")__\n\n"
                    TXT += "\n\n## Keywords\n\n"
                    TXT += "* "+"\n* ".join([x.strip() for x in row["keywords"].split(",")])
                    TXT += "\n\n## Themes\n\n"
                    TXT += "* "+"\n* ".join([x.strip() for x in row["themes"].split(",")])
                    TXT += "\n\n## Other\n\n"
                    TXT += "* Category: "+row["category"] +"\n"
                    TXT += "* Type: "+row["type"]
                    try:
                        TXT += "\n\n## Summary\n\n"
                        TXT += summaries[summaries.src == ID].summary.iloc[0]
                    except:
                        pass
                    SIG = signals[signals.src == ID]
                    if len(SIG):
                        TXT += "\n\n## Signals\n\n"
                        TXT += SIG[list(SIG.columns)[:-1]].to_markdown(index=False)
                    CON = cncrn[cncrn.src == ID]
                    if len(CON):
                        TXT += "\n\n## Concerns\n\n"
                        TXT += CON[["name","description"]].to_markdown(index=False)
                    BVR = behav[behav.src == ID]
                    if len(BVR):
                        TXT += "\n\n## Behaviors\n\n"
                        TXT += BVR[["name","description"]].to_markdown(index=False)
                    TEK = techs[techs.src == ID]
                    if len(TEK):
                        TXT += "\n\n## Technologies\n\n"
                        TXT += TEK[["name","description"]].to_markdown(index=False)
                    ISS = issue[issue.src == ID]
                    if len(ISS):
                        TXT += "\n\n## Issues\n\n"
                        TXT += ISS[["name","description"]].to_markdown(index=False)
                    with open(fn, "w") as f:
                        f.write(TXT)
                except:
                    print("Error with",fn)
                    pass

    def clean_markdown_dates(self, folder_path: str = None) -> None:
        """
        Scans all .md files in the given folder and replaces any occurrence
        of an 8-digit string followed by 'd' (e.g. 20250202d) with the 8-digit
        string only (e.g. 20250202).
        """
        pattern = re.compile(r'(\d{8})d')
        if not folder_path:
            folder_path = self.srcPages 
        for filename in os.listdir(folder_path):
            if not filename.lower().endswith(".md"):
                continue

            file_path = os.path.join(folder_path, filename)

            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            updated_content = pattern.sub(r'\1', content)

            if updated_content != content:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(updated_content)

    def createPagesIndex(self):
        ## Write Index
        INDEX  = "# Overview \n\n"
        INDEX += "This page tries to capture the information obtained in my [tech watch](https://substack.kghosh.me/). The different links and pages are captured below, trying to catalogue different weak signals." 
        summaries = pd.read_parquet(self.srcSummaries).reset_index(drop=True)

        for ix, row in summaries.iterrows():
            INDEX += "\n* ["+row["title"]+"]("+row["src"]+")"


        INDEX += "\n\n---\n\n"

        TOP = glob.glob("docs/analyses/topics/**/*.md", recursive=True)
        TOP.sort()

        INDEX += "\n\n# Analyses by Topic\n\n"
        for p in TOP:
            with open(p, "r") as f:
                name = f.readline().replace("# *Topic*: ","").strip()
            INDEX += "\n* ["+name+"]("+p[5:]+")"

        #print(TOP)
        YRLY = glob.glob("docs/analyses/yearly/**/*.md", recursive=True)
        INDEX += "\n\n# Yearly reviews\n\n"
        for p in YRLY:
            with open(p, "r") as f:
                name = f.readline().replace("#","").strip()
            INDEX += "\n* ["+name+"]("+p[5:]+")"

        with open("docs/index.md", "w") as f:
            f.write(INDEX) 
