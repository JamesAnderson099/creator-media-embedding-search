from fastapi import FastAPI

from .infrai_embeddings import InfraiEmbeddings
from .media_catalog import AssetIngestRequest, MediaCatalog, MediaSearchRequest, ProcessingReceipt, SearchHit


def create_app(catalog: MediaCatalog | None = None) -> FastAPI:
    media = catalog or MediaCatalog(InfraiEmbeddings())
    app = FastAPI(title="Creator media embedding search")

    @app.post("/assets", status_code=201, response_model=ProcessingReceipt)
    def ingest_asset(body: AssetIngestRequest) -> ProcessingReceipt:
        return media.ingest(body)

    @app.post("/search", response_model=list[SearchHit])
    def search_media(body: MediaSearchRequest) -> list[SearchHit]:
        return media.search(body)

    return app


app = create_app()
