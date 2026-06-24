# Dynamic Model Configuration Guide

## Overview

The experiment setup is now dynamic, allowing you to use different LLM providers and models without modifying code. You can specify:
- **Base URL**: API endpoint
- **Model Name**: Model identifier
- **API Key Environment Variable**: Where the API key is stored

## Default Configuration

By default, the system uses:
- **Provider**: Groq
- **Base URL**: `https://api.groq.com/openai/v1`
- **Model**: `llama-3.3-70b-versatile`
- **API Key**: `GROQ_API_KEY` environment variable

## Usage Examples

### 1. Groq (Default)

No parameters needed - uses default Groq configuration:

```bash
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3
```

Optionally specify explicitly:

```bash
python main.py experiment \
  --model-path data/output/Groq_Llama3.3 \
  --questioners 3 \
  --base-url https://api.groq.com/openai/v1 \
  --model-name llama-3.3-70b-versatile \
  --api-key-env GROQ_API_KEY
```

### 2. OpenAI GPT-4

```bash
python main.py experiment \
  --model-path data/output/OpenAI_GPT4 \
  --questioners 3 \
  --base-url https://api.openai.com/v1 \
  --model-name gpt-4 \
  --api-key-env OPENAI_API_KEY
```

### 3. Anthropic Claude

```bash
python main.py experiment \
  --model-path data/output/Anthropic_Claude \
  --questioners 3 \
  --base-url https://api.anthropic.com/v1 \
  --model-name claude-3-opus \
  --api-key-env ANTHROPIC_API_KEY
```

### 4. Local Ollama

```bash
python main.py experiment \
  --model-path data/output/Ollama_Llama2 \
  --questioners 3 \
  --base-url http://localhost:11434/v1 \
  --model-name llama2 \
  --api-key-env OLLAMA_API_KEY
```

### 5. Azure OpenAI

```bash
python main.py experiment \
  --model-path data/output/Azure_GPT4 \
  --questioners 3 \
  --base-url https://<your-resource>.openai.azure.com/v1 \
  --model-name gpt-4-deployment-name \
  --api-key-env AZURE_OPENAI_API_KEY
```

## Environment Setup

### Step 1: Set Environment Variables

Create or update your `.env` file in the project root:

```bash
# .env

# Groq
GROQ_API_KEY=your-groq-api-key

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Anthropic
ANTHROPIC_API_KEY=your-anthropic-api-key

# Ollama (usually empty if local)
OLLAMA_API_KEY=optional

# Azure
AZURE_OPENAI_API_KEY=your-azure-api-key
```

### Step 2: Verify Environment Variables

```bash
# Check that variables are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('GROQ_API_KEY:', os.getenv('GROQ_API_KEY'))"
```

## Multiple Models Comparison

Run experiments with different models and compare results:

```bash
# Test Groq
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 3 --count 3
python main.py experiment --model-path data/output/Groq_Llama3.3 --questioners 4 --count 3

# Test OpenAI GPT-4
python main.py experiment \
  --model-path data/output/OpenAI_GPT4 \
  --questioners 3 \
  --count 3 \
  --base-url https://api.openai.com/v1 \
  --model-name gpt-4 \
  --api-key-env OPENAI_API_KEY

python main.py experiment \
  --model-path data/output/OpenAI_GPT4 \
  --questioners 4 \
  --count 3 \
  --base-url https://api.openai.com/v1 \
  --model-name gpt-4 \
  --api-key-env OPENAI_API_KEY

# Evaluate each model
python main.py evaluate --model-path data/output/Groq_Llama3.3
python main.py evaluate --model-path data/output/OpenAI_GPT4
```

## Batch Script Example

Create a script to test multiple models:

