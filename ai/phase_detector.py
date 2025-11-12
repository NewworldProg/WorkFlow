"""
Phase Classifier Inference
Uses trained model to detect conversation phases
"""
import torch # lib for models tensor configuration
import torch.nn as nn # lib for neural network modules
from transformers import BertTokenizer, BertModel # lib for BERT model and tokenizer
import json # json lib
import os # operating system lib
from datetime import datetime # datetime lib

# Set UTF-8 encoding
import sys # lib for system specific parameters and functions
if sys.platform == "win32": # if the system is Windows UTF-8 encoding
    sys.stdout.reconfigure(encoding='utf-8') # to be able to handle special characters

# class for setting up model pipeline
class PhaseClassifier(nn.Module):
    # setting up model pipeline
    #1. model
    #2. dropout
    #3. classifier
    def __init__(self, n_classes=8, dropout=0.3):
        # Call the parent constructor
        super(PhaseClassifier, self).__init__()
        # Initialize BERT model
        self.bert = BertModel.from_pretrained('bert-base-uncased')
        # Add dropout to prevent overfitting and for better generalization
        self.dropout = nn.Dropout(dropout)
        # add linear layer to classify the output into n_classes, every id has a corresponding phase
        # hidden size represents the size of the output vector from BERT model
        self.classifier = nn.Linear(self.bert.config.hidden_size, n_classes)
    # forward function to give inputs that will be passed to the model
    #1. calls model
    #2. give a model input ids
    #3. give a model attention mask
    def forward(self, input_ids, attention_mask):
        # inside output give a model input ids and attention mask
        outputs = self.bert(
            input_ids=input_ids,
            attention_mask=attention_mask
        )
        # pooled output is token representation of [CLS] token
        pooled_output = outputs.pooler_output
        #output the CLS token with dropout applied
        output = self.dropout(pooled_output)
        # return classified output
        return self.classifier(output)

# based on classified text detect phase
class PhaseDetector:
    # Load and use trained phase classifier
    #1. model directory is entering parameter
    #2. hardware device that will run the model
    #3. metadata about the model
    #4. tokenizer for text processing
    #5. the model itself
    #6. load the trained version of the model
    #7. move model to device
    #8. set model to evaluation mode
    def __init__(self, model_dir):
        # var to hold directory to model
        self.model_dir = model_dir
        # var to hold device that will be used for running model cuda (graphics card) or cpu
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # Load metadata
        # var to hold directory to metadata.json
        metadata_path = os.path.join(model_dir, 'metadata.json')
        # open metadata file
        with open(metadata_path, 'r', encoding='utf-8') as f:
            self.metadata = json.load(f)
        # var to hold phase_labels array from metadata
        self.phase_labels = self.metadata['phase_labels']
        # var to hold id to phase mapping
        self.id_to_phase = {int(k): v for k, v in self.metadata['id_to_phase'].items()}
        
        # Load tokenizer from model directory
        self.tokenizer = BertTokenizer.from_pretrained(model_dir)

        # Load model for classification and input how many classes are there
        self.model = PhaseClassifier(n_classes=len(self.phase_labels))
        # var to hold directory which has the model
        model_path = os.path.join(model_dir, 'phase_classifier.pth')
        # load the model and use load_state_dict function to load trained model
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        # move model to device
        self.model.to(self.device)
        # set model to evaluation mode
        self.model.eval()

        #log model dir, metadata info, and other accuracy details
        print(f"[OK] Phase classifier loaded from {model_dir}")
        print(f"[INFO] Model trained on {self.metadata.get('training_samples', 'unknown')} samples")
        print(f"[INFO] Accuracy: {self.metadata.get('accuracy', 'unknown'):.2f}%")
    # predict function that takes context and return probabilities flag
    #1. tokenize the context text
    #2. from tokenized text give tokens the id
    #3. from tokenized text get tokens that are not relevant and give them "mask" for AI to not consider
    #4. use model to predict and not to teach him torch.no_grad
    #5. return result dictionary with phase and confidence score
    #6. optional return of all probabilities with their phase labels
    def predict(self, context, return_probabilities=False):
        """Predict conversation phase from context"""
        # Tokenize
        encoding = self.tokenizer.encode_plus(
            context, # text to be tokenized
            add_special_tokens=True, # add special tokens
            max_length=256, # max length of tokens
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        # get id of the tokenized text and move to device 
        input_ids = encoding['input_ids'].to(self.device) 
        # attention mask to ignore the tockens that are just padding
        attention_mask = encoding['attention_mask'].to(self.device)

        # use model to predict and don't teach it (no grad)
        with torch.no_grad():
            # put inputs through the model and attention mask to get outputs
            outputs = self.model(input_ids, attention_mask)
            # get probabilities of every class guess and than
            probabilities = torch.softmax(outputs, dim=1)
            # inside confidence and predticted put the class with most confidence
            confidence, predicted = torch.max(probabilities, 1)
        # map the predicted id to phase
        predicted_phase = self.id_to_phase[predicted.item()]
        # get confidence score
        confidence_score = confidence.item()
        # prepare result dictionary of phase and confidence
        result = {
            'phase': predicted_phase,
            'confidence': round(confidence_score, 4)
        }
        # optional return of all probabilities with their phase labels 
        if return_probabilities:
            all_probs = {
                self.phase_labels[i]: round(probabilities[0][i].item(), 4)
                for i in range(len(self.phase_labels))
            }
            result['all_probabilities'] = all_probs
        
        return result
    # loops through multiple contexts to predict their phases and predict for all
    def predict_batch(self, contexts):
        """Predict phases for multiple contexts"""
        results = []
        for context in contexts:
            result = self.predict(context)
            results.append(result)
        return results
# test function for phase detector to see if it works correctly
def test_detector():
    """Test the phase detector"""
    print("=" * 60)
    print("TESTING PHASE DETECTOR")
    print("=" * 60)
    
    model_dir = os.path.join(os.path.dirname(__file__), 'trained_models', 'phase_classifier_v1')
    
    if not os.path.exists(model_dir):
        print(f"[ERROR] Model not found at {model_dir}")
        print("[INFO] Please train the model first using train_phase_classifier.py")
        return
    
    detector = PhaseDetector(model_dir)
    
    # Test cases
    test_cases = [
        "Hello! I saw your application. Are you available?",
        "We need content about casino games. Can you handle technical topics?",
        "Can you explain what RTP means in slot machines?",
        "Which language do you prefer - English or Dutch?",
        "Our budget is $0.06 per word. Does that work?",
        "We need the first batch by Monday. Can you deliver?",
        "Each article needs H1, H2s, and FAQ section with SEO.",
        "I'm sending the contract now. Please accept to start."
    ]
    
    print("\n[INFO] Testing with sample contexts:\n")
    
    for i, context in enumerate(test_cases, 1):
        result = detector.predict(context, return_probabilities=True)
        print(f"{i}. Context: \"{context}\"")
        print(f"   → Phase: {result['phase']}")
        print(f"   → Confidence: {result['confidence']:.2%}")
        print(f"   → Top 3 probabilities:")
        
        sorted_probs = sorted(result['all_probabilities'].items(), key=lambda x: x[1], reverse=True)[:3]
        for phase, prob in sorted_probs:
            print(f"      - {phase}: {prob:.2%}")
        print()


if __name__ == "__main__":
    test_detector()
