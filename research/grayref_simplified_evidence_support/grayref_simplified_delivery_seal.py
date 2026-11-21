"""Verify supplemental delivery and archive its source without changing core seals."""
import argparse
import collections
import json
import re
import shutil
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

from grayref_simplified_evidence_v0.common import GROUPS, ROOT, get, put, sha, utc, write_bytes
from grayref_simplified_evidence_v0.run_all import check_sources


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.targets = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key in ('href', 'src') and value:
                self.targets.append(value)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--run', required=True)
    run = Path(parser.parse_args().run).resolve()
    check_sources(run)
    core = get(run / 'completion_seal.json')
    for key, filename in [('source_hashes_sha', 'source_hashes.json'),
                          ('run_integrity_sha', 'run_integrity.json'),
                          ('decision_sha', 'decision_result.json'),
                          ('full_gallery_index_sha', 'galleries/index.html')]:
        assert sha(run / filename) == core[key], filename
    for name, digest in core['report_hashes'].items():
        assert sha(run / 'reports' / name) == digest
    for folder in ['stage_diagnostics', 'containment_diagnostics', 'mechanism_diagnostics']:
        assert (run / folder / 'seal.json').is_file(), folder
    assert get(run / 'run_integrity.json')['processed'] == 2647
    assert get(run / 'offline_label_overlays' / 'integrity.json')['overlays'] == 120
    assert get(run / 'full_resolution_png_numeric_check.json')['frames'] == 2647
    groups = {}
    for group, count in GROUPS.items():
        qa = get(run / 'videos' / (group + '_qa.json'))
        assert qa['frames'] == count and qa['full_decode']
        assert sha(run / 'videos' / (group + '.mp4')) == qa['sha256']
        groups[group] = count
    assert (run / 'videos/index.html').is_file()
    for group, count in GROUPS.items():
        text = (run / 'galleries' / group / 'index.html').read_text(encoding='utf-8')
        entries = json.loads(re.search(r'const data=(.*?);function show', text).group(1))
        modes = collections.Counter(row['mode'] for row in entries)
        assert len(modes) == 9 and set(modes.values()) == {count}
        assert len({row['frame'] for row in entries}) == count
        for row in entries:
            assert (run / 'galleries' / group / str(row['frame']) / 'index.html').is_file()
    # Resolve every actual HTML reference, including image/video sources and group navigation.
    counts = collections.Counter()
    for folder in ['galleries', 'videos', 'offline_label_overlays']:
        for page in (run / folder).rglob('*.html'):
            links = Links()
            links.feed(page.read_text(encoding='utf-8'))
            counts['html_pages'] += 1
            for value in links.targets:
                target = urlsplit(value)
                if target.scheme or target.netloc or not target.path:
                    continue
                local = (page.parent / unquote(target.path)).resolve()
                assert local.is_file(), (page, value)
                counts['local_links'] += 1
    source = Path(__file__).parent
    source_hashes = {}
    for file in source.iterdir():
        if file.is_file() and file.suffix in ['.py', '.ps1', '.md']:
            write_bytes(run / 'support_source_snapshot' / file.name, file.read_bytes())
            source_hashes[file.name] = sha(file)
    files = []
    for folder in ['stage_diagnostics', 'containment_diagnostics', 'mechanism_diagnostics',
                   'supplementary_controls', 'offline_label_overlays', 'videos',
                   'support_source_snapshot']:
        files.extend(p for p in (run / folder).rglob('*') if p.is_file())
    for filename in ['FINAL_FINDINGS.md', 'MANUAL_VISUAL_REVIEW.md',
                     'point_source_independent_verification.json',
                     'point_source_independent_verification.csv',
                     'real_repeat_determinism.json', 'label_image_identity_check.json',
                     'full_resolution_png_numeric_check.json']:
        file = run / filename
        assert file.is_file(), filename
        files.append(file)
    frozen = datetime.fromisoformat(get(run / 'source_hashes.json')['utc'])
    finished = datetime.now(timezone.utc)
    artifacts = [p for p in run.rglob('*') if p.is_file()]
    cost = dict(source_freeze_utc=frozen.isoformat(),delivery_audit_utc=finished.isoformat(),
                elapsed_freeze_to_delivery_seconds=(finished-frozen).total_seconds(),
                elapsed_scope='Includes inference, rendering, offline scoring, QA and supplemental audits; excludes preflight/setup; not detector latency',
                run_bytes_before_final_seal=sum(p.stat().st_size for p in artifacts),
                run_files_before_final_seal=len(artifacts),disk_free_bytes=shutil.disk_usage(run).free,
                environment=get(run/'environment.json'))
    put(run / 'delivery_cost.json', cost)
    files.append(run / 'delivery_cost.json')
    seal = dict(utc=utc(),core_completion_sha=sha(run/'completion_seal.json'),
                support_source_hashes=source_hashes,video_groups=groups,
                video_frames=sum(groups.values()),offline_label_views=120,
                html_check=dict(counts),source_unchanged=True,
                files={str(p.relative_to(run)).replace('\\','/'):sha(p) for p in files})
    put(run / 'supplemental_delivery_seal.json', seal)
    print(dict(video_frames=2647,offline_label_views=120,**counts,files=len(files)),flush=True)


if __name__ == '__main__':
    main()
