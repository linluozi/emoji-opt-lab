#!/usr/bin/env python3
"""Differential test: baseline vs optimized emoji.toke tokenize/demojize.

Compares byte-for-byte equality of outputs across >=2000 random + boundary
inputs (empty, single char, extreme, non-ASCII, None/NaN-ish, long input).
Runs both the public demojize()/emojize() round trip and the raw tokenize()
token stream, asserting 0 differences.
"""
import importlib
import json
import os
import random
import subprocess
import sys
import unicodedata

BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'base'))
OPT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'emoji'))
DUMP = os.path.join(os.path.dirname(__file__), 'dump.py')
WORK = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'benchmark', 'raw'))

SYS_INPUTS = ['', 'a', 'Z', '1', '\u0000', '\n', ' ', '🦷', '👍', '😀',
              'a\U0001f309b', '👨\u200d👩\u200d👧', '\u200d🦷\u200d🦷',
              'a\U0001f468\U0000200d\U0001f467b', '\U0001f477\U0001f3fb\U0000200d\U00002640',
              '.', '...', '\ufe0f', '\ufe0e', '❌', '✓', 'ǅ']


def make_inputs():
    rng = random.Random(20261101)
    inputs = list(SYS_INPUTS)
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


def main():
    bfile = os.path.join(WORK, 'diff_base.jsonl')
    ofile = os.path.join(WORK, 'diff_opt.jsonl')
    for src, out in ((BASE, bfile), (OPT, ofile)):
        subprocess.run([sys.executable, DUMP, src, out], check=True)

    bd = {}
    with open(bfile) as f:
        for line in f:
            rec = json.loads(line)
            bd[rec['input']] = rec['outs']
    diffs = 0
    total = 0
    detail = []
    with open(ofile) as f:
        for line in f:
            rec = json.loads(line)
            total += 1
            b = bd.get(rec['input'])
            if b != rec['outs']:
                diffs += 1
                if len(detail) < 10:
                    detail.append((rec['input'][:50], b, rec['outs']))
    print(f'total={total} diffs={diffs}')
    for dg in detail:
        print('DIFF', dg)
    result = {'total_cases': total, 'differences': diffs, 'byte_exact': diffs == 0}
    with open(os.path.join(os.path.dirname(__file__), '..', 'results_diff.json'), 'w') as f:
        json.dump(result, f, indent=2)
    print(json.dumps(result))
    sys.exit(0 if diffs == 0 else 1)


if __name__ == '__main__':
    main()