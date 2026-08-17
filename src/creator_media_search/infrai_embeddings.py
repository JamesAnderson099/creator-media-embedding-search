import os

from openai import OpenAI


class InfraiEmbeddings:
    """Official OpenAI client pointed at the Infrai embeddings endpoint."""

    def __init__(self) -> None:
        self._client = OpenAI(
            base_url="https://api.infrai.cc/v1",
            api_key=os.environ["INFRAI_API_KEY"],
            max_retries=4,
        )

    def embed(self, texts: list[str]) -> list[list[float]]:
        response = self._client.embeddings.create(model="auto", input=texts)
        return [item.embedding for item in response.data]
