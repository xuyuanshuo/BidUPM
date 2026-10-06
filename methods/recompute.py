#!/usr/bin/env python3
"""Portable exact-rule baseline and pair-metric recomputation (standard library).

Consumes explicit CSV/CSV.GZ paths. Never runs a model, tunes a threshold, changes
labels, or reranks predictions. Undefined precision/recall are written as null.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import gzip
import hashlib
import json
import math
from pathlib import Path
import re


def read_csv(path):
    opener = gzip.open if path.name.endswith('.gz') else open
    with opener(path, 'rt', encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError('CSV has no header')
        return reader.fieldnames, list(reader)


def binary(value):
    text = str(value or '').strip()
    if text in {'0', '0.0'}:
        return 0
    if text in {'1', '1.0'}:
        return 1
    return None


def text(value):
    return ' '.join(str(value or '').strip().lower().split())


def description(value):
    return ' '.join(re.sub(r'[^a-z0-9]+', ' ', str(value or '').lower().replace('&', ' and ')).split())


def exact_rule(row, args):
    qd = description(row[args.query_description])
    cd = description(row[args.candidate_description])
    qu = text(row[args.query_unit])
    cu = text(row[args.candidate_unit])
    return int(bool(qd and qu and qd == cd and qu == cu))


def count_metrics(rows):
    counts = {'tp': 0, 'fp': 0, 'fn': 0, 'tn': 0,
              'unknown_reference_rows': 0, 'unscored_prediction_rows': 0, 'input_rows': len(rows)}
    for row in rows:
        y, pred = row['_label'], row['_prediction']
        if y is None:
            counts['unknown_reference_rows'] += 1
            continue
        if pred is None:
            counts['unscored_prediction_rows'] += 1
            continue
        counts['tp' if y == pred == 1 else 'tn' if y == pred == 0 else 'fp' if pred == 1 else 'fn'] += 1
    tp, fp, fn, tn = (counts[k] for k in ('tp', 'fp', 'fn', 'tn'))
    denominator = tp + fp + fn + tn
    return {**counts,
            'evaluated_rows': denominator,
            'precision': tp / (tp + fp) if tp + fp else None,
            'recall': tp / (tp + fn) if tp + fn else None,
            'f1': 2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0,
            'accuracy': (tp + tn) / denominator if denominator else None,
            'all_included_known_reference_predictions_scored': counts['unscored_prediction_rows'] == 0}


def parse_filters(filters):
    parsed = []
    for value in filters:
        if '=' not in value:
            raise ValueError('A filter must be COLUMN=VALUE')
        parsed.append(value.split('=', 1))
    return parsed


def require_columns(header, columns):
    missing = sorted(set(columns) - set(header))
    if missing:
        raise ValueError('Missing columns: ' + ', '.join(missing))


def file_hash(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    exact = sub.add_parser('exact', help='Evaluate the normalized-description and normalized-unit exact rule')
    exact.add_argument('--data', type=Path, required=True)
    for field in ('query_description', 'candidate_description'):
        exact.add_argument('--' + field.replace('_', '-'), default=field.replace('description', 'normalized_description'))
    for field in ('query_unit', 'candidate_unit'):
        exact.add_argument('--' + field.replace('_', '-'), default=field.replace('unit', 'normalized_unit'))
    metrics = sub.add_parser('metrics', help='Recompute frozen saved-prediction or score metrics by pair ID')
    metrics.add_argument('--predictions', type=Path, required=True)
    metrics.add_argument('--gold', type=Path, required=True)
    choice = metrics.add_mutually_exclusive_group(required=True)
    choice.add_argument('--prediction-column')
    choice.add_argument('--score-column')
    metrics.add_argument('--threshold', type=float)
    metrics.add_argument('--condition-column', action='append', default=[], help='Distinguish multiple seed/policy rows for a pair; repeatable')
    for child in (exact, metrics):
        child.add_argument('--id-column', default='pair_id')
        child.add_argument('--label-column', default='final_label')
        child.add_argument('--group-column', action='append', default=[], help='Metric grouping column; repeatable')
        child.add_argument('--filter', action='append', default=[], help='Evaluate only COLUMN=VALUE; repeatable, exact text')
        child.add_argument('--reference-status', required=True, choices=('original_reference', 'construction_intent', 'AI_reference', 'user_supplied'))
        child.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('Output already exists; use a new output path to preserve earlier results')
    filters = parse_filters(args.filter)
    if args.command == 'metrics':
        # Separate saved conditions rather than pooling multiple runs as pairs.
        args.group_column = list(dict.fromkeys(args.condition_column + args.group_column))
    sources = {}
    if args.command == 'exact':
        header, rows = read_csv(args.data)
        require_columns(header, [args.id_column, args.label_column, args.query_description,
                        args.candidate_description, args.query_unit, args.candidate_unit])
        seen = set()
        for row in rows:
            pair = row[args.id_column]
            if not pair or pair in seen:
                raise ValueError('Input pair IDs must be nonempty and unique')
            seen.add(pair)
            row['_label'] = binary(row[args.label_column])
            row['_prediction'] = exact_rule(row, args)
        sources['input_sha256'] = file_hash(args.data)
    else:
        if args.score_column and (args.threshold is None or not math.isfinite(args.threshold)):
            parser.error('--score-column requires a finite frozen --threshold')
        gold_header, gold_rows = read_csv(args.gold)
        require_columns(gold_header, [args.id_column, args.label_column])
        gold = {}
        for row in gold_rows:
            pair = row[args.id_column]
            if not pair or pair in gold:
                raise ValueError('Reference pair IDs must be nonempty and unique')
            gold[pair] = row
        pred_header, predictions = read_csv(args.predictions)
        column = args.prediction_column or args.score_column
        require_columns(pred_header, [args.id_column, column] + args.condition_column)
        seen = set()
        rows = []
        header = list(set(pred_header) | set(gold_header))
        for pred in predictions:
            pair = pred[args.id_column]
            key = (pair, *(pred[k] for k in args.condition_column))
            if not pair or key in seen:
                raise ValueError('Duplicate prediction pair/condition; set --condition-column for seed/policy rows')
            seen.add(key)
            if pair not in gold:
                raise ValueError('Prediction pair ID is absent from supplied reference')
            row = {**gold[pair], **pred}
            row['_label'] = binary(gold[pair][args.label_column])
            if args.prediction_column:
                row['_prediction'] = binary(pred[column])
            else:
                try:
                    score = float(pred[column])
                except ValueError:
                    score = float('nan')
                row['_prediction'] = int(score >= args.threshold) if math.isfinite(score) else None
            rows.append(row)
        sources = {'gold_sha256': file_hash(args.gold), 'predictions_sha256': file_hash(args.predictions),
                   'reference_rows': len(gold), 'prediction_rows': len(predictions),
                   'unique_prediction_pair_ids': len({row[args.id_column] for row in predictions}),
                   'reference_pairs_absent_from_predictions': len(set(gold) - {row[args.id_column] for row in predictions})}
    require_columns(header, args.group_column + [k for k, _ in filters])
    rows = [row for row in rows if all(row[k] == value for k, value in filters)]
    if not rows:
        raise ValueError('No rows remain after filtering')
    groups = defaultdict(list)
    for row in rows:
        key = tuple(row[k] for k in args.group_column)
        groups[key].append(row)
    result = {'schema': 'bidupm-portable-pair-metrics-v1', 'command': args.command,
              'reference_status': args.reference_status, 'sources': sources,
              'group_columns': args.group_column, 'filters': dict(filters),
              'threshold': getattr(args, 'threshold', None),
              'groups': [{**dict(zip(args.group_column, key)), **count_metrics(value)} for key, value in sorted(groups.items())],
              'limitations': ['Pair metrics only; no threshold tuning, model execution or Top3 reranking.',
                             'Unknown reference labels and unscored predictions are counted separately; incomplete predictions do not establish full candidate recall.',
                             'Reference status is user-declared and is never converted into human gold by this program.',
                             'The exact rule uses supplied normalized units without inventing alias conversion.']}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    print(json.dumps({'output': str(args.output), 'evaluated_groups': len(result['groups'])}))


if __name__ == '__main__':
    main()
