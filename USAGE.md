# Avadhanam - Experiment & Evaluation Guide

## Overview

The codebase has been refactored to **separate experiment execution from evaluation**. This allows you to:

1. Run experiments independently and save raw results
2. Evaluate accumulated results at any time
3. Track iterations automatically for the same questioner count

## Directory Structure

```
data/output/MODEL_NAME/
├── 3_questioners_1/
│   ├── exp_1.json
│   ├── exp_2.json
│   └── exp_3.json
├── 3_questioners_2/
│   ├── exp_1.json
│   └── exp_2.json
├── 4_questioners_1/
│   ├── exp_1.json
│   ├── exp_2.json
│   └── exp_3.json
└── evaluation_results.csv
└── evaluation_plots.png
```

**Naming Convention:**
- `<questioners>_questioners_<iteration>/`: Directory for each questioner count and iteration
- `exp_N.json`: Individual experiment result (N auto-incremented)
- Iteration number automatically increments when running new experiments for the same questioner count

## Usage

### 1. Run Experiments

Run a single experiment with specific questioner count:

```bash
# Run 1 experiment with 3 questioners (no distractors)
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3

# Run 1 experiment with 3 questioners (with distractors)
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --distractors

# Run 5 experiments with 4 questioners
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 4 --count 5

# Run experiments for multiple questioner counts
for q in 3 4 5; do
  python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners $q --count 3
done
```

**Options:**
- `--model-path`: Base path for model output (default: `data/output/Groq_Llama3.3`)
- `--questioners`: Number of questioners (required)
- `--distractors`: Include distractor rounds (flag, optional)
- `--count`: Number of experiments to run (default: 1)

### 2. Run Evaluation

Evaluate all accumulated experiments for a model:

```bash
python main.py evaluate --model-path data/output/Groq_Llama3.3
```

**What the evaluator does:**

1. **Scans directory** for all `<questioners>_questioners_<iteration>` folders
2. **Finds max common iterations** - determines how many iterations exist across ALL questioner counts
   - Example: If 3Q has iters [1,2,3], 4Q has [1,2], 5Q has [1,2,3,4]
   - Then max_common = 2 (all have at least 1 and 2)
3. **Generates CSV** with columns:
   - `questioners`: Number of questioners
   - `iteration`: Iteration number
   - `mrs`: Memory Recall Score (averaged across all exp_N.json files)
   - `wos`: Word Overlapping Score
   - `tms`: Thread Maintenance Score
   - `adherence_score`: Limerick adherence score
4. **Generates plots** showing score trends

### 3. Example Workflow

```bash
# Step 1: Run experiments for different questioner counts
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --count 5
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 4 --count 5
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 5 --count 5

# Step 2: Evaluate results
python main.py evaluate --model-path data/output/Groq_Llama3.3

# Results:
# - data/output/Groq_Llama3.3/evaluation_results.csv
# - data/output/Groq_Llama3.3/evaluation_plots.png
```

## Automatic Iteration Management

The `get_next_iteration()` function in `utils.py` automatically handles iteration numbering:

```python
from src.utils import get_next_iteration

# First experiment: 3_questioners_1/
iteration = get_next_iteration('data/output/Groq_Llama3.3', 3)  # Returns 1

# Second experiment: 3_questioners_2/
iteration = get_next_iteration('data/output/Groq_Llama3.3', 3)  # Returns 2

# And so on...
```

## JSON Structure

Each `exp_N.json` contains:

```json
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
      "main_poem": ["line 1", "line 2", "line 3", "line 4", "line 5"],
      "recall_poem": ["line 1", "line 2", "line 3", "line 4", "line 5"]
    }
  ],
  "scores": {
    "mrs": 0.85,
    "wos": 0.78,
    "tms": 0.92,
    "adherence_score": 0.75
  }
}
```

## Evaluation Results

### CSV Output

`evaluation_results.csv`:

| questioners | iteration | mrs   | wos   | tms   | adherence_score |
|-------------|-----------|-------|-------|-------|-----------------|
| 3           | 1         | 0.85  | 0.78  | 0.92  | 0.75            |
| 3           | 2         | 0.87  | 0.80  | 0.91  | 0.78            |
| 4           | 1         | 0.82  | 0.75  | 0.88  | 0.72            |
| 4           | 2         | 0.84  | 0.77  | 0.89  | 0.74            |
| 5           | 1         | 0.80  | 0.72  | 0.85  | 0.70            |
| 5           | 2         | 0.82  | 0.74  | 0.86  | 0.72            |

### Plot Output

`evaluation_plots.png` - 4 subplots showing:
1. Memory Recall Score vs Questioners (per iteration)
2. Word Overlapping Score vs Questioners (per iteration)
3. Thread Maintenance Score vs Questioners (per iteration)
4. Adherence Score vs Questioners (per iteration)

## Key Differences from Previous Version

| Aspect | Before | After |
|--------|--------|-------|
| **Entry Point** | `main.py` with hardcoded loops | CLI with `experiment` and `evaluate` commands |
| **Iteration Management** | Manual tracking | Automatic via `get_next_iteration()` |
| **Results Storage** | Single CSV for all experiments | Structured JSON per experiment + evaluation CSV |
| **Directory Organization** | Flat (`<questioners>_questioners/`) | Hierarchical (`<questioners>_questioners_<iteration>/`) |
| **Evaluation Flexibility** | Had to re-run experiments to evaluate | Can evaluate anytime after experiments complete |
| **Max Common Iterations** | Had to manually calculate | Automatic calculation during evaluation |

## Troubleshooting

### No experiments found
```
Error: No experiments found in the directory.
```
- Ensure experiments have been run first: `python main.py experiment ...`
- Check that `--model-path` is correct

### Iteration mismatch
If you see different max iterations per questioner count:
- This is normal - evaluation finds the **common max** across all questioner counts
- Only uses iterations that exist for ALL questioner counts

### Missing plots
If plots don't generate:
- Check that `matplotlib` and `seaborn` are installed
- Verify write permissions in the model directory

## Next Steps

1. Run experiments for multiple questioner counts
2. Evaluate to see score trends
3. Adjust model/prompts based on adherence scores
4. Re-run experiments for improved iterations
5. Compare evaluation plots across models
