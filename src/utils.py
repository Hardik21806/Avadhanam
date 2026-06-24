import json
import os
import re

def get_next_iteration(base_path, questioner_count, use_distractors=False):
    """
    Scans for existing <questioner_count>_questioners_<iteration>.json files
    and returns the next iteration number.
    
    Args:
        base_path: Path to the model output directory
        questioner_count: Number of questioners (e.g., 3)
        use_distractors: Whether to scan the with_distractor or without_distractor subfolder
    
    Returns:
        Next iteration number (1 if no files exist, else max + 1)
    """
    distractor_subfolder = "with_distractor" if use_distractors else "without_distractor"
    scan_path = os.path.join(base_path, distractor_subfolder)
    
    pattern = rf"^{questioner_count}_questioners_(\d+)\.json$"
    iterations = []
    
    try:
        for item in os.listdir(scan_path):
            match = re.match(pattern, item)
            if match:
                iterations.append(int(match.group(1)))
    except FileNotFoundError:
        pass
    
    return max(iterations) + 1 if iterations else 1


def save_experiment_json(model_base_path, questioner_count, iteration, data, use_distractors=False):
    """
    Saves avadhana experiment data to:
    model_base_path/with_distractor/<questioner_count>_questioners_<iteration>.json
    or
    model_base_path/without_distractor/<questioner_count>_questioners_<iteration>.json
    
    Each JSON file contains all poem pairs produced in one avadhana session.
    
    Args:
        model_base_path: Base path for the model output (e.g., data/output/Groq_Llama3.3)
        questioner_count: Number of questioners
        iteration: Iteration number
        data: Experiment data dictionary (contains all poem pairs for this questioner count)
        use_distractors: Whether to save to with_distractor or without_distractor subfolder
    """
    distractor_subfolder = "with_distractor" if use_distractors else "without_distractor"
    folder_path = os.path.join(model_base_path, distractor_subfolder)
    os.makedirs(folder_path, exist_ok=True)
    
    # Save as single JSON file: <questioner_count>_questioners_<iteration>.json
    file_path = os.path.join(folder_path, f"{questioner_count}_questioners_{iteration}.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"Successfully saved experiment as: {file_path}")