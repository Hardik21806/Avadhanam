import json
import os

def save_experiment_json(model_name, questioner_count, data):
    """
    Saves raw experiment data to: data/output/Model/Count/exp_N.json
    Automatically finds the next available N to prevent overwriting.
    """
    folder_path = os.path.join("data", "output", model_name, f"{questioner_count}_questioners")
    os.makedirs(folder_path, exist_ok=True)
    
    # Check existing files to determine the next experiment number
    existing_files = [f for f in os.listdir(folder_path) if f.startswith("exp_") and f.endswith(".json")]
    
    # Calculate next index (if 3 files exist, next is 4)
    next_index = len(existing_files) + 1
    file_path = os.path.join(folder_path, f"exp_{next_index}.json")
    
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    
    print(f"Successfully saved experiment as: {file_path}")