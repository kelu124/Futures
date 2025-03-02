from futures.substack import SubstackManager
from futures.llm import LLM
from futures.futurist import Futurist
from futures.db import DB
from futures.pages import PagesWriter

# Getting pages
sm = SubstackManager()
sm.download_pages()
sm.getPages()  # 25seconds

# Futurist
llm = LLM(datastore="data/")
f = Futurist(llm)

nb_articles = 30000
# Creating seeds
f.createSeeds(n=nb_articles)
# Creating metas
f.moreIntel(n=nb_articles)
# Creating metas
f.doMeta(n=nb_articles)

# Getting stories
f.writeAllStories()

# Preparing pages
db = DB(llm)
# Pages writer
pw = PagesWriter(db=db)
pw.createPages_metaPrep()
