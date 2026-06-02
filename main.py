import os
from dotenv import load_dotenv
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.memory import MemorySaver

from src.agents import builder, config
from src.metrics import memory_recall_score, thread_maintainence_score
from src.experiment import make_questions, choose_topics, make_distractor, make_inst_for_model, test_model

load_dotenv()

if __name__ == "__main__":
    
    low = 3
    high = 25
    model_name = "Gemini_2.5_Flash"  
    itr = 5
    
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
                    
                    mrs = memory_recall_score(questioners)
                    wos = sum(q.get('word_overlapping_score', 0) for q in questioners) / len(questioners)
                    tms = thread_maintainence_score(questioners)

                    current_result = {
                        "count_of_questioners": i,
                        "iteration": j,
                        "distractors": k,
                        "memory_recall_scores": mrs,
                        "word_overlapping_score": wos,
                        "thread_maintenence_score": tms,
                    }
                    
                    df_row = pd.DataFrame([current_result])
                    header = not os.path.exists(csv_filename)
                    df_row.to_csv(csv_filename, mode='a', header=header, index=False)
                    
                    print(f"\nScores successfully saved to '{csv_filename}':")
                    print(f"  MRS: {mrs:.4f}, WOS: {wos:.4f}, TMS: {tms:.4f}")

                except Exception as e:
                    print(f"\nAn error occurred during loop execution (Qs: {i}, Iter: {j+1}). Error: {e}")
                    continue

    print("\nAll benchmarking iterations complete. Processing line plots...")
    
    try:
        # ---------------------------------------------------------
        # FORCE THE SCRIPT TO READ YOUR OLD, SUCCESSFUL DATA FILE
        # (Make sure this string exactly matches the file in your folder!)
        # ---------------------------------------------------------
        df = pd.read_csv("benchmarking_results_incremental_3_25_OpenAI_GPT4o.csv") 
        sns.set(style='whitegrid')
        
        df_with_distractors = df[df['distractors'] == 1]
        df_without_distractors = df[df['distractors'] == 0]

        plot_configs = {
            'memory_recall_scores': 'Memory Recall Score (MRS)',
            'word_overlapping_score': 'Word Overlapping Score (WOS)',
            'thread_maintenence_score': 'Thread Maintenance Score (TMS)'
        }

        for score_col, title in plot_configs.items():
            plt.figure(figsize=(12, 7))
            sns.lineplot(data=df_without_distractors, x='count_of_questioners', y=score_col, 
                         marker='o', label='Without Distractors', color='#030304', errorbar='sd')
            sns.lineplot(data=df_with_distractors, x='count_of_questioners', y=score_col, 
                         marker='X', label='With Distractors', color='#5E5E5E', errorbar='sd')
            plt.xlabel('Number of Questioners', fontsize=12)
            plt.ylabel('Average Score', fontsize=12)
            plt.title(f'{title} vs. Number of Questioners', fontsize=14, weight='bold')
            plt.ylim(0, 1.1)
            
            # Ensure the x-axis matches the data we actually have
            plt.xticks(range(int(df['count_of_questioners'].min()), int(df['count_of_questioners'].max()) + 1))
            
            plt.legend(title='Condition')
            plt.grid(True, which='both', linestyle='--', linewidth=0.5)
            plt.tight_layout()
            
            # Save the plots based on the data we plotted
            plot_filename = f"{score_col}_comparison_final_Recovered_Data.png"
            plt.savefig(plot_filename)
            print(f"Plot saved successfully to: '{plot_filename}'")
            plt.close()
            
    except Exception as e:
        print(f"An error occurred during plotting operations: {e}")