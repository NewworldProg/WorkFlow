"""
Standalone Phase Detector - Updates database with detected phases
Separates phase detection from response generation for efficiency
"""
import sys
import os
import json
from datetime import datetime

# Set UTF-8 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from data.chat_database_manager import ChatDatabase
from ai.phase_detector import PhaseDetector

class StandalonePhaseDetector:

    # init database and try to load model
    #1. root of database and model
    #2. path to database
    #3. path to model
    #4. put database manager in var
    #5. put model in var
    #6. print metadata info
    def __init__(self):
        # var to hold root dir
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # var to hold db path
        db_path = os.path.join(project_root, "data", "chat_data.db")
        # initialize database
        self.db = ChatDatabase(db_path)
        # var to hold model dir
        model_dir = os.path.join(project_root, "ai", "trained_models", "phase_classifier_v1")
        # log
        print("\n" + "="*60)
        print("STANDALONE PHASE DETECTOR")
        print("="*60)
        # error if model not found
        # check if path to model exists
        if not os.path.exists(model_dir):
            print(f"❌ ERROR: BERT model not found at {model_dir}")
            print(f"   Run: python ai/train_phase_classifier.py")
            print("="*60 + "\n")
            raise FileNotFoundError("BERT model not trained")
        
        try:
            # call PhaseDetector class and load model
            self.phase_detector = PhaseDetector(model_dir)
            print("✅ BERT PHASE DETECTOR LOADED")
            # print model metadata
            print(f"   Accuracy: {self.phase_detector.metadata.get('accuracy')}%")
            print("="*60 + "\n")
            # except on error
        except Exception as e:
            print(f"❌ ERROR loading BERT model: {e}")
            print("="*60 + "\n")
            raise
    # function to call detection and update db
    #1. get latest session from database manager
    #2. get recent messages from database manager
    #3. build context string by adding object fields into one line string for tokenization
    #4. use predict function to get phase and confidence
    #5. update database with detected phase and confidence
    #6. log it
    def detect_and_update_phase(self, session_id='latest'):
        """Detect phase and update database (main function)"""
        # log the session id
        print(f"[PHASE DETECT] Starting detection for session: {session_id}")
        
        # get latest session if 'latest' specified from database manager
        if session_id == 'latest':
            latest = self.db.get_latest_session()
            if latest:
                session_id = latest['session_id']
                print(f"[SESSION] Using latest session: {session_id}")
            else:
                return {'success': False, 'error': 'No active sessions found'}
        # error if no session id
        if not session_id:
            return {'success': False, 'error': 'No session ID provided'}
        
        # Get conversation context limit to last 10 messages
        messages = self.db.get_recent_messages(session_id, limit=10)
        # error if no messages
        if not messages:
            return {'success': False, 'error': f'No messages found for session {session_id}'}

        # from database data make one line string from sender and text objects
        context = "\n".join([f"{m['sender_type']}: {m['text']}" for m in messages])
        # limit context
        context_preview = context[:100] + "..." if len(context) > 100 else context
        
        print(f"[CONTEXT] {len(messages)} messages, {len(context)} chars")
        print(f"[PREVIEW] {context_preview}")
        
        # log that model is analyzing
        print("[BERT] Analyzing conversation phase...")
        # use predict function that sets model to eval the input save output to var
        phase_result = self.phase_detector.predict(context)
        # extract phase and confidence from result
        phase = phase_result['phase']
        confidence = phase_result['confidence']
        # log it
        print(f"[RESULT] Phase: {phase}")
        print(f"[RESULT] Confidence: {confidence:.1%}")
        
        # update database with detected phase and put it in success var
        success = self.db.update_session_phase(session_id, phase, confidence)
        # log success
        if success:
            print(f"[SUCCESS] Database updated with phase: {phase}")
            
            return {
                'success': True,
                'session_id': session_id,
                'phase': phase,
                'confidence': confidence,
                'context_length': len(context),
                'messages_count': len(messages),
                'timestamp': datetime.now().isoformat()
            }
        else:
            return {
                'success': False,
                'error': 'Failed to update database with detected phase'
            }
# use argparse library for starting process from command line
def main():
    """Command line interface"""
    # use argparse library for starting process from command line
    import argparse
    parser = argparse.ArgumentParser(description='Standalone Phase Detector')
    parser.add_argument('--session', default='latest', 
                       help='Session ID to analyze (default: latest)')
    parser.add_argument('--output', default='json',
                       help='Output format: json or simple (default: json)')
    
    args = parser.parse_args()
    
    try:
        detector = StandalonePhaseDetector()
        result = detector.detect_and_update_phase(args.session)
        
        if args.output == 'json':
            print("\n" + "="*60)
            print("PHASE DETECTION RESULT")
            print("="*60)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result['success']:
                print(f"\n✅ Phase: {result['phase']} ({result['confidence']:.1%})")
            else:
                print(f"\n❌ Error: {result['error']}")
                
    except Exception as e:
        error_result = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        
        if args.output == 'json':
            print(json.dumps(error_result, indent=2))
        else:
            print(f"\n❌ Error: {e}")
        
        sys.exit(1)

if __name__ == "__main__":
    main()