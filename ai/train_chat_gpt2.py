"""
GPT-2 Chat Model Training Script
Trains GPT-2 model on processed JSON chat data
"""
import os
import json
import torch
from datetime import datetime
from transformers import (
    GPT2LMHeadModel, 
    GPT2Tokenizer, 
    DataCollatorForLanguageModeling,
    Trainer, 
    TrainingArguments
)
from torch.utils.data import Dataset
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)

class JSONChatDataset(Dataset):
    """Dataset that loads from processed JSON chat data"""
    # build components for extract training conversations data
    # 1. initialize tokenizer
    # 2. set block_size
    # 3. initialize data container
    # 4. initialize conversations
    # 5. initialize training examples
    def __init__(self, tokenizer, json_file_path, block_size=512):
        # Initialize tokenizer
        self.tokenizer = tokenizer
        # Set block size for tokenization
        self.block_size = block_size
        # log loading message
        print(f"📂 Loading processed chat data from: {json_file_path}")
        
        # initialize data container
        with open(json_file_path, 'r', encoding='utf-8') as f:
            self.data = json.load(f)
        
        # initialize extract training conversations data
        self.conversations = self.data["training_conversations"]
        print(f"💬 Loaded {len(self.conversations)} training conversations")
        
        # initialize extract training conversations data
        self.examples = self.create_training_examples()
    # function for create training examples

    def create_training_examples(self):
        """Create tokenized training examples from JSON data"""
        # var to hold examples
        examples = []
        # loop through conversations
        for conv in self.conversations:
            # get formatted training text
            training_text = conv["formatted_training_text"]
            
            print(f"📝 Processing conversation {conv['id']}: {conv['exchange_count']} exchanges")
            print(f"   Preview: {training_text[:150]}...")
            
            # Tokenize training text
            tokenized = self.tokenizer(
                training_text,
                truncation=True,
                max_length=self.block_size,
                return_tensors="pt"
            )
            
            examples.append(tokenized['input_ids'].squeeze())
        
        print(f"🎯 Created {len(examples)} tokenized training examples")
        return examples
    
    def __len__(self):
        return len(self.examples)
    
    def __getitem__(self, idx):
        return self.examples[idx]
    
    def get_metadata(self):
        """Get metadata from JSON file"""
        return self.data["metadata"]

