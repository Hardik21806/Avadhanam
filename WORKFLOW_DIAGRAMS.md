# Avadhanam Workflow Architecture

## System Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         main.py (CLI)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Command: experiment                Command: evaluate              │
│  ────────────────────                ────────────────              │
│  python main.py experiment           python main.py evaluate       │
│    --model-path PATH                   --model-path PATH           │
│    --questioners N                                                 │
│    [--distractors]                                                 │
│    [--count C]                                                     │
│                                                                     │
└──────────┬──────────────────────────────────────────────────┬───────┘
           │                                                  │
           ▼                                                  ▼
    ┌─────────────────┐                          ┌──────────────────┐
    │ src/experiment  │                          │ src/evaluate_    │
    │    .py          │                          │ offline.py       │
    └────────┬────────┘                          └─────────┬────────┘
             │                                            │
             │ run_experiment()                          │
             │ ├── make_questions()                       │
             │ ├── choose_topics()                        │
             │ ├── test_model()                           │
             │ ├── calculate_metrics()                    │
             │ └── save_experiment_json()                 │
             │                                            │
             │                                   scan_experiments_directory()
             │                                   ├── parse_directory_name()
             │                                   │
             │                                   find_max_common_iterations()
             │                                   │
             │                                   For each (Q, iter) pair:
             │                                   ├── load_experiment_json()
             │                                   ├── calculate_scores()
             │                                   └── Average across exp_N
             │                                   │
             │                                   └── generate plots
             │                                   └── save CSV
             ▼                                            ▼
    ┌──────────────────┐                    ┌─────────────────────┐
    │ src/utils.py     │                    │ File System         │
    ├──────────────────┤                    ├─────────────────────┤
    │                  │                    │                     │
    │ get_next_        │◄────────────────► ├─ evaluation_        │
    │   iteration()    │  Read dir         │  results.csv        │
    │                  │                    │                     │
    │ save_experiment  │◄────────────────► ├─ evaluation_        │
    │   _json()        │  Write JSON       │  plots.png          │
    │                  │                    │                     │
    └──────────────────┘                    └─────────────────────┘
             │
             │ Creates:
             ▼
    model_path/
    └── <Q>_questioners_<iter>/
        ├── exp_1.json
        ├── exp_2.json
        └── exp_N.json
```

## Experiment Execution Flow

```
START: python main.py experiment --questioners 3 --count 2
  │
  ▼
Determine iteration number: get_next_iteration()
  ├─ Scan for existing 3_questioners_* folders
  ├─ Find max iteration (e.g., 2)
  └─ Return next: 3
  │
  ├─ Create: 3_questioners_3/
  │
  ▼
First Experiment (exp_1):
  ├─ make_questions(3)
  ├─ choose_topics(questioners)
  ├─ test_model() [Poorana + Dharana]
  ├─ Calculate: mrs, wos, tms, adherence
  ├─ Create: experiment_data dict
  ├─ Save: 3_questioners_3/exp_1.json
  └─ Print: Scores
  │
  ▼
Second Experiment (exp_2):
  ├─ (repeat with new random seed)
  ├─ Save: 3_questioners_3/exp_2.json
  └─ Print: Scores
  │
  ▼
Return scores tuple & END
```

## Evaluation Execution Flow

```
START: python main.py evaluate --model-path data/output/Groq_Llama3.3
  │
  ▼
Scan directory for patterns:
  ├─ Find all: <Q>_questioners_<iter>/ folders
  ├─ Parse each: (questioner_count, iteration)
  └─ Build: {3: {1:[...], 2:[...]}, 4: {1:[...]}}
  │
  ▼
Calculate max common iterations:
  ├─ For Q=3: max iter = 2 (has 1, 2)
  ├─ For Q=4: max iter = 1 (has 1)
  ├─ For Q=5: max iter = 2 (has 1, 2)
  └─ Result: min(2, 1, 2) = 1
  │
  ▼
For each (Q, iter) where iter ≤ max_common:
  │
  ├─ Q=3, iter=1:
  │  ├─ Load: 3_questioners_1/exp_1.json
  │  ├─ Load: 3_questioners_1/exp_2.json
  │  ├─ Load: 3_questioners_1/exp_3.json
  │  ├─ Average: mrs, wos, tms, adherence
  │  └─ Add row to CSV
  │
  ├─ Q=4, iter=1:
  │  ├─ Load: 4_questioners_1/exp_1.json
  │  ├─ Average scores
  │  └─ Add row to CSV
  │
  └─ Q=5, iter=1:
     ├─ Load: 5_questioners_1/exp_1.json
     ├─ Average scores
     └─ Add row to CSV
  │
  ▼
Generate Plots:
  ├─ MRS vs Questioners
  ├─ WOS vs Questioners
  ├─ TMS vs Questioners
  └─ Adherence vs Questioners
  │
  ▼
Save Results:
  ├─ evaluation_results.csv
  ├─ evaluation_plots.png
  └─ Print: Summary & paths
  │
  ▼
