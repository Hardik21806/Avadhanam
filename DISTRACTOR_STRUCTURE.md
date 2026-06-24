# Distractor-Based Directory Structure

## Overview

Experiments are now organized by distractor configuration. Each model output directory contains two separate subfolders.

Each JSON file (e.g., `3_questioners_1.json`) contains **all poem pairs** produced in one avadhana session with that many questioners.

```
data/output/<model_name>/
├── with_distractor/
│   ├── 3_questioners_1.json      (contains 3 poem pairs from 1st iteration)
│   ├── 3_questioners_2.json      (contains 3 poem pairs from 2nd iteration)
│   ├── 3_questioners_3.json
│   ├── 4_questioners_1.json      (contains 4 poem pairs from 1st iteration)
│   ├── 4_questioners_2.json
│   └── ...
├── without_distractor/
│   ├── 3_questioners_1.json      (contains 3 poem pairs from 1st iteration)
│   ├── 3_questioners_2.json      (contains 3 poem pairs from 2nd iteration)
│   ├── 3_questioners_3.json
│   ├── 4_questioners_1.json      (contains 4 poem pairs from 1st iteration)
│   ├── 4_questioners_2.json
│   └── ...
├── evaluation_results_with_distractor.csv
├── evaluation_results_without_distractor.csv
├── evaluation_plots_with_distractor.png
└── evaluation_plots_without_distractor.png
```

## JSON File Structure

Each JSON file contains the complete results of one avadhana session:

```json
{
  "metadata": {
    "Questioners": 3,
    "Iteration": 1,
    "Distractors": false,
    "BaseURL": "default",
    "ModelName": "default"
  },
  "poems": [
    {
      "id": "Q1",
      "topic": "Mountains",
      "main_poem": ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"],
      "recall_poem": ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]
    },
    {
      "id": "Q2",
      "topic": "Rivers",
      "main_poem": [...],
      "recall_poem": [...]
    },
    {
      "id": "Q3",
      "topic": "Ocean",
      "main_poem": [...],
      "recall_poem": [...]
    }
  ],
  "scores": {
    "mrs": 0.75,
    "wos": 0.68,
    "tms": 0.82,
    "adherence_score": 0.90
  }
}
```

## Running Experiments

### Without Distractors (Default)

```bash
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3
```

- Creates: `data/output/Groq_Llama3.3/without_distractor/3_questioners_1.json`
- Contains: 3 questioner poems with their metadata and metrics

### With Distractors

```bash
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --distractors
```

- Creates: `data/output/Groq_Llama3.3/with_distractor/3_questioners_1.json`
- Contains: 3 questioner poems (with distractor rounds included in the avadhana process)

### Multiple Iterations

```bash
# Run 3 iterations with 3 questioners
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --count 3
```

Creates:
```
without_distractor/
  3_questioners_1.json
  3_questioners_2.json
  3_questioners_3.json
```

### Multiple Questioner Counts

```bash
# Run experiments with different questioner counts
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --count 2
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 4 --count 2
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 5 --count 2
```

Creates:
```
without_distractor/
  3_questioners_1.json
  3_questioners_2.json
  4_questioners_1.json
  4_questioners_2.json
  5_questioners_1.json
  5_questioners_2.json
```

## Automatic Iteration Tracking

The iteration number is determined automatically:

- If no `3_questioners_<N>.json` files exist, iteration starts at 1
- If `3_questioners_1.json` and `3_questioners_2.json` exist, next iteration will be 3
- This tracking is **independent** for each distractor configuration

Example:
```
without_distractor/                with_distractor/
  3_questioners_1.json              3_questioners_1.json
  3_questioners_2.json              3_questioners_2.json
  4_questioners_1.json              4_questioners_3.json
                                    (different iteration counts!)
```

Both can have different iteration counts!

## Evaluation

Evaluation now generates **separate** results for each configuration:

```bash
python main.py evaluate --model-path data/output/Groq_Llama3.3
```

### Output Files

1. **evaluation_results_with_distractor.csv**
   ```
   questioners,iteration,mrs,wos,tms,adherence_score
   3,1,0.75,0.68,0.82,0.90
   3,2,0.76,0.69,0.81,0.91
   4,1,0.72,0.65,0.79,0.88
   4,2,0.73,0.66,0.80,0.89
   ```

2. **evaluation_results_without_distractor.csv**
   ```
   questioners,iteration,mrs,wos,tms,adherence_score
   3,1,0.78,0.71,0.85,0.92
   3,2,0.79,0.72,0.84,0.93
   4,1,0.75,0.68,0.82,0.90
   4,2,0.76,0.69,0.81,0.91
   ```

3. **evaluation_plots_with_distractor.png** - 2x2 subplot showing metrics trends
4. **evaluation_plots_without_distractor.png** - 2x2 subplot showing metrics trends

Each CSV file contains one row per (questioner_count, iteration) pair with the metrics.

## Comparing Configurations

To compare with-distractor vs without-distractor performance:

```bash
# Run experiments for both configurations
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --count 3
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 4 --count 3
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 5 --count 3

python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --count 3 --distractors
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 4 --count 3 --distractors
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 5 --count 3 --distractors

# Evaluate - generates both CSVs and plots for comparison
python main.py evaluate --model-path data/output/Groq_Llama3.3
```

The evaluation output will show:
- Separate CSV files with results for each configuration
- Separate plots showing trends for each configuration
- Allows side-by-side comparison of model performance with vs without distractors

## Python API

Using the programmatic interface:

```python
from src.experiment import run_experiment
from src.evaluate_offline import evaluate_model

# Run without distractors
run_experiment(
    model_base_path='data/output/Groq_Llama3.3',
    questioner_count=3,
    use_distractors=False  # Saves to without_distractor/3_questioners_1.json
)

# Run with distractors
run_experiment(
    model_base_path='data/output/Groq_Llama3.3',
    questioner_count=3,
    use_distractors=True   # Saves to with_distractor/3_questioners_1.json
)

# Evaluate both
evaluate_model('data/output/Groq_Llama3.3')
```

## Understanding JSON File Contents

Each `<Q>_questioners_<N>.json` file represents one complete avadhana session:

- **Questioners**: Q number of participants
- **Iteration**: The Nth run of this configuration
- **Each Poem Pair**: 
  - `main_poem`: The 5-line limerick composed in rounds (Poorana stage)
  - `recall_poem`: The recalled limerick after distraction (Dharana stage)
- **Scores**: Aggregate metrics for this session
  - `mrs`: Memory Recall Score (how well the recalled poem matches the main poem)
  - `wos`: Word Overlapping Score (word similarity)
  - `tms`: Thread Maintenance Score (semantic continuity)
  - `adherence_score`: AABBA rhyme scheme adherence

## Key Points

✅ **Single JSON file per session** - `<Q>_questioners_<iter>.json` contains all Q poem pairs
✅ **Distractor separation** - Clear folder structure for with/without distractor experiments
✅ **Automatic iteration management** - Each configuration tracks iterations independently
✅ **Clean evaluation** - Compare metrics across configurations
✅ **Backward compatible API** - All functions accept `use_distractors` parameter (defaults to `False`)
✅ **Reproducible** - Each JSON file is self-contained with all metadata and results
