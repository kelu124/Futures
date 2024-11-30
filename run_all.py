import helpers as s

BASE_URL = "substack.kghosh.me"
pages = s.get_cache(BASE_URL)
print(pages)
s.download_substack_pages(pages)
## Create content and analysis
s.getlinks()
s.getdraftlinks()
s.pages_content("data/urls.parquet.gzip")
s.download_pages(archivepath='.archive')
s.createSeeds()
s.do_signals()
s.do_meta()
print("DoDB")
## DB
s.createDB()
findclosest = False 
df, signals = s.createPages_metaPrep(longtest=findclosest)
if findclosest:
    s.createPages_metaUse(df, signals)

print("Do Stories")
from writers import getStories
stories = getStories()