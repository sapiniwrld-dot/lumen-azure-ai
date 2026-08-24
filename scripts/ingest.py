from pathlib import Path

from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    HnswAlgorithmConfiguration,
    SearchField,
    SearchFieldDataType,
    SearchIndex,
    SearchableField,
    SimpleField,
    VectorSearch,
    VectorSearchProfile,
)

from app.ai import client
from app.config import settings

EMBEDDING_DIMENSIONS = 1536
DOCUMENT_PATH = Path("data/support-handbook.txt")


def create_index(credential: DefaultAzureCredential) -> None:
    fields = [
        SimpleField(
            name="id",
            type=SearchFieldDataType.String,
            key=True,
            filterable=True,
        ),
        SearchableField(
            name="title",
            type=SearchFieldDataType.String,
        ),
        SearchableField(
            name="content",
            type=SearchFieldDataType.String,
        ),
        SimpleField(
            name="source",
            type=SearchFieldDataType.String,
            filterable=True,
        ),
        SearchField(
            name="content_vector",
            type=SearchFieldDataType.Collection(
                SearchFieldDataType.Single
            ),
            searchable=True,
            vector_search_dimensions=EMBEDDING_DIMENSIONS,
            vector_search_profile_name="vector-profile",
        ),
    ]

    vector_search = VectorSearch(
        algorithms=[
            HnswAlgorithmConfiguration(name="hnsw"),
        ],
        profiles=[
            VectorSearchProfile(
                name="vector-profile",
                algorithm_configuration_name="hnsw",
            ),
        ],
    )

    index = SearchIndex(
        name=settings.search_index,
        fields=fields,
        vector_search=vector_search,
    )

    index_client = SearchIndexClient(
        endpoint=settings.search_endpoint,
        credential=credential,
    )
    index_client.create_or_update_index(index)


def load_sections() -> list[dict]:
    text = DOCUMENT_PATH.read_text(encoding="utf-8")
    sections = [
        section.strip()
        for section in text.split("\n\n")
        if section.strip()
    ]

    documents = []

    for position, section in enumerate(sections):
        lines = section.splitlines()
        title = lines[0]
        content = "\n".join(lines[1:]) or title

        embedding = client.embeddings.create(
            model=settings.embedding_deployment,
            input=content,
        ).data[0].embedding

        documents.append(
            {
                "id": f"handbook-{position}",
                "title": title,
                "content": content,
                "source": DOCUMENT_PATH.name,
                "content_vector": embedding,
            }
        )

    return documents


def main() -> None:
    credential = DefaultAzureCredential()
    create_index(credential)

    documents = load_sections()

    search_client = SearchClient(
        endpoint=settings.search_endpoint,
        index_name=settings.search_index,
        credential=credential,
    )
    result = search_client.upload_documents(documents)

    succeeded = sum(item.succeeded for item in result)
    print(f"Indexed {succeeded}/{len(documents)} sections")


if __name__ == "__main__":
    main()
