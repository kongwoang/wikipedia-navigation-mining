"""Directed weighted node2vec walks + single-worker Gensim SGNS.

Second-order convention follows the reference: near(previous,next) iff next→previous.
Walks stop at dangling nodes; no invented hyperlink is added.
"""

from collections import OrderedDict
import hashlib
import time

import numpy as np
from gensim.models import Word2Vec
from gensim.models.callbacks import CallbackAny2Vec


def stable_hash(text):
    return int.from_bytes(hashlib.sha256(str(text).encode()).digest()[:8], "little")


class DirectedWalks:
    def __init__(self, matrix, p=1, q=1, seed=17, walks=3, length=20, cache_size=10000):
        if p <= 0 or q <= 0 or walks <= 0 or length <= 0:
            raise ValueError("Positive node2vec parameters required")
        self.matrix = matrix.tocsr()
        self.p, self.q, self.seed = p, q, seed
        self.walks, self.length, self.cache_size = walks, length, cache_size
        self.neighbors = [matrix.indices[matrix.indptr[i]:matrix.indptr[i+1]]
                          for i in range(matrix.shape[0])]
        self.weights = [matrix.data[matrix.indptr[i]:matrix.indptr[i+1]]
                        for i in range(matrix.shape[0])]
        self.sets = [set(row) for row in self.neighbors]

    def probabilities(self, previous, current):
        neighbors = self.neighbors[current]
        weights = self.weights[current].copy()
        if previous is not None:
            bias = np.array([1/self.p if x == previous else 1.0
                             if previous in self.sets[x] else 1/self.q for x in neighbors])
            weights *= bias
        return weights/weights.sum() if len(weights) else weights

    def __iter__(self):
        rng = np.random.default_rng(self.seed)
        cache = OrderedDict()
        n = self.matrix.shape[0]
        for _ in range(self.walks):
            for start in rng.permutation(n):
                path = [int(start)]
                while len(path) < self.length:
                    current = path[-1]
                    neighbors = self.neighbors[current]
                    if not len(neighbors):
                        break
                    previous = path[-2] if len(path)>1 and (self.p != 1 or self.q != 1) else None
                    key = previous, current
                    cumulative = cache.get(key)
                    if cumulative is None:
                        cumulative = self.probabilities(previous, current).cumsum()
                        cumulative[-1] = 1.0
                        cache[key] = cumulative
                        if len(cache)>self.cache_size:
                            cache.popitem(last=False)
                    else:
                        cache.move_to_end(key)
                    next_index = min(np.searchsorted(cumulative, rng.random()),len(neighbors)-1)
                    path.append(int(neighbors[next_index]))
                yield [str(node) for node in path]


class LossHistory(CallbackAny2Vec):
    def __init__(self):
        self.history, self.previous = [], 0.0

    def on_epoch_end(self, model):
        cumulative = float(model.get_latest_training_loss())
        self.history.append({"epoch": len(self.history)+1, "cumulative_sgns_loss": cumulative,
                             "epoch_loss_delta": cumulative-self.previous})
        self.previous = cumulative


def train_embedding(data, matrix, *, dimension=32, p=1.0, q=1.0, seed=17,
                    walks=3, length=20, window=5, epochs=5, negative=5):
    start = time.perf_counter()
    # Bounded corpus materialization avoids resampling across epochs/hidden train changes.
    corpus = list(DirectedWalks(matrix, p, q, seed, walks, length))
    callback = LossHistory()
    model = Word2Vec(vector_size=dimension, window=window, min_count=1, workers=1,
                     sg=1, negative=negative, hs=0, sample=0, seed=seed,
                     hashfxn=stable_hash, shrink_windows=False, sorted_vocab=1)
    model.build_vocab(corpus)
    model.train(corpus, total_examples=len(corpus), epochs=epochs, compute_loss=True,
                callbacks=[callback])
    vectors = np.stack([model.wv[str(i)] for i in range(len(data.ids))])
    norms = np.linalg.norm(vectors, axis=1, keepdims=True)
    normalized = np.divide(vectors, norms, out=np.zeros_like(vectors), where=norms>0)
    scores = {s: normalized[data.candidates(s)] @ normalized[s] for s in data.queries}
    info = {"seconds": time.perf_counter()-start, "walks": len(corpus),
            "tokens": sum(map(len, corpus)), "seed": seed, "dimension": dimension, "p": p, "q": q,
            "loss": callback.history, "norm_min": float(norms.min()), "norm_max": float(norms.max()),
            "workers": 1, "loss_semantics": "cumulative within one train() call; epoch deltas auxiliary SGNS loss",
            "directed_convention": "next->previous adjacency"}
    return scores, normalized, info
