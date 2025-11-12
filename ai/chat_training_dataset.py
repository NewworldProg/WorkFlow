"""
Chat Training Dataset Processor
Parses raw chat data and outputs structured JSON for GPT-2 training
"""
import os
import json
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# class for parsing data for chat model training
class ChatDataProcessor:
    """Processes raw chat data into structured JSON format"""
    # build components for processing
    # 1. set input file path
    # 2. make output file name from input file
    # 3. set output file path
    # 4. ensure directories exist
    def __init__(self, input_file=None, output_file=None):
        # set up input file path
        if input_file is None:
            input_file = "ai/training_data/raw_data/chat_conversations_v1.txt"
        # set up output file path
        if output_file is None:
            # from raw data file name make parsed file name addinng _parsed.json instad of .txt
            filename = os.path.basename(input_file).replace('.txt', '_parsed.json')
            # set output file path
            output_file = f"ai/training_data/parsed_data/{filename}"
        
        self.input_file = input_file
        self.output_file = output_file
        
        # Ensure directories exist
        os.makedirs(os.path.dirname(self.output_file), exist_ok=True)
    # function to process chat data like main function
    #     
    def process_chat_data(self):
        """Main function to process chat data and save to JSON"""
        print(f"📚 Processing chat data from: {self.input_file}")
        
        # Check if input file exists
        if not os.path.exists(self.input_file):
            print(f"❌ Input file not found: {self.input_file}")
            print(f"💡 Please place raw chat data in: ai/training_data/raw_data/")
            return None
        
        # read raw chat data and put in var chat_text
        with open(self.input_file, 'r', encoding='utf-8') as f:
            chat_text = f.read()
        # log loaded data length
        print(f"📄 Loaded {len(chat_text)} characters of raw chat data")
        
        # inside var call parse_chat_conversations function to get conversations
        conversations = self.parse_chat_conversations(chat_text)
        print(f"💬 Parsed {len(conversations)} conversation segments")
        
        # in var call create_structured_output to make structured data with inputs
        structured_data = self.create_structured_output(conversations, chat_text)
        
        # Save to JSON
        self.save_to_json(structured_data)
        
        return self.output_file

    # function to parse chat conversations
    # 1. split chat text into lines
    # 2. detect speaker
    #3. make dict with speaker and message as keys
    #4. skip system messages and timestamps
    #5. add messages to current speaker until speaker changes
    #6. split conversations into training segments
    #7. return conversations array with dicts of speaker and message
    def parse_chat_conversations(self, chat_text):
        """Parse chat text into structured conversations"""
        # array to hold all conversations
        conversations = []
        # make an array where one place holde is chat text that split where there is a new line
        lines = chat_text.split('\n')
        # variables to track current conversation
        current_conversation = []
        # variables to track current speaker
        current_speaker = None
        # variable to accumulate current message
        current_message = ""
        
        # loop through each line in chat text
        for line in lines:
            # split line where there are whitespaces to make one line
            line = line.strip()
            if not line:
                continue
                
            # detect speaker and append conversation to him until speaker changes
            # Detect speaker and put it to current_speaker var
            if 'Noel Angeles' in line:
                # if speaker stays the same save message if they exist
                if current_speaker and current_message.strip():
                    # make dict with speaker and message as keys
                    current_conversation.append({
                        'speaker': current_speaker,
                        'message': current_message.strip()
                    })
                    current_message = ""
                current_speaker = 'freelancer'
            # when speaker changes change current_speaker var
            elif 'YM' in line or 'Yuliia M' in line:
                # Save previous message
                if current_speaker and current_message.strip():
                    # make dict with speaker and message as keys
                    current_conversation.append({
                        'speaker': current_speaker,
                        'message': current_message.strip()
                    })
                    current_message = ""
                current_speaker = 'client'
                
            # Skip system messages and timestamps
            elif any(skip_word in line for skip_word in [
                'View details', 'View contract', 'View offer', 'Est. Budget',
                'AM', 'PM', '2025', '.xlsx', '.docx', 'sent an offer',
                'accepted an offer', 'removed this message'
            ]):
                continue
            else:
                # Add to current message to the current speaker
                if line and current_speaker:
                    if current_message:
                        current_message += " " + line
                    else:
                        current_message = line
        
        # Save last message
        if current_speaker and current_message.strip():
            current_conversation.append({
                'speaker': current_speaker,
                'message': current_message.strip()
            })
        
        # Split conversation into training segments
        if current_conversation:
            segments = []
            for i in range(0, len(current_conversation), 3):
                segment = current_conversation[i:i+5]
                if len(segment) >= 2:  # At least 2 messages
                    segments.append(segment)
            conversations.extend(segments)
            
        return conversations
    # function to create structured output
    # 1. make structured data dict with metadata and training conversations array
    # 2. iterate through conversations
    # 3. call format_conversation_for_training to format text
    # 4. only include conversations with 50 + characters
    # 5. create conv_data dict with metadata
    #6. add conv_data to structured_data training_conversations array
    #7. add to valid conversations count
    #8. return structured data
    def create_structured_output(self, conversations, raw_text):
        """Create structured data for JSON output"""
        # structured data dict
        structured_data = {
            # metadata about the processing
            "metadata": {
                "source_file": self.input_file,
                "output_file": self.output_file,
                "processed_on": datetime.now().isoformat(),
                "total_conversations": len(conversations),
                "raw_text_length": len(raw_text),
                "processor_version": "1.0"
            },
            # training conversations data
            "training_conversations": []
        }
        
        # Process each conversation for training
        valid_conversations = 0
        # Iterate through conversations
        for i, conv in enumerate(conversations):
            # call format_conversation_for_training to format text
            formatted_text = self.format_conversation_for_training(conv)
            
            # Only include conversations with 50 + characters
            if len(formatted_text) > 50:
                # Create conve_data dictionary
                conv_data = {
                    # conversation metadata
                    "id": valid_conversations + 1,
                    "exchanges": conv,
                    "formatted_training_text": formatted_text,
                    "exchange_count": len(conv),
                    "speakers": list(set([msg['speaker'] for msg in conv])),
                    "text_length": len(formatted_text)
                }
                # add conv_data to structured_data training_conversations array
                structured_data["training_conversations"].append(conv_data)
                # add to valid conversations count
                valid_conversations += 1
                
                print(f"📝 Conversation {valid_conversations}: {len(conv)} exchanges, {len(formatted_text)} chars")
        # add valid conversations count to metadata
        structured_data["metadata"]["valid_conversations"] = valid_conversations
        print(f"✅ Created {valid_conversations} valid training conversations")
        
        return structured_data
    # function to format conversation for training
    # 1. Initialize formatted text with start token
    # 2. loop throught conversation
    # 3. get speaker and message
    # 4. clean up message
    # 5. add speaker token and message to formatted text
    # 6. add end token at the end
    def format_conversation_for_training(self, conversation):
        """Format conversation for GPT-2 training"""
        # Initialize formatted text with start token
        formatted_text = "<|startoftext|>"
        # loop throught conversation
        for turn in conversation:
            # get speaker and message
            speaker = turn['speaker']
            message = turn['message']
            
            # Clean up message
            message = message.replace('\n', ' ').strip()
            # if speaker is client add client token
            if speaker == 'client':
                formatted_text += f"\n<|client|> {message}"
            # if speaker is freelancer add freelancer token
            else:
                formatted_text += f"\n<|freelancer|> {message}"
        # at the end add end token
        formatted_text += "\n<|endoftext|>"
        return formatted_text
    # function to save structured data to json
    # 1. Open output file with utf-8 encoding and write JSON data
    # 2. in var put metadata and conversations for logging summary
    # 3 . log summary of metadata and conversations
    def save_to_json(self, data):
        """Save structured data to JSON file"""
        # Open output file with utf-8 encoding and and write JSON data
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # log it
        print(f"💾 Structured training data saved to: {self.output_file}")
        
        # in var put metadata
        metadata = data["metadata"]
        # in var put conversations
        conversations = data["training_conversations"]
        #log summary of metadata and conversations
        print(f"\n📊 Processing Summary:")
        print(f"   📁 Input file: {metadata['source_file']}")
        print(f"   📄 Output file: {metadata['output_file']}")
        print(f"   💬 Valid conversations: {metadata['valid_conversations']}")
        print(f"   📝 Raw text length: {metadata['raw_text_length']} chars")
        print(f"   ⏰ Processed on: {metadata['processed_on']}")
        
        if conversations:
            total_text_length = sum(conv['text_length'] for conv in conversations)
            avg_exchanges = sum(conv['exchange_count'] for conv in conversations) / len(conversations)
            print(f"   📊 Total training text: {total_text_length} chars")
            print(f"   📈 Average exchanges per conversation: {avg_exchanges:.1f}")
