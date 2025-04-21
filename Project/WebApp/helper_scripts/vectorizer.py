from sentence_transformers import SentenceTransformer
import numpy as np

class ArticleVectorizer:
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2'):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def encode(self, text: str, normalize_embeddings=True) -> np.ndarray:
        return self.model.encode(text, normalize_embeddings=normalize_embeddings)