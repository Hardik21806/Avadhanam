# CLI Commands Reference

## Command Structure

```
python main.py <command> [options]
```

## Commands

### 1. EXPERIMENT Command

**Purpose:** Run a single experiment with specified configuration

**Syntax:**
```bash
python main.py experiment --model-path <path> --questioners <count> [--distractors] [--count <n>]
```

**Options:**
- `--model-path TEXT` (default: `data/output/Groq_Llama3.3`)
  - Base path for model output
  - Must be writable
  - Example: `data/output/Groq_Llama3.3`

- `--questioners INT` (required)
  - Number of questioners for this experiment
  - Positive integer
  - Example: `3`, `4`, `5`

- `--distractors` (flag, optional)
  - Include distractor rounds in experiment
  - No value needed, just add the flag
  - Default: disabled

- `--count INT` (default: `1`)
  - Number of experiments to run with this configuration
  - Positive integer
  - Example: `1`, `5`, `10`

**Examples:**

```bash
# Single experiment: 3 questioners, no distractors
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3

# Single experiment: 3 questioners, with distractors
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --distractors

# Run 5 experiments: 4 questioners, with distractors
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 4 --count 5 --distractors

# Using default model path
python main.py experiment --questioners 3

# Custom model path
python main.py experiment --model-path data/output/MyModel_v2 --questioners 5 --count 3
```

**Output Structure:**
```
model_path/
└── <questioners>_questioners_<iteration>/
    ├── exp_1.json
    ├── exp_2.json
    └── exp_N.json
```

**What happens:**
1. Determines iteration number automatically (increments each run)
2. Creates directory `<questioners>_questioners_<iteration>/`
3. Runs experiment N times (`--count` parameter)
4. Saves each run as `exp_1.json`, `exp_2.json`, etc.
5. Prints progress and scores to console

---

### 2. EVALUATE Command

**Purpose:** Evaluate all accumulated experiments for a model

**Syntax:**
```bash
python main.py evaluate --model-path <path>
```

**Options:**
- `--model-path TEXT` (required)
  - Path to model output directory containing experiments
  - Must contain `<questioners>_questioners_<iteration>/` folders
  - Example: `data/output/Groq_Llama3.3`

**Examples:**

```bash
# Evaluate model
python main.py evaluate --model-path data/output/Groq_Llama3.3

# Evaluate custom model
python main.py evaluate --model-path data/output/MyModel_v2
```

**Output Files:**
1. `evaluation_results.csv` - Score sheet with columns:
   - `questioners`: Number of questioners
   - `iteration`: Iteration number
   - `mrs`: Memory Recall Score
   - `wos`: Word Overlapping Score
   - `tms`: Thread Maintenance Score
   - `adherence_score`: Limerick adherence score

2. `evaluation_plots.png` - 2x2 grid showing score trends

**What happens:**
1. Scans directory for all `<questioners>_questioners_<iteration>/` folders
2. Identifies all unique questioner counts
3. Finds iterations available for each questioner count
4. Determines max common iterations (iterations that exist for ALL questioner counts)
5. For each (questioner, iteration) pair:
   - Loads all `exp_N.json` files
   - Averages their scores
   - Creates one row in CSV
6. Generates visualization plots
7. Saves CSV and PNG to model directory

---

## Workflow Examples

### Workflow 1: Single Configuration Test

```bash
# Run one experiment with 3 questioners
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3

# Evaluate (will only show 3 questioners, 1 iteration)
python main.py evaluate --model-path data/output/Groq_Llama3.3
```

### Workflow 2: Multi-Questioner Comparison

```bash
# Run experiments for different questioner counts
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --count 5
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 4 --count 5
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 5 --count 5

# Evaluate to see trends
python main.py evaluate --model-path data/output/Groq_Llama3.3
```

### Workflow 3: Iterative Testing with Distractors

