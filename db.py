import helpers as s

BASE_URL = "substack.kghosh.me"
pages = s.get_cache(BASE_URL)

## DB
s.createDB()
df, signals = s.createPages_metaPrep()
s.createPages_metaUse(df, signals)
