"""
Intelligent Cover Letter Generator
=================================
Checks database and generates cover letter only if needed
Memory efficient - loads model only when necessary
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime

# Add data directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
# Try to import database manager, else exit with error
try:
    from data.database_manager import UpworkDatabase

except ImportError:
    print("❌ Cannot import database_manager")
    sys.exit(1)

# Try to import AI model and tokenizer, else exit with error
try:
    import torch
    from transformers import GPT2LMHeadModel, GPT2Tokenizer
    AI_AVAILABLE = True
except ImportError as e:
    print(f"❌ AI libraries not available: {e}")
    sys.exit(1)

# Try to import NLTK for better text processing
try:
    import nltk
    from nltk.tokenize import sent_tokenize
    NLTK_AVAILABLE = True
    
    # Download required NLTK data if not present
    try:
        nltk.data.find('tokenizers/punkt')
    except LookupError:
        print("📥 Downloading NLTK punkt tokenizer...")
        nltk.download('punkt', quiet=True)
    
    # Try newer punkt_tab format
    try:
        nltk.data.find('tokenizers/punkt_tab')
    except LookupError:
        print("📥 Downloading NLTK punkt_tab tokenizer...")
        nltk.download('punkt_tab', quiet=True)
        
except ImportError:
    print("⚠️ NLTK not available, using basic text cleaning")
    NLTK_AVAILABLE = False

# class to call AI model for generating cover letters
# it has functions to 
# 1.  check database and look for jobs without cover letters
# 2.  get latest job without cover letter
# 3.  load model temporarily for generation
# 4.  unload model to free memory
# 5.  generate cover letter for job
class SmartCoverLetterGenerator:
    """Smart cover letter generator that checks if work is needed first"""
    # function to initialize class
    # 1. set model path to trained model
    # 2. set model and tokenizer to None
    # 3. set hardware device to CPU for compatibility
    def __init__(self):
        """Initialize generator"""
        # path to trained model
        self.model_path = "trained_models/advanced_cover_letter_model/final"
        # model and tokenizer placeholders
        self.model = None
        self.tokenizer = None
        # set hardware device to use CPU for hardware compatibility
        self.device = torch.device('cpu')

    # ======= 🔎💼 function to check if cover letter generation is needed ======    
    # connects to database and checks for jobs without cover letters
    # 1. connect to database
    # 2. query jobs table left join cover_letters table on job id
    # 3. count jobs where cover letter is null
    # 4. return boolean if count > 0 and count
    def check_if_cover_letter_needed(self):
        """Check if there are jobs without cover letters"""
        # try to connect to database
        try:
            # variable for database
            db = UpworkDatabase()
            # establish connection to database
            conn = sqlite3.connect(db.db_path)
            # create cursor
            cursor = conn.cursor()
            
            # query to count jobs without cover letters
            # left join jobs as j and cover_letters as cl on job id as FOREIGN KEY
            cursor.execute('''
                SELECT COUNT(*) 
                FROM jobs j
                LEFT JOIN cover_letters cl ON j.id = cl.job_id
                WHERE cl.job_id IS NULL
            ''')
            # fetch first row and first column as count
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0, count
            # If there are no jobs without cover letters, return early
        except Exception as e:
            print(f"❌ Error checking database: {e}")
            return False, 0
    # ======= 🔎📝💼 function to get latest job without cover letter ======
    # 1. connect to database
    # 2. query jobs table left join cover_letters table on job id
    # 3. get latest job row where cover letter is null
    # 4. return job data from database as dictionary
    def get_latest_job_without_cover_letter(self):
        """Get the most recent job without cover letter"""
        try:
            db = UpworkDatabase()
            conn = sqlite3.connect(db.db_path)
            cursor = conn.cursor()
            # query to get latest job without cover letter
            cursor.execute('''
                SELECT j.id, j.job_title, j.job_type, j.budget, j.experience_level, 
                       j.skills, j.description, j.parsed_timestamp
                FROM jobs j
                LEFT JOIN cover_letters cl ON j.id = cl.job_id
                WHERE cl.job_id IS NULL
                ORDER BY j.parsed_timestamp DESC
                LIMIT 1
            ''')
            # fetch first row as latest job without cover letter
            job_row = cursor.fetchone()
            conn.close()
            # return None if no job found
            if not job_row:
                return None
            # return job data as dictionary, of values and rows in database
            return {
                'id': job_row[0],
                'job_title': job_row[1],
                'job_type': job_row[2],
                'budget': job_row[3],
                'experience_level': job_row[4],
                'skills': job_row[5],
                'description': job_row[6],
                'parsed_timestamp': job_row[7]
            }
            
        except Exception as e:
            print(f"❌ Error getting job: {e}")
            return None
    # ======= 🧱🤖 function to load model temporarily ======
    # calls trained model and tokenizer from model_path
    # 1. check if there is a trained model at model_path
    # 2. load tokenizer from model_path
    # 3. load trained model from model_path
    # 4. set model to eval mode
    def load_model_temporarily(self):
        # try to initialize trained model
        try:
            # check if model path exists
            model_path = Path(self.model_path)
            if not model_path.exists():
                print(f"❌ Model not found at {model_path}")
                return False
            
            print(f"🔄 Loading trained model...")
            
            # Load tokenizer
            self.tokenizer = GPT2Tokenizer.from_pretrained(str(model_path))
            # get pad token or fallback to eos token
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
            
            # Fix attention mask issue by explicitly setting pad token
            self.tokenizer.padding_side = "left"

            # Load trained model and set to eval mode
            self.model = GPT2LMHeadModel.from_pretrained(
                str(model_path),
                torch_dtype=torch.float32,
                low_cpu_mem_usage=True
            )
            self.model.eval()
            
            print(f"✅ Model loaded")
            return True
            
        except Exception as e:
            print(f"❌ Error loading model: {e}")
            return False

    # ======= 🗑️🤖 function to unload model ======
    # frees memory by deleting model and tokenizer
    def unload_model(self):
        # check if model and tokenizer are loaded and delete to free memory
        if self.model:
            del self.model
            self.model = None
        if self.tokenizer:
            del self.tokenizer  
            self.tokenizer = None
        print("🗑️ Model memory freed")

    # ======= 🤖📝 function for setting up prompt for better cover letter generation ======
    # takes input job data extracts relevant fields and creates prompt
    # 1. extract job details from get_latest_job_without_cover_letter result
    # 2. create compact prompt with job title, type, budget, skills
    # 3. tokenize with minimal length
    # 4. generate with conservative settings
    # 5. decode response
    # 6. extract cover letter from response
    # 7. call function that cleans up text
    # 8. return cleaned cover letter
    def generate_cover_letter(self, job_data):
        """Generate cover letter for job"""
        # check if model and tokenizer are loaded
        if not self.model or not self.tokenizer:
            print("❌ Model not loaded")
            return None
        
        try:
            # Extract job details from get_latest_job_without_cover_letter result
            job_title = job_data.get('job_title', 'Unknown Position')
            job_type = job_data.get('job_type', 'Project')
            budget = job_data.get('budget', 'Not specified')
            experience_level = job_data.get('experience_level', 'Not specified')
            skills = job_data.get('skills', [])
            
            # Parse skills if JSON string
            if isinstance(skills, str):
                try:
                    skills = json.loads(skills)
                except:
                    skills = []
            # if no skills given place relevant technologies
            skills_str = ', '.join(skills[:3]) if skills else 'relevant technologies'
            
            # Create compact prompt with  get_latest_job_without_cover_letter result fields
            prompt = f"""Job: {job_title}