# function to analyze raw data
# 1. check for file path to training data
# 2. Read raw data content
#3. log data length and sample
#4. Count conversation participants
def analyze_raw_data(file_path):
    """Analyze raw training data before processing"""
    # check for file path to training data
    if not os.path.exists(file_path):
        print(f"❌ Training data not found at: {file_path}")
        return False
    
    print("🔍 Analyzing raw training data...")
    # Read raw data content
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    # log data length and sample
    print(f"📄 Raw data length: {len(content)} characters")
    print(f"📝 First 500 characters:\n{content[:500]}")
    
    # Count conversation participants
    noel_count = content.count("Noel Angeles")
    yuliia_count = content.count("Yuliia M") + content.count("YM")
    
    print(f"\n💬 Speaker analysis:")
    print(f"   👨‍💻 Noel Angeles mentions: {noel_count}")
    print(f"   👩‍💼 Yuliia M mentions: {yuliia_count}")
    print(f"   💫 Total speaker changes: {noel_count + yuliia_count}")
    
    return True
# function to list available files
# 1. var to hold raw_data_dir and parsed_data_dir
# 2. log it
# 3. List raw data files and parsed data files with sizes
def list_available_files():
    """List available raw data files"""
    # var to hold raw_data_dir 
    raw_data_dir = "ai/training_data/raw_data"
    # var to hold parsed_data_dir
    parsed_data_dir = "ai/training_data/parsed_data"
    # log it
    print(f"📂 Available files:")

    # List raw data files
    if os.path.exists(raw_data_dir):
        raw_files = [f for f in os.listdir(raw_data_dir) if f.endswith('.txt')]
        print(f"\n📄 Raw data files in {raw_data_dir}:")
        if raw_files:
            for file in raw_files:
                file_path = os.path.join(raw_data_dir, file)
                size = os.path.getsize(file_path)
                print(f"   - {file} ({size:,} bytes)")
        else:
            print(f"   No .txt files found")
    
    # List parsed data files
    if os.path.exists(parsed_data_dir):
        parsed_files = [f for f in os.listdir(parsed_data_dir) if f.endswith('.json')]
        print(f"\n📊 Parsed data files in {parsed_data_dir}:")
        if parsed_files:
            for file in parsed_files:
                file_path = os.path.join(parsed_data_dir, file)
                size = os.path.getsize(file_path)
                print(f"   - {file} ({size:,} bytes)")
        else:
            print(f"   No .json files found")
