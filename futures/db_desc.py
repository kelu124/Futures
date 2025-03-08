from langchain.chains.query_constructor.base import AttributeInfo


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
