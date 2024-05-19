import helpers as s

BASE_URL = "substack.kghosh.me"
pages = s.get_cache(BASE_URL)

## Create content and analysis
s.getlinks()
s.pages_content("data/urls.parquet.gzip")
s.download_pages(archivepath='.archive')
s.createSeeds()
s.do_signals()
s.do_meta()

## DB
s.createDB()
df, signals = s.createPages_metaPrep()
s.createPages_metaUse(df, signals)