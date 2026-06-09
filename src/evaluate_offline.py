import os
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import nltk

# --- 1. Deterministic NLTK Setup ---
# Bypass macOS SSL issues if they occur
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

# Download and load CMU Pronouncing Dictionary
try:
    cmu_dict = nltk.corpus.cmudict.dict()
except LookupError:
    nltk.download('cmudict', quiet=True)
    cmu_dict = nltk.corpus.cmudict.dict()

# --- 2. Rhyme Logic ---
def get_last_word(line):
    """Extracts the final word from a line, ignoring punctuation."""
    words = re.findall(r'\b\w+\b', line.lower())
    return words[-1] if words else ""

def extract_cmu_rhyme_part(phonemes):
    """Extracts the Rime (from primary stress '1' to the end)."""
    for i, p in enumerate(phonemes):
        if '1' in p:
            return phonemes[i:]
    return phonemes

def check_rhyme(line1, line2):
    """Deterministically checks if the last words of two lines rhyme."""
    word1 = get_last_word(line1)
    word2 = get_last_word(line2)
    
    if not word1 or not word2:
        return False
    if word1 not in cmu_dict or word2 not in cmu_dict:
        return False # Fails if word is completely unknown
        
    rime1 = extract_cmu_rhyme_part(cmu_dict[word1][0])
    rime2 = extract_cmu_rhyme_part(cmu_dict[word2][0])
    
    return rime1 == rime2

def check_limerick_adherence(poem_lines):
    """
    Checks AABBA adherence on a scale of 0.0 to 1.0 based on 4 rhyme relations.
    """
    if len(poem_lines) != 5:
        return 0.0
    
    # 1. Get the rimes for all 5 lines
    rimes = []
    for line in poem_lines:
        word = get_last_word(line)
        if word not in cmu_dict:
            rimes.append(None)
        else:
            rimes.append(extract_cmu_rhyme_part(cmu_dict[word][0]))
            
    # If we couldn't parse the dictionary, return 0
    if None in rimes:
        return 0.0
    
    # 2. Define the 4 required rhyme relations
    # R1: 1-2, R2: 1-5, R3: 2-5, R4: 3-4
    relations = [
        (rimes[0] == rimes[1]), # 1-2
        (rimes[0] == rimes[4]), # 1-5
        (rimes[1] == rimes[4]), # 2-5
        (rimes[2] == rimes[3])  # 3-4
    ]
    
    # 3. Calculate score based on how many relations are True
    score = sum(relations) / 4.0
    return score

# --- 3. Offline Evaluation & File Updating ---
def load_grade_and_update():
    """
    Scans the JSON folder structure, grades them, and builds a DataFrame 
    directly from the files, bypassing the broken CSV.
    """
    data_points = []
    base_dir = "data/output/Groq_Llama3.3"
    
    for q_folder in os.listdir(base_dir):
        q_path = os.path.join(base_dir, q_folder)
        if os.path.isdir(q_path):
            questioner_count = int(q_folder.split('_')[0])
            
            for exp_file in os.listdir(q_path):
                if exp_file.endswith(".json"):
                    with open(os.path.join(q_path, exp_file), 'r') as f:
                        data = json.load(f)
                    
                    
                    # Grade the poem if not already graded
                    poem_lines = data['poems'][0].get('main_poem', [])
                    adherence = check_limerick_adherence(poem_lines)
                    data['scores']['adherence_score'] = adherence
                    
                    # Build the data point
                    data_points.append({
                        'Questioners': questioner_count,
                        'MRS': data['scores'].get('mrs', 0),
                        'WOS': data['scores'].get('wos', 0),
                        'TMS': data['scores'].get('tms', 0),
                        'Adherence': adherence
                    })
    return pd.DataFrame(data_points)

# --- 4. Plotting Generation ---
if __name__ == "__main__":
    print("Starting Offline Evaluation...")
    df = load_grade_and_update()
    
    if not df.empty:
        df = df.sort_values('Questioners')
        
        plt.figure(figsize=(10, 6))
        
        # Plot all 4 metrics
        sns.lineplot(data=df, x='Questioners', y='MRS', marker='o', label='Memory Recall Score (MRS)')
        sns.lineplot(data=df, x='Questioners', y='WOS', marker='s', label='Word Overlap Score (WOS)')
        sns.lineplot(data=df, x='Questioners', y='TMS', marker='^', label='Thread Maintenance Score (TMS)')
        sns.lineplot(data=df, x='Questioners', y='Adherence', marker='D', label='Rhyme Adherence (AABBA)')
        
        plt.title("Cognitive Degradation Analysis (Groq Llama 3.3)")
        plt.xlabel("Number of Questioners (Cognitive Load)")
        plt.ylabel("Score (0.0 to 1.0)")
        plt.legend(loc='lower left')
        plt.grid(True, linestyle='--', alpha=0.7)
        
        plt.savefig("cognitive_degradation_graph.png")
        print("Evaluation complete! Check your JSON files and 'cognitive_degradation_graph.png'.")
    else:
        print("No data found to plot.")