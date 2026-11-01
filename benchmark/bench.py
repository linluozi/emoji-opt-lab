#!/usr/bin/env python3
"""Benchmark emoji.demojize baseline vs optimized.

Usage:
  python bench.py <src_path> <impl_label> <scale> <out_json>

Imports the `emoji` package from src_path (an absolute/relative path whose
parent is on sys.path) and times demojize over warmup + timed samples.
"""
import json
import os
import random
import statistics
import sys
import time

SRC_PATH = sys.argv[1] if len(sys.argv) > 1 else '.'
IMPL = sys.argv[2] if len(sys.argv) > 2 else 'baseline'
SCALE = sys.argv[3] if len(sys.argv) > 3 else 'small'
OUT = sys.argv[4] if len(sys.argv) > 4 else 'raw/x.json'

SEED = 12345

random.seed(SEED)

# Build deterministic realistic input per scale
WORDS = (
    'Hello world this is a test string with some punctuation, '
    'and numbers 123. The quick brown fox jumps over the lazy dog. '
    'Streams of ordinary text with :) and having emoji: '
)
EMOJIS = ['😀', '🚀', '👍', '❤️', '👨\u200d👩\u200d👧', '🎉', '🔥', '😍', '🌍', '💡']

def build_text(scale: str) -> str:
    n = {'small': 3000, 'medium': 8000, 'large': 18000}[scale]
    parts = []
    total = 0
    while total < n:
        base = WORDS if random.random() < 0.7 else ''
        parts.append(base)
        total += len(base)
        if random.random() < 0.45:
            e = random.choice(EMOJIS)
            parts.append(e)
            total += len(e)
    return ''.join(parts)

def run(text: str, reps: int):
    # warmup
    for _ in range(3):
        emoji.demojize(text)
    samples = []
    for _ in range(reps):
        t0 = time.perf_counter()
        emoji.demojize(text)
        t1 = time.perf_counter()
        samples.append(t1 - t0)
    return samples

if __name__ == '__main__':
    sys.path.insert(0, SRC_PATH)
    import emoji  # noqa: E402
    sys_path_abs = os.path.abspath(SRC_PATH)
    text = build_text(SCALE)
    samples = run(text, 7)
    stats = {
        'impl': IMPL,
        'scale': SCALE,
        'seed': SEED,
        'text_len': len(text),
        'samples_ms': [round(s * 1e3, 4) for s in samples],
        'median_ms': round(statistics.median(samples) * 1e3, 4),
        'p25_ms': round(sorted(samples)[1] * 1e3, 4),
        'p75_ms': round(sorted(samples)[len(samples) - 2] * 1e3, 4),
    }
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(stats, f, indent=2)
    print(json.dumps(stats))