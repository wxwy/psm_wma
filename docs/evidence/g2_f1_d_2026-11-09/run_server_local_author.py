"""Server-local author classification; stdout contains aggregate/hash data only.

Inputs and per-component outputs stay on the server. Optional inbound public
reference bytes are labelled snapshots, never an installed-version assertion.
"""
import argparse
import hashlib
import json
from pathlib import Path
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from g2.io import digest, new_output, read_json, verified_file, write_json
from g2.sim.role_hypotheses import generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runtime-json', required=True)
    parser.add_argument('--catalog', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--fetch-public-reference', action='store_true')
    parser.add_argument('--public-reference-root')
    args = parser.parse_args()
    runtime = read_json(args.runtime_json); reference = read_json(args.catalog)
    protected = [args.runtime_json, args.catalog, runtime['gate'], *runtime.get('generator_roots', {}).values()]
    if args.public_reference_root:
        protected.append(args.public_reference_root)
    for layout in (1, 10):
        path = Path(runtime['gate']) / 'evidence' / ('roles_layout%d_frame0_inventory' % layout) / 'inventory.json'
        protected.extend(Path(s['path']).resolve(strict=True).parent for s in read_json(path)['sources'])
    out = new_output(args.output, protected); out.mkdir(parents=True)
    roots = dict(runtime.get('generator_roots', {})); snapshot = out / 'public_reference_snapshot'
    origins = {}; existing_matches = 0
    for key, record in reference['sources'].items():
        root = roots.get(record['root'])
        try:
            if root:
                verified_file(root, record); existing_matches += 1; origins[key] = 'EXISTING_SOURCE_BYTES_MATCH'
        except (OSError, ValueError):
            pass
    for group in {r['root'] for r in reference['sources'].values()}:
        group_records = {key: r for key, r in reference['sources'].items() if r['root'] == group}
        if all(origins.get(key) == 'EXISTING_SOURCE_BYTES_MATCH' for key in group_records):
            continue
        if args.public_reference_root:
            for key, record in group_records.items():
                verified_file(args.public_reference_root, record)
                origins[key] = 'PINNED_PUBLIC_REFERENCE_SNAPSHOT_NOT_INSTALLED_VERSION_PROOF'
            roots[group] = str(Path(args.public_reference_root).resolve(strict=True))
            continue
        if not args.fetch_public_reference:
            raise RuntimeError('matching local source roots unavailable; explicit public reference snapshot required')
        for key, record in group_records.items():
            url = 'https://raw.githubusercontent.com/' + record['repository'] + '/' + record['commit'] + '/' + record['path']
            with urllib.request.urlopen(url, timeout=30) as response:
                payload = response.read(8 * 1024 * 1024 + 1)
            if len(payload) != record['bytes'] or hashlib.sha256(payload).hexdigest() != record['sha256']:
                raise RuntimeError('public source bytes differ from fixed catalog')
            relative = Path(record['path'])
            if relative.is_absolute() or '..' in relative.parts:
                raise RuntimeError('public source path must stay within new snapshot')
            path = snapshot / relative; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(payload)
            origins[key] = 'PINNED_PUBLIC_REFERENCE_SNAPSHOT_NOT_INSTALLED_VERSION_PROOF'
        roots[group] = str(snapshot)
    verified_spans = 0
    for rule in [*reference['rules'].values(), *reference.get('non_classifying_facts', [])]:
        for span in rule.get('generator_spans', []):
            record = reference['sources'][span['source_id']]
            payload = verified_file(roots[record['root']], record).read_bytes()
            lines = payload.splitlines(keepends=True)
            start, end = span['start_line'], span['end_line']
            if (not 1 <= start <= end <= len(lines)
                or hashlib.sha256(b''.join(lines[start-1:end])).hexdigest() != span['excerpt_sha256']):
                raise RuntimeError('public reference excerpt bounds/hash differ')
            verified_spans += 1
    provenance = {'source_origins': origins, 'existing_source_matches': existing_matches,
        'verified_excerpt_spans': verified_spans, 'historical_episode_generator_version_certified': False,
        'prior_gpt_review_commit': 'ceb5dbb1a32753f275d8ed1dd54a55d8342bca9f'}
    write_json(out / 'reference_provenance.json', provenance)
    results = []
    for layout in (1, 10):
        gate = Path(runtime['gate']) / 'evidence'
        paths = [gate / ('roles_layout%d_frame%d_inventory' % (layout, frame)) / 'inventory.json' for frame in (0, 200)]
        result = generate(paths, args.catalog, out / ('layout' + str(layout)), generator_roots=roots)
        results.append(dict(result, layout=layout))
    report = {'scope': 'AUTHOR_INSTANCE_CLASSIFICATION_PENDING_GPT_NOT_INDEPENDENT_ACCEPTANCE',
        'layouts': results, 'reference_provenance_sha256': digest(out / 'reference_provenance.json'),
        'existing_generator_file_matches': existing_matches, 'private_individual_files_exported': False,
        'point_cloud_regenerated': False, 'production_code_or_roles_changed': False, 'training_ready': False}
    write_json(out / 'author_aggregate.json', report)
    print(json.dumps(report, sort_keys=True))


if __name__ == '__main__':
    main()
