# Refactoring Summary

## Changes Made

### 1. **main.py** - Separated into CLI with two commands

**Before:** Hardcoded loops running experiments and evaluation together
**After:** Flexible CLI interface
- `python main.py experiment`: Run experiments
- `python main.py evaluate`: Evaluate results

### 2. **src/experiment.py** - Focused on experiment execution only

**New Function:**
```python
def run_experiment(model_base_path, questioner_count, use_distractors=False)
```
- Takes base path, questioner count, and distractor flag
- Automatically determines iteration number using `get_next_iteration()`
- Saves results to `model_base_path/<questioner_count>_questioners_<iteration>/exp_N.json`
- Returns scores tuple: `(mrs, wos, tms, adherence_score)`

**Key Changes:**
- Removed CSV writing logic
- Removed evaluation logic
- Added metric calculation (moved from main.py)
- Organized helpers with `_` prefix (private functions)

### 3. **src/utils.py** - Added iteration management

**New Functions:**

```python
def get_next_iteration(base_path, questioner_count) -> int
```
- Scans for existing `<questioner_count>_questioners_<iteration>` folders
- Returns next available iteration number
- Returns 1 if no folders exist

```python
def save_experiment_json(model_base_path, questioner_count, iteration, data)
```
- Updated signature to include `iteration` parameter
- Saves to: `model_base_path/<questioner_count>_questioners_<iteration>/exp_N.json`

### 4. **src/evaluate_offline.py** - Complete rewrite

**New Functions:**

```python
def parse_directory_name(dir_name) -> Tuple[int, int]
```
- Parses `3_questioners_2` → `(3, 2)`

```python
def scan_experiments_directory(model_path) -> Dict
```
- Scans all experiment folders
- Returns hierarchical structure: `{questioner: {iteration: [json_files]}}`

```python
def find_max_common_iterations(experiments) -> int
```
- Finds max iterations that exist for ALL questioner counts
- Example: `{3: [1,2,3], 4: [1,2]} → 2`

```python
def evaluate_model(model_path) -> DataFrame
```
- Main evaluation function
- Generates CSV: `evaluation_results.csv`
- Generates plots: `evaluation_plots.png`
- Returns pandas DataFrame

**Key Changes:**
- Removed old code scanning single directory structure
- Added proper handling of hierarchical folders
- Added automatic max-common-iterations detection
- Added plotting functionality
- Made it a standalone module that can be imported

## Directory Structure Changes

### Before
```
data/output/Groq_Llama3.3/
├── 3_questioners/
│   ├── exp_1.json
│   ├── exp_2.json
│   └── exp_3.json
├── 4_questioners/
│   └── ...
└── benchmarking_results_*.csv
```

### After
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
│   └── ...
├── evaluation_results.csv
└── evaluation_plots.png
```

## Usage Examples

### Run Single Experiment
```bash
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3
```

### Run Multiple Experiments
```bash
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --count 5 --distractors
```

### Evaluate Results
```bash
python main.py evaluate --model-path data/output/Groq_Llama3.3
```

## Benefits

1. **Separation of Concerns**
   - Experiments are independent from evaluation
   - Can run many experiments before evaluating
   - Can evaluate at any time

2. **Automatic Iteration Tracking**
   - No manual iteration numbering needed
   - Safe to re-run experiments without overwriting
   - Easy to track progress

3. **Flexible Evaluation**
   - Automatically handles different questioner counts
   - Finds max common iterations across all types
   - Generates both CSV and plots

4. **Scalability**
   - Easy to add more questioner counts
   - Easy to add more metrics
   - CLI allows batching experiments via shell scripts

5. **Better Organization**
   - Hierarchical directory structure
   - Clearer file naming convention
   - Self-documenting through directory names

## Migration Notes

If you have old experiment data in the old format:

1. The old format had: `data/output/MODEL/3_questioners/exp_N.json`
2. The new format has: `data/output/MODEL/3_questioners_1/exp_N.json`

**To migrate old data:**
```bash
# Create iteration 1 directory
mkdir -p data/output/Groq_Llama3.3/3_questioners_1

# Move old experiments
mv data/output/Groq_Llama3.3/3_questioners/exp_*.json data/output/Groq_Llama3.3/3_questioners_1/
```

## File Changes Summary

| File | Changes | Impact |
|------|---------|--------|
| `main.py` | Complete rewrite | CLI interface, separate commands |
| `src/experiment.py` | Focus on running, removed evaluation | Cleaner, single responsibility |
| `src/utils.py` | Added `get_next_iteration()` | Automatic iteration management |
| `src/evaluate_offline.py` | Complete rewrite | Proper evaluation pipeline |
| `USAGE.md` | New file | User documentation |

## Testing the Changes

```bash
# 1. Run an experiment
python main.py experiment --model-path data/output/Test --questioners 3

# Expected: Creates data/output/Test/3_questioners_1/exp_1.json

# 2. Run another experiment (should increment iteration)
python main.py experiment --model-path data/output/Test --questioners 3

# Expected: Creates data/output/Test/3_questioners_2/exp_1.json

# 3. Run with different questioner count
python main.py experiment --model-path data/output/Test --questioners 4

# Expected: Creates data/output/Test/4_questioners_1/exp_1.json

# 4. Evaluate
python main.py evaluate --model-path data/output/Test

# Expected:
# - data/output/Test/evaluation_results.csv
# - data/output/Test/evaluation_plots.png
```