```bash
# Test without distractors first
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --count 3
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 4 --count 3
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 5 --count 3

# Evaluate first round
python main.py evaluate --model-path data/output/Groq_Llama3.3
# → Creates evaluation_results_round1.csv

# Now test with distractors (creates new iterations)
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --count 3 --distractors
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 4 --count 3 --distractors
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 5 --count 3 --distractors

# Evaluate again (will show more iterations)
python main.py evaluate --model-path data/output/Groq_Llama3.3
# → Updates evaluation results with new iterations
```

### Workflow 4: Batch Testing (Multiple Models)

```bash
# Test multiple models in a loop
for model in "Groq_Llama3.3" "OpenAI_GPT4" "Anthropic_Claude"; do
  echo "Testing $model..."
  python main.py experiment --model-path data/output/$model --questioners 3 --count 5
  python main.py experiment --model-path data/output/$model --questioners 4 --count 5
  python main.py experiment --model-path data/output/$model --questioners 5 --count 5
  python main.py evaluate --model-path data/output/$model
done
```

### Workflow 5: Automated Scaling Test

```bash
#!/bin/bash
# scale_test.sh

MODEL_PATH="data/output/Groq_Llama3.3"
QUESTIONERS_RANGE=(3 4 5 6 7)
EXPERIMENTS_PER_Q=10

for q in "${QUESTIONERS_RANGE[@]}"; do
  echo "Running $EXPERIMENTS_PER_Q experiments with $q questioners..."
  python main.py experiment \
    --model-path "$MODEL_PATH" \
    --questioners "$q" \
    --count "$EXPERIMENTS_PER_Q"
  
  echo "Evaluating..."
  python main.py evaluate --model-path "$MODEL_PATH"
done

echo "All scaling tests completed!"
```

---

## Directory State Examples

### After Single Experiment
```
data/output/Groq_Llama3.3/
└── 3_questioners_1/
    └── exp_1.json
```

### After Multiple Experiments (Same Questioner Count)
```
data/output/Groq_Llama3.3/
├── 3_questioners_1/
│   ├── exp_1.json
│   ├── exp_2.json
│   └── exp_3.json
├── 3_questioners_2/
│   ├── exp_1.json
│   └── exp_2.json
└── 3_questioners_3/
    └── exp_1.json
```

### After Multiple Questioner Counts
```
data/output/Groq_Llama3.3/
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
├── 5_questioners_1/
│   ├── exp_1.json
│   ├── exp_2.json
│   └── exp_3.json
├── evaluation_results.csv      ← Generated after evaluate
└── evaluation_plots.png        ← Generated after evaluate
```

---

## CSV Output Format

**evaluation_results.csv:**

```
questioners,iteration,mrs,wos,tms,adherence_score
3,1,0.85,0.78,0.92,0.75
3,2,0.87,0.80,0.91,0.78
4,1,0.82,0.75,0.88,0.72
4,2,0.84,0.77,0.89,0.74
5,1,0.80,0.72,0.85,0.70
5,2,0.82,0.74,0.86,0.72
```

**Interpretation:**
- Each row = one (questioners, iteration) combination
- Scores are **averaged** across all `exp_N.json` files in that combination
- Example: Row "3,1" averages scores from `3_questioners_1/exp_1.json`, `exp_2.json`, `exp_3.json`

---

## Troubleshooting

### Command not found
```
Error: 'python main.py' command not found
```
**Solution:** Make sure you're in the project root directory
```bash
cd /Users/dipsambhavani/Study/MTech/MTP/Repo/Avadhanam
python main.py --help
```

### Missing required argument
```
Error: the following arguments are required: --model-path
```
**Solution:** 
- For `experiment`: Add `--questioners N`
- For `evaluate`: Add `--model-path <path>`

### No experiments found
```
Error: No experiments found in the directory.
```
**Solution:** Run experiments first before evaluating
```bash
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3
python main.py evaluate --model-path data/output/Groq_Llama3.3
```

### Permission denied
```
Error: Permission denied: 'data/output/Groq_Llama3.3'
```
**Solution:** Check write permissions
```bash
chmod -R 755 data/output/Groq_Llama3.3
```

---

## Help Commands

```bash
# Show overall help
python main.py --help

# Show experiment command help
python main.py experiment --help

# Show evaluate command help
python main.py evaluate --help
```
