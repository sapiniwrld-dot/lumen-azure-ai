from azure.identity import DefaultAzureCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery

from app.ai import client
from app.config import settings

credential = DefaultAzureCredential()

search_client = SearchClient(
    endpoint=settings.search_endpoint,
    index_name=settings.search_index,
    credential=credential,
)


def retrieve(question: str, limit: int = 3) -> list[dict]:
    embedding = client.embeddings.create(
        model=settings.embedding_deployment,
        input=question,
    ).data[0].embedding

    vector_query = VectorizedQuery(
        vector=embedding,
        k_nearest_neighbors=limit,
        fields="content_vector",
    )

    results = search_client.search(
        search_text=question,
        vector_queries=[vector_query],
        select=["title", "content", "source"],
        top=limit,
    )

    return [
        {
            "title": result["title"],
            "content": result["content"],
            "source": result["source"],
            "score": result["@search.score"],
        }
        for result in results
    ]