END: Return DataFrame
```

## Iteration Management Logic

```
First Run with Q=3:
  └─ get_next_iteration('path', 3)
     ├─ Scan for 3_questioners_*
     ├─ Find: (none)
     └─ Return: 1
  └─ Create: 3_questioners_1/

Second Run with Q=3:
  └─ get_next_iteration('path', 3)
     ├─ Scan for 3_questioners_*
     ├─ Find: 3_questioners_1
     ├─ Extract: iterations = [1]
     └─ Return: max([1]) + 1 = 2
  └─ Create: 3_questioners_2/

Third Run with Q=3:
  └─ get_next_iteration('path', 3)
     ├─ Scan for 3_questioners_*
     ├─ Find: 3_questioners_1, 3_questioners_2
     ├─ Extract: iterations = [1, 2]
     └─ Return: max([1, 2]) + 1 = 3
  └─ Create: 3_questioners_3/
```

## Max Common Iterations Example

```
Scenario: After running experiments with counts: 3, 4, 5

Directory State:
  3_questioners_1/ (has exp_1, exp_2)
  3_questioners_2/ (has exp_1)
  3_questioners_3/ (has exp_1, exp_2, exp_3)
  4_questioners_1/ (has exp_1, exp_2)
  4_questioners_2/ (has exp_1)
  5_questioners_1/ (has exp_1)
  5_questioners_2/ (has exp_1, exp_2)

Collected Iterations:
  Q=3: [1, 2, 3]  → max = 3
  Q=4: [1, 2]     → max = 2
  Q=5: [1, 2]     → max = 2

Max Common = min(3, 2, 2) = 2

CSV will include:
  (3, 1), (3, 2)        ← Uses iter 1, 2 (skips 3)
  (4, 1), (4, 2)        ← Uses iter 1, 2
  (5, 1), (5, 2)        ← Uses iter 1, 2

CSV will NOT include:
  (3, 3)                ← Excluded because Q=4 doesn't have iter 3
```

## JSON File Structure

```
3_questioners_1/exp_1.json
{
  "metadata": {
    "Questioners": 3,
    "Iteration": 1,
    "Distractors": false
  },
  
  "poems": [
    {
      "id": "42",
      "topic": "moonlight",
      "main_poem": [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "line 5"
      ],
      "recall_poem": [
        "line 1",
        "line 2",
        "line 3",
        "line 4",
        "line 5"
      ]
    },
    { ...more questioners... }
  ],
  
  "scores": {
    "mrs": 0.85,
    "wos": 0.78,
    "tms": 0.92,
    "adherence_score": 0.75
  }
}
```

## CSV Output Structure

```
evaluation_results.csv

questioners,iteration,mrs,wos,tms,adherence_score
3,1,0.85,0.78,0.92,0.75
3,2,0.87,0.80,0.91,0.78
3,3,0.86,0.79,0.93,0.76
4,1,0.82,0.75,0.88,0.72
4,2,0.84,0.77,0.89,0.74
5,1,0.80,0.72,0.85,0.70
5,2,0.82,0.74,0.86,0.72

Note: Each row is AVERAGED across all exp_N.json files
      Example: Row "3,1" = average of 3_questioners_1/exp_1.json, exp_2.json, exp_3.json
```

## Key Data Flows

```
Experiment Data Flow:
  Config Input
    ├─ model_base_path
    ├─ questioner_count
    └─ use_distractors
         │
         ▼
    Run Experiment
    ├─ Compose poems
    ├─ Calculate metrics
    └─ Save JSON
         │
         ▼
    JSON Files
    ├─ 3_questioners_1/exp_1.json
    ├─ 3_questioners_1/exp_2.json
    └─ ...
```

```
Evaluation Data Flow:
  Model Path Input
         │
         ▼
    Scan Directories
    ├─ Find all <Q>_questioners_<iter>/ folders
    └─ Map to (questioner_count, iteration)
         │
         ▼
    Find Max Common Iterations
    ├─ Determine iterations available for each Q
    └─ Find minimum of maximums
         │
         ▼
    Load & Average JSON Files
    ├─ For each (Q, iter)
    ├─ Load all exp_N.json files
    └─ Calculate average scores
         │
         ▼
    Generate CSV & Plots
    ├─ evaluation_results.csv
    └─ evaluation_plots.png
```

## Benefits Visualization

```
Before (Mixed):
  main.py
    ├─ Run experiments  ⚠️ Hard-coded loops
    ├─ Calculate scores
    ├─ Save CSV         ⚠️ Single CSV for all
    ├─ Generate plots   ⚠️ Tied to experiment
    └─ Limited flexibility

After (Separated):
  experiment.py              evaluate_offline.py
    ├─ Run experiments    │       ├─ Load experiments
    ├─ Save JSON          │       ├─ Analyze patterns
    └─ Return scores      │       ├─ Generate CSV
                          │       └─ Plot trends
         │                │              │
         ▼                ▼              ▼
    CLI: main.py          CLI: main.py
    └─ experiment         └─ evaluate
    
    ✓ Independent runs
    ✓ Flexible evaluation
    ✓ Easy to scale
    ✓ Better organization
```
