import json
import os

mp3_json_path = os.path.join(os.path.dirname(__file__), '../gen/mp3_duration_scan_output.json')
hymns_json_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../cifras-ccb/data/Hymns.json'))

with open(mp3_json_path, 'r', encoding='utf-8') as f:
    mp3_data = json.load(f)

with open(hymns_json_path, 'r', encoding='utf-8') as f:
    hymns = json.load(f)

hymns_by_code = {h.get('code'): h for h in hymns if 'code' in h}

for mp3 in mp3_data:
    filename = mp3.get('filename')
    if not filename or not filename.endswith('.mp3'):
        continue
    code = filename.split('.')[0]
    hymn = hymns_by_code.get(code)
    if hymn is not None:
        if 'time' not in hymn or not isinstance(hymn['time'], dict):
            hymn['time'] = {}
        if 'duration_sec' in mp3:
            hymn['time']['duration'] = mp3['duration_sec']
        if 'intro_duration_sec' in mp3:
            hymn['time']['introDuration'] = mp3['intro_duration_sec']

with open(hymns_json_path, 'w', encoding='utf-8') as f:
    json.dump(hymns, f, ensure_ascii=False, indent=2)

print('Hymns.json updated with durations.')