class ChatGPT2Trainer:
    """GPT-2 model trainer for chat conversations"""
    # build components for training
    #1. model name (gpt2)
    #2. output directory for saving models
    #3. hardware device (cuda or cpu)
    def __init__(self, model_name="gpt2", output_dir="ai/trained_models"):
        # model name
        self.model_name = model_name
        # output dir
        self.output_dir = output_dir
        # hardware device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Create output directory for saving models
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(os.path.join(output_dir, "advanced_chat_model"), exist_ok=True)
        os.makedirs(os.path.join(output_dir, "final_chat_model"), exist_ok=True)
        
        print(f"🔧 Using device: {self.device}")
    # function to load model and tokenizer
    # 1. load tokenizer from pretrained model
    # 2. add special tokens for chat    
    # 3. load gpt2 model from pretrained
    # 4. resize model embeddings to match new tokenizer size
    def load_model_and_tokenizer(self):
        """Load GPT-2 model and tokenizer"""
        
        print(f"🤖 Loading model: {self.model_name}")
        
        # Load tokenizer
        self.tokenizer = GPT2Tokenizer.from_pretrained(self.model_name)
        
        # make dict for special tokens
        special_tokens = {
            "additional_special_tokens": [
                "<|client|>", 
                "<|freelancer|>", 
                "<|startoftext|>", 
                "<|endoftext|>"
            ]
        }
        # Add special tokens to tokenizer
        num_added = self.tokenizer.add_special_tokens(special_tokens)
        # log it
        print(f"➕ Added {num_added} special tokens")
        # set pad token to eos token
        self.tokenizer.pad_token = self.tokenizer.eos_token
        
        # Load model
        self.model = GPT2LMHeadModel.from_pretrained(self.model_name)
        # Resize model embeddings to match new tokenizer size
        self.model.resize_token_embeddings(len(self.tokenizer))
        # move model to device
        self.model.to(self.device)
        # log vocab size
        print(f"📊 Model loaded. Vocab size: {len(self.tokenizer)}")
    # function to train model
    #1. load model and tokenizer
    # 2. create dataset from chat data    
    # 3. set up data collator for language modeling
    # 4. define training arguments
    # 5. create trainer
    # 6. train the model
    # 7. save trained model and tokenizer
    # 8. save training metadata
    def train_model(self, json_data_path, epochs=5, batch_size=1, learning_rate=3e-5, validate_data=True):
        """Train the GPT-2 model on JSON chat data"""
        
        print("🚀 Starting model training from JSON data...")
        print(f"📋 Training parameters: epochs={epochs}, batch_size={batch_size}, lr={learning_rate}")
        
        # Validate JSON data
        if validate_data and not self.validate_json_data(json_data_path):
            return None
        
        # Load model and tokenizer
        self.load_model_and_tokenizer()
        
        # Create dataset from JSON
        dataset = JSONChatDataset(
            tokenizer=self.tokenizer,
            json_file_path=json_data_path,
            block_size=512
        )
        
        if len(dataset) == 0:
            raise ValueError("❌ No training examples found in JSON!")
        
        print(f"📊 Training on {len(dataset)} examples")
        
        # Ask user confirmation
        if validate_data:
            user_input = input("\n➡️  Continue with training? (y/N): ").lower().strip()
            if user_input != 'y':
                print("⏸️  Training cancelled.")
                return None
        
        # Data collator for language modeling
        data_collator = DataCollatorForLanguageModeling(
            tokenizer=self.tokenizer,
            mlm=False
        )
        
        # Training arguments
        training_args = TrainingArguments(
            output_dir=os.path.join(self.output_dir, "advanced_chat_model"),
            overwrite_output_dir=True,
            num_train_epochs=epochs,
            per_device_train_batch_size=batch_size,
            save_steps=50,
            save_total_limit=2,
            prediction_loss_only=True,
            learning_rate=learning_rate,
            warmup_steps=20,
            logging_dir=os.path.join(self.output_dir, "logs"),
            logging_steps=5,
            remove_unused_columns=False,
            dataloader_drop_last=False
        )
        
        # Create trainer from model, args, data collator, and dataset
        trainer = Trainer(
            model=self.model,
            args=training_args,
            data_collator=data_collator,
            train_dataset=dataset,
        )
        
        # Train the model
        print(f"🔥 Training for {epochs} epochs on {len(dataset)} examples...")
        trainer.train()
        
        # Save the trained model
        final_model_path = os.path.join(self.output_dir, "final_chat_model", "trained_chat_model_1.0")
        os.makedirs(final_model_path, exist_ok=True)
        
        trainer.save_model(final_model_path)
        self.tokenizer.save_pretrained(final_model_path)
        
        print(f"✅ Model training completed!")
        print(f"💾 Advanced model saved to: {os.path.join(self.output_dir, 'advanced_chat_model')}")
        print(f"🎯 Final model saved to: {final_model_path}")
        
        # Save training metadata
        metadata = dataset.get_metadata()
        self.save_training_metadata(final_model_path, json_data_path, metadata, epochs, batch_size, learning_rate, len(dataset))
        
        return final_model_path
    # function to validate json data
    # 1. check if file exists
    # 2. load json data
    # 3. print metadata and sample conversations
    def validate_json_data(self, json_path):
        """Validate JSON training data"""
        if not os.path.exists(json_path):
            print(f"❌ JSON training data not found: {json_path}")
            return False
        
        print(f"🔍 Validating JSON training data: {json_path}")
        
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        metadata = data["metadata"]
        conversations = data["training_conversations"]
        
        print(f"\n📊 Training Data Validation:")
        print(f"   📅 Processed on: {metadata['processed_on']}")
        print(f"   📁 Source file: {metadata['source_file']}")
        print(f"   💬 Training conversations: {len(conversations)}")
        print(f"   📝 Processor version: {metadata.get('processor_version', 'unknown')}")
        
        if len(conversations) == 0:
            print(f"❌ No training conversations found!")
            return False
        
        # Show sample conversations
        print(f"\n📋 Sample conversations:")
        for i, conv in enumerate(conversations[:3]):
            print(f"\n--- Conversation {conv['id']} ---")
            print(f"Exchanges: {conv['exchange_count']}")
            print(f"Text length: {conv['text_length']} chars")
            print(f"Speakers: {', '.join(conv['speakers'])}")
            # Show first exchange
            if conv['exchanges']:
                first_exchange = conv['exchanges'][0]
                print(f"First message: {first_exchange['speaker']} - {first_exchange['message'][:100]}...")
        
        return True
    # function to save training metadata
    #
    def save_training_metadata(self, model_path, json_data_path, source_metadata, epochs, batch_size, learning_rate, num_examples):
        """Save training metadata"""
        
        metadata = {
            "model_name": "trained_chat_model_1.0",
            "base_model": self.model_name,
            "training_data_json": json_data_path,
            "source_data_info": source_metadata,
            "training_params": {
                "epochs": epochs,
                "batch_size": batch_size,
                "learning_rate": learning_rate,
                "num_examples": num_examples
            },
            "trained_on": datetime.now().isoformat(),
            "device": str(self.device),
            "vocab_size": len(self.tokenizer),
            "special_tokens": ["<|client|>", "<|freelancer|>", "<|startoftext|>", "<|endoftext|>"]
        }
        
        metadata_path = os.path.join(model_path, "training_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Training metadata saved to: {metadata_path}")