# main function to call
def main():
    """Main processing function"""
    try:
        # List available files first
        list_available_files()
        
        # set default input file path
        input_file = "ai/training_data/raw_data/chat_conversations_v1.txt"
        
        print(f"\n🚀 Starting chat data processing...")
        print(f"📁 Looking for input file: {input_file}")
        
        # Check if we have any raw data files
        raw_data_dir = "ai/training_data/raw_data"
        if os.path.exists(raw_data_dir):
            raw_files = [f for f in os.listdir(raw_data_dir) if f.endswith('.txt')]
            if raw_files:
                # Use the first available file if default doesn't exist
                if not os.path.exists(input_file):
                    input_file = os.path.join(raw_data_dir, raw_files[0])
                    print(f"💡 Using available file: {input_file}")
        
        # Analyze raw data first
        if not analyze_raw_data(input_file):
            print(f"\n💡 To add training data:")
            print(f"   1. Place your chat conversation .txt files in: {raw_data_dir}")
            print(f"   2. Run this script again")
            return False
        
        # Process chat data
        processor = ChatDataProcessor(input_file)
        output_path = processor.process_chat_data()
        
        if output_path:
            print(f"\n🎉 Processing completed successfully!")
            print(f"📄 Processed data available at: {output_path}")
            print(f"🔄 Ready for GPT-2 training!")
            print(f"📋 Next step: python ai/train_chat_gpt2.py")
        
        return output_path is not None
        
    except Exception as e:
        print(f"❌ Processing failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    print(f"\n{'✅ Processing successful!' if success else '❌ Processing failed!'}")
