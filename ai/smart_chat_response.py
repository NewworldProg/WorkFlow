"""
Smart Chat Response Generator - CLEAN VERSION
Phase Detection: BERT AI only (no keywords, no fallbacks)
Response Modes: Template OR AI (GPT-2)
"""
import sys
import os
import json
import argparse
from datetime import datetime

# Set UTF-8 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path and import database manager
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from data.chat_database_manager import ChatDatabase

#class to hold templates and generate responses based on phase
class SmartChatResponse:
    """Simple phase-based response generator with BERT AI"""

    # templates dict for each phase (detected by BERT AI)
    TEMPLATES = {
        'initial_response': [
            "Thank you for reaching out! I'm very interested. Could you tell me more about the project?",
            "Good day! I'm available. What are the main deliverables?",
            "Hello! I'd be happy to help. Can you share more details?"
        ],
        'ask_details': [
            "Could you provide more details about the project scope?",
            "What specific requirements do you have in mind?",
            "I'd love to learn more about what you're looking for!"
        ],
        'knowledge_check': [
            "Yes, I have extensive experience with that topic. Let me show you my expertise.",
            "Absolutely! I'm well-versed in that area. Would you like some examples?",
            "I'm confident in handling that subject. What specific aspects interest you?"
        ],
        'language_confirm': [
            "I'm fluent in both languages. Which would you prefer for this project?",
            "I can work in either language comfortably. What's your preference?",
            "Both languages work for me. Which fits your target audience better?"
        ],
        'rate_negotiation': [
            "That rate works perfectly for me. When can we start?",
            "I'm comfortable with that pricing. What's the next step?",
            "Great! That rate is acceptable. Should we proceed with the contract?"
        ],
        'deadline_samples': [
            "Absolutely! I can deliver by that deadline. Should I start immediately?",
            "Yes, that timeline works perfectly. I'll prioritize your project.",
            "I can definitely meet that deadline. Let's get started!"
        ],
        'structure_clarification': [
            "Perfect! I understand the structure requirements. I'll follow that format exactly.",
            "Got it! I'll include all those elements in the proper structure.",
            "Understood! I'll make sure each piece follows that exact format."
        ],
        'contract_acceptance': [
            "Contract accepted! Starting work now. You'll have it by the deadline.",
            "Thank you! I've accepted and will begin immediately.",
            "Great! Contract signed. I'm diving into the first batch now."
        ],
        'scope_clarification': [
            "Thank you! Could you clarify: which language(s) and how many words per week?",
            "Great! What language and what's the expected weekly volume?",
            "Perfect! What language? How many articles per week?"
        ],
        'timeline_discussion': [
            "Perfect! When would you need the first delivery?",
            "Got it! What's your preferred timeline for completion?",
            "Understood! When is the deadline? I can start immediately."
        ],
        'requirements_discussion': [
            "Could you share the content structure requirements? (H1, H2s, SEO, etc.)",
            "Do you have specific formatting requirements?",
            "What structure do you prefer for the articles?"
        ],
        'project_acceptance': [
            "Contract accepted! Starting work now. You'll have it by the deadline.",
            "Thank you! I've accepted and will begin immediately.",
            "Great! Contract signed. I'm diving into the first batch now."
        ],
        'follow_up': [
            "Just checking in - do you need any clarifications?",
            "Let me know if you have any questions!",
            "Feel free to reach out if you need anything!"
        ],
        'general_inquiry': [
            "Could you provide more details about what you're looking for?",
            "I'd be glad to assist! Can you clarify what you need?",
            "Let me know the specifics and I'll help!"
        ]
    }


    # initialize database manager
    def __init__(self):
        """Initialize response generator (no phase detection)"""
        # var to hold project root
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # var to hold path to database
        db_path = os.path.join(project_root, "data", "chat_data.db")
        # var for database
        self.db = ChatDatabase(db_path)
        
        print("\n" + "="*60)
        print("INITIALIZING SMART CHAT RESPONSE")
        print("="*60)
        print("✅ RESPONSE GENERATOR ACTIVE")
        print("   Phase detection: Standalone (from database)")
        print("   Template responses: 8 phases")
        print("   AI responses: GPT-2")
        print("="*60 + "\n")
        
        print("="*60 + "\n")
    # get conversation context from database or retrun empty
    def get_context(self, session_id, max_messages=10):
        """Get conversation context from database"""
        if session_id == "latest":
            latest = self.db.get_latest_session()
            session_id = latest['session_id'] if latest else None
        
        if not session_id:
            return "", None
        # get recent messages
        messages = self.db.get_recent_messages(session_id, limit=max_messages)
        context = "\n".join([f"{m['sender_type']}: {m['text']}" for m in messages])
        return context, session_id

    # function that takes phase as input and generates template responses based on phase
    def generate_template_response(self, phase, num_options=3):
        """Generate template responses"""
        templates = self.TEMPLATES.get(phase, self.TEMPLATES['general_inquiry'])
        return templates[:min(num_options, len(templates))]
    # function to save results to temp file for dashboard
    #1. var to hold temp file path
    #2. temp data structure compatible with dashboard to hold suggestions
    #3. based on result content append appropriate fields to temp_data
    def save_to_temp_file(self, result):
        """Save results to temp file for dashboard"""
        try:
            # path to temp file
            temp_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_ai_suggestions.json')

            # Create temp data structure compatible with dashboard to hold suggestions
            temp_data = {
                'session_id': result['session_id'],
                'phase': result['phase'],
                'confidence': result['confidence'],
                'model_used': 'bert_phase_detector',
                'created_at': datetime.now().isoformat()
            }
            # append temp_data with responses
            # if smart_chat_response.generate() was set to return both template and AI append both
            if 'template_response' in result and 'ai_response' in result:
                # Both mode
                temp_data['suggestion_type'] = 'both'
                temp_data['template_response'] = result['template_response']
                temp_data['ai_response'] = result['ai_response']
            # else append one or the other
            elif 'responses' in result:
                # Template or AI mode
                temp_data['suggestion_type'] = result.get('mode', 'template')
                temp_data['responses'] = result['responses']
            
            # Save to file
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(temp_data, f, ensure_ascii=False, indent=2)
            # log it  
            print(f"[SAVE] Results saved to temp_ai_suggestions.json")
            
        except Exception as e:
            print(f"[WARN] Failed to save temp file: {e}")

    # function that takes phase as input and generates AI response using GPT-2
    
    def generate_ai_response(self, phase, context, session_id):
        """Generate AI response using GPT-2"""
        try:
            # 
            from ai.chat_gpt2_generator import ChatGPT2Generator
            gpt2 = ChatGPT2Generator()
            
            # Create detailed prompt for better GPT-2 response
            prompt = f"""You are a professional freelancer responding to a client in an Upwork chat conversation.

CONVERSATION CONTEXT:
{context[-500:]}

AI PHASE DETECTION RESULT:
The AI system has analyzed this conversation and detected that the client is in the "{phase}" phase.

PHASE MEANINGS:
- initial_response: Client is asking if you're available for work
- ask_details: Client wants more information about project scope  
- knowledge_check: Client is testing your expertise in specific topics
- language_confirm: Client is asking about language preferences
- rate_negotiation: Client is discussing pricing and budget
- deadline_samples: Client is asking about delivery timelines
- structure_clarification: Client wants to know about content format/structure
- contract_acceptance: Client is ready to hire and wants you to accept contract

YOUR TASK:
Write a professional, friendly response that addresses the "{phase}" phase appropriately. 
- Keep it concise (1-3 sentences)
- Sound natural and conversational
- Be enthusiastic and professional
- Directly address what the client needs in this phase

Response:"""
            
            result = gpt2.generate_response(
                session_id=session_id,
                custom_prompt=prompt,
                response_type='professional'
            )
            
            if result.get('success') and result.get('responses'):
                return result['responses'][0]
            else:
                return self.generate_template_response(phase, 1)[0]
        except Exception as e:
            print(f"[WARN] GPT-2 failed: {e}")
            return self.generate_template_response(phase, 1)[0]
    
    def generate(self, session_id='latest', mode='template', num_options=3):
        """
        Main generation function - NEW VERSION
        
        1. Get session with pre-detected phase from database
        2. Generate response based on mode (template or AI)
        3. NO phase detection here - phase must be detected first!
        """
        
        # Get session with phase from database
        if session_id == 'latest':
            latest = self.db.get_latest_session()
            if latest:
                session_id = latest['session_id']
            else:
                return {'success': False, 'error': 'No active sessions found'}
        
        if not session_id:
            return {'success': False, 'error': 'No session ID provided'}
        
        # Get session with phase (NO PHASE DETECTION HERE!)
        session_data = self.db.get_session_with_phase(session_id)
        
        if not session_data:
            return {'success': False, 'error': f'Session {session_id} not found'}
        
        if not session_data.get('phase'):
            return {
                'success': False, 
                'error': 'Phase not detected yet. Run standalone phase detector first.',
                'session_id': session_id
            }
        
        phase = session_data['phase']
        confidence = session_data['phase_confidence']
        
        print(f"\n[PHASE] {phase} ({confidence:.1%} confidence) - from database")
        print(f"[SESSION] {session_id}")
        
        # Get context for AI generation (if needed)
        if mode in ['ai', 'both']:
            messages = self.db.get_recent_messages(session_id, limit=10)
            context = "\n".join([f"{m['sender_type']}: {m['text']}" for m in messages])
        else:
            context = ""
        
        # Generate response based on mode (NO phase detection!)
        if mode == 'template':
            responses = self.generate_template_response(phase, num_options)
            print(f"[MODE] Template ({len(responses)} options)")
        elif mode == 'ai':
            ai_response = self.generate_ai_response(phase, context, session_id)
            responses = [ai_response]
            print(f"[MODE] AI (GPT-2)")
        elif mode == 'both':
            template_response = self.generate_template_response(phase, 1)[0]
            ai_response = self.generate_ai_response(phase, context, session_id)
            print(f"[MODE] Both (Template + AI)")
            result = {
                'success': True,
                'phase': phase,
                'confidence': confidence,
                'template_response': template_response,
                'ai_response': ai_response,
                'session_id': session_id
            }
            # Save to temp file for dashboard
            self.save_to_temp_file(result)
            return result
        else:
            return {'success': False, 'error': f'Invalid mode: {mode}'}
        
        result = {
            'success': True,
            'session_id': session_id,
            'mode': mode,
            'phase': phase,
            'confidence': confidence,
            'responses': responses,
            'timestamp': datetime.now().isoformat()
        }
        
        # Save to temp file for dashboard
        self.save_to_temp_file(result)
        return result

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Smart Chat Response')
    parser.add_argument('--session-id', default='latest')
    parser.add_argument('--mode', choices=['template', 'ai', 'both'], default='template')
    parser.add_argument('--num-options', type=int, default=3)
    
    args = parser.parse_args()
    
    try:
        generator = SmartChatResponse()
        result = generator.generate(args.session_id, args.mode, args.num_options)
        
        print("\n" + "="*60)
        if result['success']:
            print(f"Phase: {result['phase']} ({result['confidence']:.1%})")
            
            if args.mode == 'both':
                print(f"\nTemplate Response:")
                print(f"• {result['template_response']}\n")
                print(f"AI Response:")
                print(f"• {result['ai_response']}\n")
            else:
                print(f"\nResponses:\n")
                for i, resp in enumerate(result['responses'], 1):
                    print(f"{i}. {resp}\n")
        else:
            print(f"Error: {result['error']}")
        print("="*60)
        
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0 if result['success'] else 1
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
