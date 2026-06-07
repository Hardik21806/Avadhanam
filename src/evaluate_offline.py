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
    Checks if a 5-line poem adheres strictly to the AABBA scheme.
    Returns 1.0 for perfect, 0.0 for failed.
    """
    if len(poem_lines) != 5:
        return 0.0
    
    is_aab = (check_rhyme(poem_lines[0], poem_lines[1]) and 
              check_rhyme(poem_lines[0], poem_lines[4]))
    is_bb = check_rhyme(poem_lines[2], poem_lines[3])
    
    return 1.0 if (is_aab and is_bb) else 0.0

# --- 3. Offline Evaluation & File Updating ---
def load_grade_and_update():
    """
    Scans all JSONs, calculates Adherence, saves it BACK into the JSON,
    and returns a DataFrame of the aggregated results.
    """
    data_points = []
    base_dir = "data/output/Groq_Llama3.3" # Update this to match your model folder
    
    if not os.path.exists(base_dir):
        print(f"Directory not found: {base_dir}")
        return pd.DataFrame()

    for q_folder in os.listdir(base_dir):
        q_path = os.path.join(base_dir, q_folder)
        if os.path.isdir(q_path):
            questioner_count = int(q_folder.split('_')[0])
            
            mrs_scores = []
            wos_scores = []
            tms_scores = []
            adherence_scores = []
            
            for exp_file in os.listdir(q_path):
                if exp_file.endswith(".json"):
                    file_path = os.path.join(q_path, exp_file)
                    
                    # 1. Open the JSON
                    with open(file_path, 'r') as f:
                        data = json.load(f)
                    
                    # 2. Extract the poem and calculate adherence
                    # Assuming the structure is data['poems'][0]['main_poem']
                    if 'poems' in data and len(data['poems']) > 0:
                        poem_lines = data['poems'][0].get('main_poem', [])
                        adherence = check_limerick_adherence(poem_lines)
                        
                        # 3. Update the JSON data object
                        if 'scores' not in data:
                            data['scores'] = {} # Ensure scores block exists
                        data['scores']['adherence_score'] = adherence
                        
                        # 4. Save the JSON file BACK to the disk (Self-Grading)
                        with open(file_path, 'w') as f:
                            json.dump(data, f, indent=4)
                            
                        # 5. Append to our local lists for plotting
                        mrs_scores.append(data['scores'].get('mrs', 0))
                        wos_scores.append(data['scores'].get('wos', 0))
                        tms_scores.append(data['scores'].get('tms', 0))
                        adherence_scores.append(adherence)
            
            # Aggregate averages for this questioner count
            if len(mrs_scores) > 0:
                data_points.append({
                    'Questioners': questioner_count,
                    'MRS': sum(mrs_scores) / len(mrs_scores),
                    'WOS': sum(wos_scores) / len(wos_scores),
                    'TMS': sum(tms_scores) / len(tms_scores),
                    'Adherence': sum(adherence_scores) / len(adherence_scores)
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