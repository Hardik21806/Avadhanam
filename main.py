import os
import json
import re
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

import nltk

# --- NLTK RHYME CHECKER SETUP ---
import ssl
try:
    _create_unverified_https_context = ssl._create_unverified_context
except AttributeError:
    pass
else:
    ssl._create_default_https_context = _create_unverified_https_context

try:
    cmu_dict = nltk.corpus.cmudict.dict()
except LookupError:
    nltk.download('cmudict', quiet=True)
    cmu_dict = nltk.corpus.cmudict.dict()

def get_last_word(line):
    words = re.findall(r'\b\w+\b', line.lower())
    return words[-1] if words else ""

def extract_cmu_rhyme_part(phonemes):
    for i, p in enumerate(phonemes):
        if '1' in p: return phonemes[i:]
    return phonemes

def check_rhyme(line1, line2):
    word1, word2 = get_last_word(line1), get_last_word(line2)
    if not word1 or not word2: return False
    if word1 not in cmu_dict or word2 not in cmu_dict: return False
    return extract_cmu_rhyme_part(cmu_dict[word1][0]) == extract_cmu_rhyme_part(cmu_dict[word2][0])

def check_limerick_adherence(poem_lines):
    """Checks strict AABBA adherence. Returns 1.0 or 0.0."""
    if len(poem_lines) != 5: return 0.0
    is_aab = (check_rhyme(poem_lines[0], poem_lines[1]) and check_rhyme(poem_lines[0], poem_lines[4]))
    is_bb = check_rhyme(poem_lines[2], poem_lines[3])
    return 1.0 if (is_aab and is_bb) else 0.0
# --------------------------------

from src.agents import builder, config
from src.metrics import memory_recall_score, thread_maintainence_score
from src.experiment import make_questions, choose_topics, make_distractor, make_inst_for_model, test_model

load_dotenv()

if __name__ == "__main__":
    
    low = 3
    high = 3
    model_name = "Groq_Llama3.3"  
    itr = 1
    
    # Dynamically define the filename
    csv_filename = f"benchmarking_results_incremental_{low}_{high}_{model_name}.csv"

    for i in range(low, high + 1):
        for j in range(itr):
            for k in range(2):
                print(f"\n{'='*20} STARTING TEST {'='*20}\nConfig: {i} Qs, Iteration {j+1}, Distractors: {'Yes' if k else 'No'}\n")
                
                try:
                    questioners = make_questions(i)
                    choose_topics(questioners)
                    distractors_instance = make_distractor() if k else None
                    
                    model = {'memory': MemorySaver(), 'graph': builder.compile(checkpointer=MemorySaver())}
                    model["graph"].invoke({"messages": [HumanMessage(content=make_inst_for_model(questioners))]}, config)
                    
                    test_model(questioners, distractors_instance, model)
                    
                    # 1. Calculate Standard Metrics
                    mrs = memory_recall_score(questioners)
                    wos = sum(q.get('word_overlapping_score', 0) for q in questioners) / len(questioners)
                    tms = thread_maintainence_score(questioners)

                    # 2.  Calculate Adherence Score
                    adherence_scores = []
                    for q in questioners:
                        poem_lines = q['poem'].strip().split('\n')
                        score = check_limerick_adherence(poem_lines)
                        adherence_scores.append(score)
                    
                    avg_adherence = sum(adherence_scores) / len(adherence_scores) if adherence_scores else 0.0

                    # 3. Compile the structured dictionary
                    experiment_data = {
                        "metadata": {
                            "Model": model_name,
                            "Questioners": i,
                            "Iteration": j + 1,
                            "Distractors": "Yes" if k else "No"
                        },
                        "poems": [],
                        "scores": {
                            "mrs": mrs,
                            "wos": wos,
                            "tms": tms,
                            "adherence_score": avg_adherence  
                        }
                    }

                    for q in questioners:
                        poem_data = {
                            "id": q['id'],
                            "topic": q['topic'],
                            "main_poem": q['poem'].strip().split('\n'),
                            "recall_poem": q['recall_poem'].strip().split('\n')
                        }
                        experiment_data["poems"].append(poem_data)

                    # 4. Save using the utility
                    from src.utils import save_experiment_json
                    save_experiment_json(model_name, i, experiment_data)
                    
                    current_result = {
                        "count_of_questioners": i,
                        "iteration": j,
                        "distractors": k,
                        "memory_recall_scores": mrs,
                        "word_overlapping_score": wos,
                        "thread_maintenence_score": tms,
                        "adherence_score": avg_adherence 
                    }
                    
                    df_row = pd.DataFrame([current_result])
                    header = not os.path.exists(csv_filename)
                    df_row.to_csv(csv_filename, mode='a', header=header, index=False)
                    
                    print(f"\nScores successfully saved to '{csv_filename}':")
                    print(f"  MRS: {mrs:.4f}, WOS: {wos:.4f}, TMS: {tms:.4f}, Adherence: {avg_adherence:.4f}")

                except Exception as e:
                     print(f"\nAn error occurred during loop execution (Qs: {i}, Iter: {j+1}). Error: {e}")
                     continue

    print("\nAll benchmarking iterations complete. Processing line plots...")

    try:
        # Load the newly created CSV
        df = pd.read_csv(csv_filename) 
        sns.set_theme(style='whitegrid') # Updated from sns.set to sns.set_theme
        
        df_with_distractors = df[df['distractors'] == 1]
        df_without_distractors = df[df['distractors'] == 0]

        # 5.  Added adherence_score to the plots
        plot_configs = {
            'memory_recall_scores': 'Memory Recall Score (MRS)',
            'word_overlapping_score': 'Word Overlapping Score (WOS)',
            'thread_maintenence_score': 'Thread Maintenance Score (TMS)',
            'adherence_score': 'Rhyme Adherence (AABBA)'
        }

        for score_col, title in plot_configs.items():
            plt.figure(figsize=(12, 7))
            sns.lineplot(data=df_without_distractors, x='count_of_questioners', y=score_col, 
                         marker='o', label='Without Distractors', color='#030304')
            sns.lineplot(data=df_with_distractors, x='count_of_questioners', y=score_col, 
                         marker='X', label='With Distractors', color='#5E5E5E')
            plt.xlabel('Number of Questioners', fontsize=12)
            plt.ylabel('Average Score', fontsize=12)
            plt.title(f'{title} vs. Number of Questioners', fontsize=14, weight='bold')
            plt.ylim(-0.1, 1.1) # Adjusted slightly so 0.0 doesn't get cut off
            
            plt.xticks(range(int(df['count_of_questioners'].min()), int(df['count_of_questioners'].max()) + 1))
            
            plt.legend(title='Condition')
            plt.grid(True, which='both', linestyle='--', linewidth=0.5)
            plt.tight_layout()
            
            plot_filename = f"{score_col}_comparison.png"
            plt.savefig(plot_filename)
            print(f"Plot saved successfully to: '{plot_filename}'")
            plt.close()
            
    except Exception as e:
        print(f"An error occurred during plotting operations: {e}")