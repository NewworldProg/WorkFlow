# Training Data Organization

This directory contains all training data for the GPT-2 chat model.

## Directory Structure

```
training_data/
├── README.md           # This file
├── raw_data/          # Raw chat conversations (input for chat_training_dataset.py)
│   └── *.txt          # Raw text files with chat conversations
└── parsed_data/       # Processed JSON data (input for train_chat_gpt2.py)
    └── *.json         # Structured JSON files ready for training
```

## Workflow

1. **Step 1: Place raw chat data**
   - Put your raw chat conversation files in `raw_data/`
   - Files should be in `.txt` format

2. **Step 2: Process raw data**
   ```bash
   python ai/chat_training_dataset.py
   ```
   - Reads from `raw_data/`
   - Outputs structured JSON to `parsed_data/`

3. **Step 3: Train GPT-2 model**
   ```bash
   python ai/train_chat_gpt2.py
   ```
   - Reads from `parsed_data/`
   - Outputs trained model to `ai/trained_models/`

## File Naming Convention

- Raw data: `chat_conversations_[version].txt`
- Parsed data: `chat_conversations_[version]_parsed.json`

Example:
- `raw_data/chat_conversations_v1.txt`
- `parsed_data/chat_conversations_v1_parsed.json`