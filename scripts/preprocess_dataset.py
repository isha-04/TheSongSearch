# intify
# sort by start time
import os, json
from tqdm import tqdm

def read_file(full_path):
    with open(full_path, 'r') as f:
        data = json.load(f)
    return data

def write_file(full_path, data):
    with open(full_path, 'w') as f:
        json.dump(data, f)

def int_and_sorted_notes(notes):
    cleaned_notes = []
    for note in notes:
        for key,val in note.items():
            note[key] = float(val)
        cleaned_notes.append(note)
    cleaned_notes = sorted(cleaned_notes, key = lambda x: (x['start_time'], x.get('instrument',-1)))
    return cleaned_notes

def clean_json(transcribed_json):
    notes = transcribed_json['notes']
    cleaned_notes = int_and_sorted_notes(notes)
    transcribed_json['notes'] = cleaned_notes
    return transcribed_json

source_path = r'dataset\wav_output'
# source_path = r'dataset\query_output'

input_path = os.path.join(source_path, 'raw')
output_path = os.path.join(source_path, 'cleaned')

for file_name in tqdm(os.listdir(input_path)):
    out_file_path = os.path.join(output_path, file_name)
    in_file_path = os.path.join(input_path, file_name)

    transcribed_json = read_file(in_file_path)

    cleaned_transcribed_json = clean_json(transcribed_json)

    write_file(out_file_path, cleaned_transcribed_json)



