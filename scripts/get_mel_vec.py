import librosa,os
import numpy as np
import torch
import torch.nn.functional as F
from scipy import spatial
from tqdm import tqdm


from sklearn.metrics.pairwise import cosine_similarity

def load_mel_spec(filename, n_mels=40, n_frames = 80, n_fft = 128, hop_length = 128):
    # load audio data
    y, sample_rate = librosa.load(filename, mono=True)
    # calc mel-spectrogram
    S = librosa.feature.melspectrogram(y = y, sr = sample_rate, n_mels=n_mels, n_fft = n_fft, hop_length=hop_length, fmax = 8000)  
    # convert to Decibel
    S = librosa.power_to_db(S, ref = np.max)
    # take a sample from 
    center_frame_idx = S.shape[1] / 2
    offset           = int(center_frame_idx - n_frames / 2)
    
    return S[:,offset:(offset+n_frames)].flatten()

dataset_features = []
dataset_file = []
data_dir = 'dataset\wav_files\wav_files'
for file_pth in os.listdir(data_dir):
    if not file_pth.endswith('.wav'):
        continue
    
    file_pth = os.path.join(data_dir, file_pth)
    feature = load_mel_spec(file_pth)
    dataset_features.append(feature)
    file_pth = file_pth.split('\\')[-1]
    dataset_file.append(file_pth)

queries = []
query_dir = 'dataset\queries\queries'
for file_pth in os.listdir(query_dir):
    if not file_pth.endswith('.wav'):
        continue

    file_pth = os.path.join(query_dir, file_pth)
    feature = load_mel_spec(file_pth)
    file_pth = file_pth.split('\\')[-1]
    queries.append((feature,file_pth))

# print(dataset_features)
# print(queries)
results = []
n = 5
num_misses = 0
output_indexes = []
num_of_queries = 0
# dataset_features = torch.Tensor(dataset_features)

for q_feature, query_file in queries:
    if q_feature.shape[0] != 3200:
        continue
    num_of_queries += 1
    query_file = '.'.join(query_file.split('_')[:2])+'.wav'
    print(f'QUERY:  {query_file}')
    similarities = []
    for dataset_feature in dataset_features:
        # sim = cosine_similarity(dataset_feature , q_feature)
        sim = 1 - spatial.distance.cosine(dataset_feature , q_feature)
        similarities.append(sim)
    # print(similarities)
    top5_best = np.array(similarities).argsort()[::-1][:n]
    output = [(dataset_file[i], similarities[i]) for i in top5_best]
    print(f'BEST MATCHES ARE: {output}')
    outlist = [tup[0] for tup in output]
    best_match_index = outlist.index(query_file) if query_file in outlist else -1
    print(f'CORRECT OUTPUT IN INDEX: {best_match_index}')
    output_indexes.append(best_match_index)
    if best_match_index == -1:
        num_misses +=1
    print('-'*30)
    # break

from collections import Counter
# print(f'NUM OF qUERIES {num_of_queries}')
# print(f'NUM OF MATCHES {num_of_queries - num_misses}')
# print(f'NUM OF MISSES {num_misses}')
print(f'Fetch results {(num_of_queries - num_misses)*100/num_of_queries}')
# print(f'fetched index distribution {Counter(output_indexes)}')