```bash
#!/bin/bash
# test_all_models.sh

QUESTIONERS=(3 4 5)
EXPERIMENTS=3

# Groq
echo "Testing Groq..."
for q in "${QUESTIONERS[@]}"; do
  python main.py experiment \
    --model-path data/output/Groq_Llama3.3 \
    --questioners $q \
    --count $EXPERIMENTS
done
python main.py evaluate --model-path data/output/Groq_Llama3.3

# OpenAI GPT-4
echo "Testing OpenAI GPT-4..."
for q in "${QUESTIONERS[@]}"; do
  python main.py experiment \
    --model-path data/output/OpenAI_GPT4 \
    --questioners $q \
    --count $EXPERIMENTS \
    --base-url https://api.openai.com/v1 \
    --model-name gpt-4 \
    --api-key-env OPENAI_API_KEY
done
python main.py evaluate --model-path data/output/OpenAI_GPT4

# Anthropic Claude
echo "Testing Anthropic Claude..."
for q in "${QUESTIONERS[@]}"; do
  python main.py experiment \
    --model-path data/output/Anthropic_Claude \
    --questioners $q \
    --count $EXPERIMENTS \
    --base-url https://api.anthropic.com/v1 \
    --model-name claude-3-opus \
    --api-key-env ANTHROPIC_API_KEY
done
python main.py evaluate --model-path data/output/Anthropic_Claude
```

Usage:
```bash
chmod +x test_all_models.sh
./test_all_models.sh
```

## Programmatic Usage

You can also use the API directly in Python:

```python
from src.experiment import run_experiment

# Run with Groq (default)
mrs, wos, tms, adherence = run_experiment(
    model_base_path='data/output/Groq_Llama3.3',
    questioner_count=3
)

# Run with OpenAI
mrs, wos, tms, adherence = run_experiment(
    model_base_path='data/output/OpenAI_GPT4',
    questioner_count=3,
    base_url='https://api.openai.com/v1',
    model_name='gpt-4',
    api_key_env='OPENAI_API_KEY'
)

# Run with Anthropic
mrs, wos, tms, adherence = run_experiment(
    model_base_path='data/output/Anthropic_Claude',
    questioner_count=3,
    base_url='https://api.anthropic.com/v1',
    model_name='claude-3-opus',
    api_key_env='ANTHROPIC_API_KEY'
)
```

## JSON Metadata

When an experiment runs with custom model parameters, the JSON file stores this information:

```json
{
  "metadata": {
    "Questioners": 3,
    "Iteration": 1,
    "Distractors": false,
    "BaseURL": "https://api.openai.com/v1",
    "ModelName": "gpt-4"
  },
  "scores": {...},
  "poems": [...]
}
```

This allows you to track which model/configuration produced each result.

## Common Issues

### Issue: API Key Not Found

**Error:** `ValueError: API key not found in environment variable: OPENAI_API_KEY`

**Solution:** 
1. Add the key to `.env` file
2. Verify the environment variable name matches exactly
3. Reload the environment: `source .env`

### Issue: Connection Error

**Error:** `ConnectTimeout: Failed to establish connection`

**Solution:**
1. Verify the `base_url` is correct
2. Check API endpoint is accessible
3. For local Ollama: ensure it's running on `http://localhost:11434`

### Issue: Invalid Model Name

**Error:** `InvalidRequestError: The model 'model-xyz' does not exist`

**Solution:**
1. Check model name is correct for the provider
2. Verify the model is available in your account
3. Groq models: https://console.groq.com/keys
4. OpenAI models: https://platform.openai.com/account/billing/overview

## CLI Reference

```bash
# Show all options
python main.py experiment --help

# All parameters
--model-path TEXT          Base path for output (default: data/output/Groq_Llama3.3)
--questioners INT          Number of questioners (required)
--distractors              Include distractor rounds (flag)
--count INT                Number of experiments (default: 1)
--base-url TEXT            API base URL
--model-name TEXT          Model identifier
--api-key-env TEXT         Environment variable for API key
```

## Supported Models by Provider

### Groq (Free/Fast)
- `llama-3.3-70b-versatile`
- `llama-3.1-405b-reasoning`
- `mixtral-8x7b-32768`

### OpenAI
- `gpt-4`
- `gpt-4-turbo`
- `gpt-3.5-turbo`

### Anthropic
- `claude-3-opus-20240229`
- `claude-3-sonnet-20240229`
- `claude-3-haiku-20240307`

### Ollama (Local)
- `llama2`
- `mistral`
- `neural-chat`
- (Any model you've pulled)

### Azure
- Your deployment names
- Same models as OpenAI

## Next Steps

1. Set up API keys in `.env`
2. Run experiments with different models
3. Compare results using evaluation
4. Analyze performance differences
