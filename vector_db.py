from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, PointStruct


class QdrantStorage:
    def __init__(self, url="http://localhost:6333", collection="docs", dim=384):
        self.client = QdrantClient(url=url, timeout=30)
        self.collection = collection
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=VectorParams(size=dim, distance=Distance.COSINE),
            )

    def upsert(self, ids, vectors, payloads):
        points = [PointStruct(id=ids[i], vector=vectors[i], payload=payloads[i]) for i in range(len(ids))]
        self.client.upsert(self.collection, points=points)

    def search(self, query_vec: list[float], top_k: int):
    # CORRECT METHOD for your Qdrant version
        results = self.client.query_points(
        collection_name=self.collection,
        query=query_vec,  # Use 'query' parameter
        limit=top_k
    )
    
    # Extract from query_points results
        contexts = []
        sources = []
        if hasattr(results, 'points') and results.points:
            for point in results.points:
                payload = getattr(point, 'payload', {})
                text = payload.get("text", "")
                source = payload.get("source", "")
                if text:
                    contexts.append(text)
                    sources.append(source)
        else:
            # Fallback for different response format
            for hit in results:
                payload = getattr(hit, "payload", {})
                text = payload.get("text", "")
                source = payload.get("source", "")
                if text:
                    contexts.append(text)
                    sources.append(source)
        
        return {
            "contexts": contexts,
            "sources": sources
        }
