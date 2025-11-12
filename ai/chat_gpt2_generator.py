"""
Simplified ChatGPT2Generator - Lightweight GPT-2 for SmartChatResponse
"""
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import json
import os
from datetime import datetime

class ChatGPT2Generator:
    def __init__(self):
        print("Loading GPT-2...")
        self.tokenizer = GPT2Tokenizer.from_pretrained("gpt2")
        self.model = GPT2LMHeadModel.from_pretrained("gpt2")
        
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.model.to(self.device)
        self.model.eval()
        print("✅ GPT-2 Ready")
    
    def generate_response(self, session_id, custom_prompt=None, response_type="professional"):
        """Generate AI response - simplified for SmartChatResponse"""
        try:
            if not custom_prompt:
                return {
                    'success': False,
                    'error': 'No prompt provided',
                    'responses': ["Thank you for your message."]
                }
            
            # Use custom_prompt AS-IS (from SmartChatResponse)
            response = self.generate_single_response(custom_prompt)
            
            return {
                'success': True,
                'session_id': session_id,
                'responses': [response] if response else ["Thank you for your message."],
                'model_used': 'gpt2-simplified'
            }
            
        except Exception as e:
            return {
                'success': False, 
                'error': str(e),
                'responses': ["Thank you for your message."]
            }
    
    def generate_single_response(self, prompt, max_length=80):
        """Simple GPT-2 text generation"""
        try:
            inputs = self.tokenizer.encode(prompt, return_tensors='pt').to(self.device)
            
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs,
                    max_length=inputs.shape[1] + max_length,
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.9,
                    pad_token_id=self.tokenizer.eos_token_id,
                    no_repeat_ngram_size=2
                )
            
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            response = generated_text[len(prompt):].strip()
            
            # Simple cleanup
            if not response.endswith(('.', '!', '?')) and len(response) > 10:
                response = response.rsplit(' ', 1)[0] + '.'
            
            return response[:150] if len(response) > 150 else response
            
        except Exception as e:
            print(f"GPT-2 Error: {e}")
            return "Thank you for your message."

# Keep original main() for backward compatibility
def main():
    """Backward compatibility main function"""
    import argparse
    parser = argparse.ArgumentParser(description='Simplified GPT-2 Chat Generator')
    parser.add_argument('--session-id', required=True, help='Chat session ID')
    parser.add_argument('--type', default='professional', help='Response type')
    parser.add_argument('--prompt', help='Custom prompt')
    
    args = parser.parse_args()
    
    try:
        generator = ChatGPT2Generator()
        result = generator.generate_response(
            session_id=args.session_id,
            custom_prompt=args.prompt,
            response_type=args.type
        )
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result.get('success', False)
        
    except Exception as e:
        result = {'success': False, 'error': str(e)}
        print(json.dumps(result))
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)