Type: {job_type}
Budget: {budget}
Skills: {skills_str}

Cover Letter:
Dear Hiring Manager,

I am excited to apply for the {job_title} position."""
            # Log prompt generation
            print(f"🔄 Generating for: {job_title[:40]}...")
            
            # Tokenize with minimal length
            inputs = self.tokenizer(
                prompt,
                return_tensors='pt',
                truncation=True,
                max_length=250,  # Very compact
                padding=True,  # Enable padding
                add_special_tokens=True
            )
            
            # Generate with conservative settings
            with torch.no_grad():
                outputs = self.model.generate(
                    inputs['input_ids'],
                    attention_mask=inputs['attention_mask'],  # Pass attention mask
                    max_length=inputs['input_ids'].shape[1] + 120,  # Only 120 new tokens
                    temperature=0.7,
                    do_sample=True,
                    top_p=0.8,
                    top_k=30,
                    pad_token_id=self.tokenizer.pad_token_id,
                    eos_token_id=self.tokenizer.eos_token_id,
                    repetition_penalty=1.1
                )
            
            # Decode response
            generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract cover letter
            if "Cover Letter:" in generated_text:
                cover_letter = generated_text.split("Cover Letter:")[1].strip()
            else:
                cover_letter = generated_text.strip()
            
            # after extraction call function that cleans up text
            cover_letter = self._clean_text(cover_letter)
            # Log cover letter generation
            print("✅ Cover letter generated")
            # Return the cleaned cover letter
            return cover_letter
            # error handling if generation fails
        except Exception as e:
            print(f"❌ Error generating: {e}")
            return None
    # ======= 🧼📝 function to clean generated text with NLTK ======
    # 1. try to use NLTK to tokenize sentences
    # 2. make array for clean sentences
    # 3. loop through sentences
    # 4. strip whitespace from each sentence
    # 5. less aggressive filtering - keep meaningful sentences longer than 10 characters
    # 6. add to clean sentences
    # 7. take max 6 sentences like basic method
    # 8. fallback to basic cleaning if NLTK fails
    def _clean_text(self, text):
        # calls NLTK to clean text from short or meaningless sentences
        if NLTK_AVAILABLE:
            # Use NLTK for better sentence tokenization
            try:
                # Tokenize text into sentences using NLTK
                sentences = sent_tokenize(text)
                # make array for clean sentences
                clean_sentences = []
                # loop through sentences
                for sentence in sentences:
                    # Strip whitespace from each sentence
                    sentence = sentence.strip()
                    # Less aggressive filtering - keep meaningful sentences longer than 10 characters
                    if sentence and len(sentence) > 10:  # Lower threshold
                        # Remove duplicate whitespace
                        sentence = ' '.join(sentence.split())
                        # add to clean sentences
                        clean_sentences.append(sentence)
                
                # Take max 6 sentences like basic method
                result = '. '.join(clean_sentences[:6])
                # log successful cleaning
            except Exception as e:
                print(f"⚠️ NLTK tokenization failed: {e}, using fallback")
                result = self._basic_clean_text(text)
        else:
            # Fallback to basic cleaning
            result = self._basic_clean_text(text)
        
        # Ensure proper ending
        if result and not result.endswith('.'):
            result += '.'
        
        # Add professional signature if missing
        if not any(phrase in result for phrase in ["Best regards", "Sincerely", "Thank you"]):
            result += "\n\nBest regards,\n[Your Name]"
        
        return result
    # ======= 🧼📝 fallback basic text cleaning method ======
    # 1. split text into sentences
    # 2. make array for clean sentences
    # 3. loop through sentences and strip whitespace
    # 4. less aggressive filtering - keep meaningful sentences longer than 10 characters
    def _basic_clean_text(self, text):
        """Fallback text cleaning method"""
        # split text into sentences
        sentences = text.split('.')
        clean_sentences = []
        
        # loop through sentences if they have more than 10 characters keep them
        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and len(sentence) > 10:
                clean_sentences.append(sentence)
        
        return '. '.join(clean_sentences[:6])  # Max 6 sentences

# ======= 🧠🚀 main function for smart generation ======
# 1. log event
# 2. initialize SmartCoverLetterGenerator class
# 3. check if work is needed with check_if_cover_letter_needed
# 4, extract job data with get_latest_job_without_cover_letter
# 5. load model temporarily with load_model_temporarily
# 6. generate cover letter with generate_cover_letter from job data
# 7. unload model to free memory with unload_model
# 8. save to database with UpworkDatabase class and add_cover_letter function
def smart_generate_cover_letter():
    
    # log event
    print("🧠 SMART COVER LETTER GENERATOR")
    print("===============================")

    # Initialize inside variable class that has functions for smart generation
    generator = SmartCoverLetterGenerator()
    
    # inside variable put
    # 1. boolean if work is needed
    # 2. count of jobs needing cover letters
    needed, count = generator.check_if_cover_letter_needed()
    # If no work
    if not needed:
        print("✅ All jobs already have cover letters - no work needed")
        return True
    # else log count of jobs needing cover letters
    print(f"📋 Found {count} jobs needing cover letters")
    
    # inside variable get latest job without cover letter
    job_data = generator.get_latest_job_without_cover_letter()
    
    if not job_data:
        print("❌ No job found")
        return False
    
    print(f"🎯 Processing: {job_data['job_title']}")
    
    # inside variable Load model
    if not generator.load_model_temporarily():
        print("❌ Failed to load model")
        return False
    
    # inside variable call generate_cover_letter 
    # and eval data extracted by get_latest_job_without_cover_letter
    cover_letter = generator.generate_cover_letter(job_data)
    
    # Immediately unload model to free memory
    generator.unload_model()
    
    if not cover_letter:
        print("❌ Failed to generate cover letter")
        return False
    
    # Save to database with UpworkDatabase class and add_cover_letter function
    try:
        db = UpworkDatabase()
        cover_letter_id = db.add_cover_letter(
            job_id=job_data['id'],
            ai_provider="trained_gpt2_smart",
            cover_letter_text=cover_letter,
            notes=f"Smart generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
        
        print(f"✅ Cover letter saved (ID: {cover_letter_id})")
        print(f"📝 Preview: {cover_letter[:80]}...")
        return True
        
    except Exception as e:
        print(f"❌ Error saving: {e}")
        return False
# main function to call smart cover letter generator function
def main():
    """Main function"""
    success = smart_generate_cover_letter()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()