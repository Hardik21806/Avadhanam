import os
import json
import re
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import nltk
import ssl
from pathlib import Path

# --- NLTK SETUP ---
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


def _get_last_word(line):
    """Extracts the final word from a line, ignoring punctuation."""
    words = re.findall(r'\b\w+\b', line.lower())
    return words[-1] if words else ""


def _extract_cmu_rhyme_part(phonemes):
    """Extracts the Rime (from primary stress '1' to the end)."""
    for i, p in enumerate(phonemes):
        if '1' in p:
            return phonemes[i:]
    return phonemes


def _check_rhyme(line1, line2):
    """Deterministically checks if the last words of two lines rhyme."""
    word1 = _get_last_word(line1)
    word2 = _get_last_word(line2)
    
    if not word1 or not word2:
        return False
    if word1 not in cmu_dict or word2 not in cmu_dict:
        return False
    
    rime1 = _extract_cmu_rhyme_part(cmu_dict[word1][0])
    rime2 = _extract_cmu_rhyme_part(cmu_dict[word2][0])
    
    return rime1 == rime2


def _check_limerick_adherence(poem_lines):
    """
    Checks AABBA adherence on a scale of 0.0 to 1.0 based on 4 rhyme relations.
    """
    if len(poem_lines) != 5:
        return 0.0
    
    # Get the rimes for all 5 lines
    rimes = []
    for line in poem_lines:
        word = _get_last_word(line)
        if word not in cmu_dict:
            rimes.append(None)
        else:
            rimes.append(_extract_cmu_rhyme_part(cmu_dict[word][0]))
    
    # If we couldn't parse the dictionary, return 0
    if None in rimes:
        return 0.0
    
    # Define the 4 required rhyme relations
    # R1: 1-2, R2: 1-5, R3: 2-5, R4: 3-4
    relations = [
        (rimes[0] == rimes[1]),  # 1-2
        (rimes[0] == rimes[4]),  # 1-5
        (rimes[1] == rimes[4]),  # 2-5
        (rimes[2] == rimes[3])   # 3-4
    ]
    
    # Calculate score based on how many relations are True
    score = sum(relations) / 4.0
    return score


def parse_directory_name(dir_name):
    """
    Parse directory name like '3_questioners_2' and extract:
    - questioner_count: 3
    - iteration: 2
    
    Returns: (questioner_count, iteration) or (None, None) if invalid
    """
    pattern = r'^(\d+)_questioners_(\d+)$'
    match = re.match(pattern, dir_name)
    if match:
        return int(match.group(1)), int(match.group(2))
    return None, None


def scan_experiments_directory(model_path):
    """
    Scans the model directory for experiment JSON files in both with_distractor and without_distractor folders.
    
    Each JSON file is named: <questioner_count>_questioners_<iteration>.json
    
    Returns:
    {
        "with_distractor": {
            "3": {  # questioner count as string
                "1": "/path/to/3_questioners_1.json",
                "2": "/path/to/3_questioners_2.json"
            },
            "4": { ... }
        },
        "without_distractor": {
            "3": { ... },
            "4": { ... }
        }
    }
    """
    experiments = {"with_distractor": {}, "without_distractor": {}}
    
    if not os.path.isdir(model_path):
        raise ValueError(f"Model path does not exist: {model_path}")
    
    # Pattern to match: <questioner_count>_questioners_<iteration>.json
    pattern = r'^(\d+)_questioners_(\d+)\.json$'
    
    # Scan both distractor subfolders
    for distractor_folder in ["with_distractor", "without_distractor"]:
        distractor_path = os.path.join(model_path, distractor_folder)
        
        if not os.path.isdir(distractor_path):
            continue
        
        for filename in os.listdir(distractor_path):
            filepath = os.path.join(distractor_path, filename)
            
            # Only process JSON files, skip directories
            if not filename.endswith('.json') or os.path.isdir(filepath):
                continue
            
            match = re.match(pattern, filename)
            if not match:
                continue
            
            q_count = int(match.group(1))
            iteration = int(match.group(2))
            
            q_count_str = str(q_count)
            iter_str = str(iteration)
            
            if q_count_str not in experiments[distractor_folder]:
                experiments[distractor_folder][q_count_str] = {}
            
            experiments[distractor_folder][q_count_str][iter_str] = filepath
    
    return experiments


def find_max_common_iterations(experiments_by_distractor):
    """
    Given experiments dict with distractor configuration, find the maximum iteration count
    that exists for ALL questioner counts within each distractor configuration.
    
    Args:
        experiments_by_distractor: {"with_distractor": {...}, "without_distractor": {...}}
    
    Returns:
        {"with_distractor": max_iters, "without_distractor": max_iters}
    """
    result = {}
    
    for distractor_config, experiments in experiments_by_distractor.items():
        if not experiments:
            result[distractor_config] = 0
            continue
        
        max_iter_per_count = {}
        for q_count, iterations in experiments.items():
            if iterations:
                max_iter_per_count[q_count] = max(int(i) for i in iterations.keys())
        
        result[distractor_config] = min(max_iter_per_count.values()) if max_iter_per_count else 0
    
    return result