# function to list available parsed data files
def list_available_parsed_data():
    """List available parsed data files"""
    parsed_data_dir = "ai/training_data/parsed_data"
    
    print(f"📂 Available parsed data files:")
    
    if os.path.exists(parsed_data_dir):
        parsed_files = [f for f in os.listdir(parsed_data_dir) if f.endswith('.json')]
        if parsed_files:
            for file in parsed_files:
                file_path = os.path.join(parsed_data_dir, file)
                size = os.path.getsize(file_path)
                
                # Try to read metadata
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    metadata = data.get("metadata", {})
                    conversations = data.get("training_conversations", [])
                    
                    print(f"\n� {file} ({size:,} bytes)")
                    print(f"   💬 Training conversations: {len(conversations)}")
                    print(f"   📅 Processed: {metadata.get('processed_on', 'unknown')}")
                    print(f"   📁 Source: {os.path.basename(metadata.get('source_file', 'unknown'))}")
                except:
                    print(f"\n� {file} ({size:,} bytes) - ❌ Invalid JSON")
            
            return parsed_files
        else:
            print(f"   No .json files found in {parsed_data_dir}")
            return []
    else:
        print(f"   Directory not found: {parsed_data_dir}")
        return []
# main function to run training
def main():
    """Main training function"""
    
    try:
        # List available parsed data files
        parsed_files = list_available_parsed_data()
        
        if not parsed_files:
            print(f"\n❌ No parsed data files found!")
            print(f"💡 Please run 'python ai/chat_training_dataset.py' first to process raw data")
            return False
        
        # Use default or first available file
        default_file = "ai/training_data/parsed_data/chat_conversations_v1_parsed.json"
        if os.path.exists(default_file):
            json_data_path = default_file
        else:
            json_data_path = os.path.join("ai/training_data/parsed_data", parsed_files[0])
            print(f"💡 Using available file: {json_data_path}")
        
        print(f"\n🎯 Starting GPT-2 training from processed JSON data")
        print(f"📄 Input file: {json_data_path}")
        
        # Initialize trainer
        trainer = ChatGPT2Trainer(model_name="gpt2")
        
        # Train model
        model_path = trainer.train_model(
            json_data_path=json_data_path,
            epochs=8,
            batch_size=1,
            learning_rate=2e-5,
            validate_data=True
        )
        
        if model_path:
            print(f"\n🎉 Training completed successfully!")
            print(f"🎯 Trained model available at: {model_path}")
            print(f"🚀 Ready to use trained model!")
        
        return model_path is not None
        
    except Exception as e:
        print(f"❌ Training failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'🎉 Training successful!' if success else '❌ Training failed!'}")