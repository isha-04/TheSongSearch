import json, os
from tqdm import tqdm

THRESH = 0
ALLOWED_FAULTS = 3

def get_files_in_dataset(transcribed_dataset_path):
    files = os.listdir(transcribed_dataset_path)
    return files

def read_file(path, file_name):
    full_path = os.path.join(path, file_name)
    with open(full_path, 'r') as f:
        data = json.load(f)
    return data

def read_all_file(path, dataset_files):
    out = {}
    for file_name in dataset_files:
        full_path = os.path.join(path, file_name)
        with open(full_path, 'r') as f:
            data = json.load(f)
        out[file_name] = data
    return out

def is_same_note(ds_note, query_note, use_instrument = False):
    if ds_note['pitch'] == query_note['pitch'] and ds_note['velocity'] == query_note['velocity']:
        if use_instrument:
            if ds_note.get('instrument', '-1') == query_note.get('instrument', '-1'):
                return True
            else: 
                return False
        return True
    else:
        return False

def simple_matching_algorithm(ds_samp_notes, query_notes, allowed_faluts = 0, use_instrument = False):
    # allowed_faluts skip if missing
    num_query_notes = len(query_notes)
    num_samp_notes = len(ds_samp_notes)

    num_matches_to_check = min(num_samp_notes,num_query_notes)

    num_matching_notes = 0
    samp_idx, query_idx = 0,0

    try:
        # for ds_note, query_note in zip(ds_samp_notes, query_notes):
        while samp_idx < num_matches_to_check and query_idx < num_matches_to_check:
            ds_note, query_note = ds_samp_notes[samp_idx], query_notes[query_idx]
            if is_same_note(ds_note, query_note, use_instrument):
                num_matching_notes+=1
                query_idx +=1
                samp_idx +=1
            elif allowed_faluts > 0:
                allowed_faluts -=1 # handle additional notes
                query_idx +=1
            else:
                query_idx +=1
                samp_idx +=1
    except:
        print(samp_idx, query_idx)
    normalized_matching = num_matching_notes/num_query_notes
    return normalized_matching

def rk_hash(notes):
    pitch_list = [int(note['pitch']) for note in notes]
    velocity_list = [int(note['velocity']) for note in notes]

    return sum(pitch_list), sum(velocity_list)

def check_percent_hashing(samp_val, search_val):
    return 0.85*samp_val <= search_val <=samp_val

# smith waterman

def sliding_window_matching_algorithm(ds_samp_json, query_json):
    # print('sliding window with robin karp algorithm')
    ds_samp_notes, query_notes = ds_samp_json['notes'], query_json['notes']

    num_query_notes = len(query_notes)
    num_samp_notes = len(ds_samp_notes)
    num_sliding_windows =  num_samp_notes - num_query_notes +1
    max_matching_notes = 0

    query_hash_p, query_hash_v = rk_hash(query_notes)
    
    # print(f'number of notes in sample {len(ds_samp_notes)}')
    # print(f'number of query notes {num_query_notes}')
    # print(f'number of sliding windows {num_sliding_windows}')

    if num_sliding_windows <= 0:
        # print('no sliding window')
        max_matching_notes = simple_matching_algorithm(ds_samp_notes, query_notes, ALLOWED_FAULTS)
    else:
        for i in range(num_sliding_windows):
            window_notes = ds_samp_notes[i:i+num_query_notes]
            window_hash_p, window_hash_v = rk_hash(window_notes)

            if check_percent_hashing(query_hash_p, window_hash_p) and \
                check_percent_hashing(query_hash_v, window_hash_v):
                matching_result = simple_matching_algorithm(window_notes, query_notes, ALLOWED_FAULTS, False)
                max_matching_notes = max(max_matching_notes, matching_result)
    return max_matching_notes


def run_retrieval(transcribed_dataset_path, query_json, algo = 'simple', k = 5):
    # dataset_files = get_files_in_dataset(transcribed_dataset_path)
    # all_transcribed_json = read_all_file(transcribed_dataset_path, dataset_files)
    output = []
    for file_name in dataset_files:
        # transcribed_json = read_file(transcribed_dataset_path, file_name)
        if algo == 'simple':
            # print('simple algorithm')
            ds_samp_notes, query_notes = transcribed_json['notes'], query_json['notes']
            matching_results = simple_matching_algorithm(ds_samp_notes, query_notes)
        else:
            matching_results = sliding_window_matching_algorithm(transcribed_json, query_json)
        # if matching_results > 0:
            # print(f'{file_name} has a matching result of {matching_results}')
        # print('-'*30)
        if matching_results > THRESH:
            output.append((file_name, matching_results))
    output = sorted(output, key = lambda x: x[1], reverse= True) [:k]
    return output

def run_retrieval_multi(all_transcribed_json, query_json, algo = 'simple', k = 10):
    output = []
    for file_name, transcribed_json in all_transcribed_json.items():
        if algo == 'simple':
            # print('simple algorithm')
            ds_samp_notes, query_notes = transcribed_json['notes'], query_json['notes']
            matching_results = simple_matching_algorithm(ds_samp_notes, query_notes)
        else:
            matching_results = sliding_window_matching_algorithm(transcribed_json, query_json)
        # if matching_results > 0:
            # print(f'{file_name} has a matching result of {matching_results}')
        # print('-'*30)
        if matching_results > THRESH:
            output.append((file_name, matching_results))
    output = sorted(output, key = lambda x: x[1], reverse= True) [:k]
    return output



transcribed_dataset_path = r'dataset\wav_output\cleaned'
query_path =  r'dataset\query_output\cleaned'


dataset_files = get_files_in_dataset(transcribed_dataset_path)
all_transcribed_json = read_all_file(transcribed_dataset_path, dataset_files)

# query_file = 'query_pianosonata.json'
# query_file = 'query_furelise.json'
output_list = []
for query_file in tqdm(os.listdir(query_path)):
    query = read_file(query_path, query_file)
    if len(query['notes']) == 0:
        continue
    output = run_retrieval_multi(all_transcribed_json, query, algo = 'complex')
    output_list.append((query_file,output))
    # break

num_misses = 0
output_indexes = []
for query_file, output in output_list:
    query_file = '.'.join(query_file.split('_')[:2]) + '.json'
    print('-'*30)
    print(f'QUERY:  {query_file}')
    print(f'BEST MATCHES ARE: {output}')
    outlist = [tup[0] for tup in output]
    best_match_index = outlist.index(query_file) if query_file in outlist else -1
    print(f'CORRECT OUTPUT IN INDEX: {best_match_index}')
    output_indexes.append(best_match_index)
    if best_match_index == -1:
        num_misses +=1

from collections import Counter
print(f'NUM OF qUERIES {len(output_list)}')
print(f'NUM OF MISSES {num_misses}')
print(f'fetched index distribution {Counter(output_indexes)}')