def load_experiment_json(json_path):
    """Load and parse a single experiment JSON file."""
    with open(json_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def calculate_scores_from_experiment(exp_data):
    """
    Extract scores from experiment data.
    Returns: (mrs, wos, tms, adherence_score)
    """
    scores = exp_data.get('scores', {})
    return (
        scores.get('mrs', 0.0),
        scores.get('wos', 0.0),
        scores.get('tms', 0.0),
        scores.get('adherence_score', 0.0)
    )


def evaluate_model(model_path):
    """
    Main evaluation function:
    1. Scans directory for experiments in both with_distractor and without_distractor folders
    2. Finds max common iteration across all questioner counts for each configuration
    3. Generates separate CSV files for each configuration
    4. Saves CSVs to model_path/evaluation_results_with_distractor.csv and evaluation_results_without_distractor.csv
    5. Generates separate plots for each configuration
    
    Args:
        model_path: Path to model output directory (e.g., data/output/Groq_Llama3.3)
    """
    print(f"\n{'='*60}")
    print(f"EVALUATION: {model_path}")
    print(f"{'='*60}\n")
    
    # Scan experiments
    experiments_by_distractor = scan_experiments_directory(model_path)
    
    # Check if any experiments found
    has_experiments = any(
        experiments_by_distractor[config] 
        for config in experiments_by_distractor
    )
    
    if not has_experiments:
        print("No experiments found in the directory.")
        return
    
    # Find max common iterations for each configuration
    max_common_iters = find_max_common_iterations(experiments_by_distractor)
    
    # Process each distractor configuration
    for distractor_config in ["with_distractor", "without_distractor"]:
        experiments = experiments_by_distractor[distractor_config]
        max_common_iter = max_common_iters[distractor_config]
        
        if not experiments or max_common_iter == 0:
            print(f"\nNo experiments found for: {distractor_config}")
            continue
        
        print(f"\n{'='*50}")
        print(f"Configuration: {distractor_config.upper()}")
        print(f"{'='*50}")
        
        print(f"Found experiments for questioner counts: {sorted(experiments.keys())}")
        print(f"Questioner iterations:")
        for q_count in sorted(experiments.keys()):
            iters = sorted(experiments[q_count].keys())
            print(f"  {q_count} questioners: iterations {iters}")
        
        print(f"\nMax common iterations across all questioner counts: {max_common_iter}")
        
        # Collect results
        results = []
        
        for q_count in sorted(experiments.keys()):
            for iter_num in range(1, max_common_iter + 1):
                iter_str = str(iter_num)
                if iter_str not in experiments[q_count]:
                    continue
                
                json_file = experiments[q_count][iter_str]
                
                # Load the single JSON file containing all poem pairs for this (questioner_count, iteration)
                exp_data = load_experiment_json(json_file)
                mrs, wos, tms, adherence = calculate_scores_from_experiment(exp_data)
                
                results.append({
                    'questioners': int(q_count),
                    'iteration': iter_num,
                    'mrs': mrs,
                    'wos': wos,
                    'tms': tms,
                    'adherence_score': adherence
                })
                
                print(f"  Questioners={q_count}, Iteration={iter_num}: "
                      f"MRS={mrs:.4f}, WOS={wos:.4f}, TMS={tms:.4f}, Adherence={adherence:.4f}")
        
        if not results:
            continue
        
        # Create DataFrame
        df = pd.DataFrame(results)
        
        # Save CSV
        csv_filename = f'evaluation_results_{distractor_config}.csv'
        csv_path = os.path.join(model_path, csv_filename)
        df.to_csv(csv_path, index=False)
        print(f"\nResults saved to: {csv_path}")
        
        # Generate plots
        plot_filename = f'evaluation_plots_{distractor_config}.png'
        plot_evaluation_results(df, model_path, plot_filename, distractor_config)
    
    print(f"\n{'='*60}")
    print("Evaluation complete!")
    print(f"{'='*60}\n")


def plot_evaluation_results(df, model_path, plot_filename='evaluation_plots.png', distractor_config=''):
    """
    Generate plots showing score trends across questioner counts.
    
    Args:
        df: DataFrame with evaluation results
        model_path: Path to save plots
        plot_filename: Name of the output plot file
        distractor_config: Configuration name for title (e.g., 'with_distractor')
    """
    print("\nGenerating plots...")
    
    # Create figure with subplots for each metric
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    config_title = f' ({distractor_config.replace("_", " ").title()})' if distractor_config else ''
    fig.suptitle(f'Evaluation Results Across Different Questioner Counts{config_title}', fontsize=16)
    
    metrics = ['mrs', 'wos', 'tms', 'adherence_score']
    metric_labels = ['Memory Recall Score', 'Word Overlapping Score', 'Thread Maintenance Score', 'Adherence Score']
    
    for idx, (metric, label) in enumerate(zip(metrics, metric_labels)):
        ax = axes[idx // 2, idx % 2]
        
        # Plot lines for each iteration
        for iteration in sorted(df['iteration'].unique()):
            iter_data = df[df['iteration'] == iteration]
            ax.plot(iter_data['questioners'], iter_data[metric], marker='o', label=f'Iteration {iteration}')
        
        ax.set_xlabel('Number of Questioners')
        ax.set_ylabel(label)
        ax.set_title(label)
        ax.legend()
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plot_path = os.path.join(model_path, plot_filename)
    plt.savefig(plot_path, dpi=300, bbox_inches='tight')
    print(f"Plots saved to: {plot_path}")
    plt.close()


def main(model_path):
    """
    Entry point for evaluation.
    
    Usage:
        python -c "from src.evaluate_offline import main; main('data/output/Groq_Llama3.3')"
    """
    evaluate_model(model_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python -m src.evaluate_offline <model_path>")
        print("Example: python -m src.evaluate_offline data/output/Groq_Llama3.3")
        sys.exit(1)
    
    model_path = sys.argv[1]
    main(model_path)
