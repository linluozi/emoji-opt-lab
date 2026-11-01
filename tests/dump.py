#!/usr/bin/env python3
"""Dump outputs for all differential inputs from one emoji source tree.

Usage: python dump.py <src_path> <out_jsonl>
Emits one JSON line per input describing all compared outputs.
"""
import importlib
import json
import os
import random
import sys
import unicodedata

SRC = os.path.abspath(sys.argv[1])
OUT = sys.argv[2]

sys.path.insert(0, SRC)
# Also allow SRC/.. in case emoji package is a subdirectory of SRC
sys.path.insert(0, os.path.dirname(SRC))
import emoji  # noqa: E402

SYS = ['', 'a', 'Z', '1', '\u0000', '\n', ' ', '🦷', '👍', '😀',
       'a\U0001f309b', '👨\u200d👩\u200d👧', '\u200d🦷\u200d🦷',
       'a\U0001f468\U0000200d\U0001f467b', '\U0001f477\U0001f3fb\U0000200d\U00002640',
       '.', '...', '\ufe0f', '\ufe0e', '❌', '✓', 'ǅ']


def make_inputs():
    rng = random.Random(20261101)
    inputs = list(SYS)
    pool = list('abcXYZ .,\'"!?\U0001f600\U0001f601🏃🏽‍♀️\u200d\u00e9\u00fc\u4e2d\ufe0f')
    for _ in range(2000):
        n = rng.randint(0, 300)
        inputs.append(''.join(rng.choice(pool) for _ in range(n)))
    inputs.append('Hello 😀 world 🚀 test 👍 with "code": ~!@#\u00e9\u4e2d👍' * 120)
    inputs.append('👨\u200d👩\u200d👧' * 400)
    inputs.append('a' * 5000)
    inputs.append('z' * 5000 + '😀' + 'y' * 5000)
    inputs.append('\uffff' * 50)
    inputs.append(unicodedata.normalize('NFKC', 'ǅ'))
    return inputs


def ser(v):
    if isinstance(v, str):
        return v
    return json.dumps(v, default=str)


def outputs(s):
    res = {}
    def tryf(label, fn):
        try:
            res[label] = ('ok', ser(fn()))
        except Exception as e:  # noqa
            res[label] = ('err', type(e).__name__ + ':' + str(e))
    tryf('demojize_en', lambda: emoji.demojize(s, language='en'))
    tryf('demojize_alias', lambda: emoji.demojize(s, language='alias'))
    tryf('tokenize_t', lambda: [t.chars + '|' + str(t.value) for t in emoji.tokenize(s, True)])
    tryf('tokenize_f', lambda: [t.chars + '|' + str(t.value) for t in emoji.tokenize(s, False)])
    tryf('analyze', lambda: [str(t) for t in emoji.analyze(s, non_emoji=True, join_emoji=True)])
    tryf('emoji_list', lambda: emoji.emoji_list(s))
    return res


with open(OUT, 'w') as f:
    for s in make_inputs():
        f.write(json.dumps({'input': s, 'outs': outputs(s)}) + '\n')
print('wrote', OUT)