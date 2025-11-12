"""
Interactive Chat Dashboard Generator
Creates HTML dashboard with chat data and AI responses
"""
import sys
import os
import json
import argparse
from datetime import datetime

# Set UTF-8 encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from data.chat_database_manager import ChatDatabase

class ChatDashboardGenerator:
    def __init__(self):
        # Use same database path as AI system
        import os
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        db_path = os.path.join(project_root, "data", "chat_data.db")
        self.db = ChatDatabase(db_path)
    
    def generate_dashboard(self, session_id=None):
        """Generate interactive dashboard HTML"""
        try:
            # Get dashboard data
            dashboard_data = self.db.get_dashboard_data()
            print(f"Dashboard data keys: {list(dashboard_data.keys())}")
            
            # Load temporary AI suggestions if they exist
            temp_ai_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_ai_suggestions.json')
            ai_suggestions = []
            if os.path.exists(temp_ai_file):
                try:
                    with open(temp_ai_file, 'r', encoding='utf-8') as f:
                        temp_suggestions = json.load(f)
                        
                        # Check if it's multi-mode format (new)
                        if 'all_modes' in temp_suggestions:
                            # New format with all 4 modes
                            print("[INFO] Loading multi-mode AI suggestions")
                            ai_suggestions = [{
                                'session_id': temp_suggestions.get('session_id', 'unknown'),
                                'suggestion_type': 'all-modes',
                                'confidence': temp_suggestions.get('confidence', 0.0),
                                'generated_at': temp_suggestions.get('created_at', datetime.now().isoformat()),
                                'all_modes': temp_suggestions.get('all_modes', {}),
                                'phase': temp_suggestions.get('phase', 'Unknown'),
                                'model_used': temp_suggestions.get('model_used', 'unknown'),
                                'detection_method': temp_suggestions.get('detection_method', 'unknown'),
                                'total_options': temp_suggestions.get('total_options', 0),
                                'used': False
                            }]
                        elif 'template_response' in temp_suggestions and 'ai_response' in temp_suggestions:
                            # New "both" format with template and AI responses
                            print("[INFO] Loading 'both' mode AI suggestions (Template + AI)")
                            ai_suggestions = [{
                                'session_id': temp_suggestions.get('session_id', 'unknown'),
                                'suggestion_type': 'both',
                                'confidence': temp_suggestions.get('confidence', 0.0),
                                'generated_at': temp_suggestions.get('created_at', datetime.now().isoformat()),
                                'template_response': temp_suggestions.get('template_response', ''),
                                'ai_response': temp_suggestions.get('ai_response', ''),
                                'phase': temp_suggestions.get('phase', 'Unknown'),
                                'model_used': temp_suggestions.get('model_used', 'unknown'),
                                'used': False
                            }]
                        else:
                            # Old format with single mode
                            print("[INFO] Loading single-mode AI suggestions")
                            ai_suggestions = [{
                                'session_id': temp_suggestions.get('session_id', 'unknown'),
                                'suggestion_type': temp_suggestions.get('suggestion_type', 'unknown'),
                                'confidence': temp_suggestions.get('confidence', 0.0),
                                'generated_at': temp_suggestions.get('created_at', datetime.now().isoformat()),
                                'responses': temp_suggestions.get('responses', []),
                                'used': False
                            }] if temp_suggestions.get('responses') else []
                except Exception as e:
                    print(f"[ERROR] Error loading temp AI suggestions: {e}")
                    ai_suggestions = []
            
            # Replace recent_responses with temp AI suggestions
            dashboard_data['recent_responses'] = ai_suggestions
            print(f"AI suggestions loaded: {len(ai_suggestions)}")
            
            if not dashboard_data:
                return self.generate_empty_dashboard()
            
            # Generate HTML
            print("Creating dashboard HTML...")
            html_content = self.create_dashboard_html(dashboard_data)
            
            # Save to file
            dashboard_path = os.path.join(os.path.dirname(__file__), 'chat_dashboard.html')
            
            with open(dashboard_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            print(f"[OK] Dashboard generated: {dashboard_path}")
            
            return {
                'success': True,
                'dashboard_path': dashboard_path,
                'sessions_count': len(dashboard_data['active_sessions']),
                'total_messages': dashboard_data['stats']['total_messages'],
                'ai_suggestions': len(dashboard_data['recent_responses']),
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"[ERROR] Dashboard generation error: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_dashboard_html(self, data):
        """Create the complete dashboard HTML"""
        
        sessions_html = self.generate_sessions_html(data['active_sessions'])
        ai_suggestions_html = self.generate_ai_suggestions_html(data['recent_responses'])
        stats_html = self.generate_stats_html(data)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chat AI Assistant Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .dashboard-container {{
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
        }}
        
        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.2);
        }}
        
        .header .subtitle {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        
        .refresh-button {{
            position: absolute;
            top: 30px;
            right: 180px;
            background: rgba(255, 255, 255, 0.2);
            border: 2px solid rgba(255, 255, 255, 0.3);
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            transition: all 0.3s ease;
        }}
        
        .continue-workflow-button {{
            position: absolute;
            top: 30px;
            right: 30px;
            background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
            border: none;
            color: white;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            font-size: 1em;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(67, 233, 123, 0.3);
        }}
        
        .continue-workflow-button:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(67, 233, 123, 0.4);
        }}
        
        .refresh-button:hover {{
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
        }}
        
        .continue-button {{
            position: absolute;
            top: 30px;
            left: 30px;
            background: #28a745;
            border: none;
            color: white;
            padding: 12px 25px;
            border-radius: 25px;
            cursor: pointer;
            font-weight: bold;
            font-size: 16px;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(40, 167, 69, 0.3);
        }}
        
        .continue-button:hover {{
            background: #218838;
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(40, 167, 69, 0.4);
        }}
        
        .dashboard-content {{
            padding: 30px;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 100%);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            color: white;
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            font-size: 1.1em;
            opacity: 0.9;
        }}
        
        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 30px;
            margin-top: 30px;
        }}
        
        .section {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
        }}
        
        .section h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
            border-bottom: 3px solid #4facfe;
            padding-bottom: 10px;
        }}
        
        .session-item {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            margin-bottom: 15px;
            border-left: 4px solid #4facfe;
            transition: all 0.3s ease;
        }}
        
        .session-item:hover {{
            background: #e9ecef;
            transform: translateX(5px);
        }}
        
        .session-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .session-title {{
            font-weight: bold;
            color: #333;
            font-size: 1.1em;
        }}
        
        .platform-badge {{
            background: #4facfe;
            color: white;
            padding: 4px 12px;
            border-radius: 15px;
            font-size: 0.8em;
            text-transform: uppercase;
        }}
        
        .session-details {{
            color: #666;
            margin-bottom: 10px;
        }}
        
        .message-preview {{
            background: white;
            padding: 10px;
            border-radius: 8px;
            border-left: 3px solid #28a745;
            font-style: italic;
            max-height: 60px;
            overflow: hidden;
        }}
        
        .ai-suggestion {{
            background: #fff3cd;
            border: 1px solid #ffeaa7;
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
            position: relative;
        }}
        
        .ai-suggestion .suggestion-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }}
        
        .confidence-badge {{
            background: #28a745;
            color: white;
            padding: 4px 10px;
            border-radius: 12px;
            font-size: 0.8em;
        }}
        
        .response-options {{
            margin-top: 10px;
        }}
        
        .response-option {{
            background: white;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 12px;
            margin-bottom: 8px;
            cursor: pointer;
            transition: all 0.3s ease;
        }}
        
        .response-option:hover {{
            background: #f0f8ff;
            border-color: #4facfe;
            transform: translateX(5px);
        }}
        
        .timestamp {{
            color: #888;
            font-size: 0.9em;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }}
        
        .empty-state h3 {{
            font-size: 1.5em;
            margin-bottom: 15px;
        }}
        
        .loading {{
            display: none;
            text-align: center;
            padding: 20px;
        }}
        
        .spinner {{
            border: 4px solid #f3f3f3;
            border-top: 4px solid #4facfe;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }}
        
        @keyframes spin {{
            0% {{ transform: rotate(0deg); }}
            100% {{ transform: rotate(360deg); }}
        }}
        
        @media (max-width: 768px) {{
            .main-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .continue-button, .refresh-button {{
                position: static;
                margin: 10px;
            }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-container">
        <div class="header">
            <button class="continue-button" onclick="continueWorkflow()">🔄 Continue Workflow</button>
            <button class="refresh-button" onclick="refreshDashboard()">🔄 Refresh</button>
            <button class="continue-workflow-button" onclick="continueWorkflow()">▶️ Continue Workflow</button>
            <h1>🤖 Chat AI Assistant Dashboard</h1>
            <div class="subtitle">Real-time chat monitoring with AI response suggestions</div>
        </div>
        
        <div class="dashboard-content">
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Loading dashboard data...</p>
            </div>
            
            {stats_html}
            
            <div class="main-grid">
                <div class="section">
                    <h2>📱 Active Chat Sessions</h2>
                    {sessions_html}
                </div>
                
                <div class="section">
                    <h2>🧠 AI Response Suggestions</h2>
                    {ai_suggestions_html}
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function refreshDashboard() {{
            document.getElementById('loading').style.display = 'block';
            setTimeout(() => {{
                window.location.reload();
            }}, 1000);
        }}
        
        function continueWorkflow() {{
            document.getElementById('loading').style.display = 'block';
            
            // Simple approach: show message and user can manually trigger
            alert('Continue Workflow triggered! Please run the Chat AI workflow again in n8n, or execute: run_continue_chat_workflow.ps1');
            
            // Auto-refresh in 3 seconds to check for updates
            setTimeout(() => {{
                refreshDashboard();
            }}, 3000);
        }}
        
        function copyResponse(text) {{
            navigator.clipboard.writeText(text).then(() => {{
                alert('Response copied to clipboard!');
            }});
        }}
        
        // Auto-refresh every 30 seconds
        setInterval(() => {{
            if (!document.getElementById('loading').style.display || 
                document.getElementById('loading').style.display === 'none') {{
                refreshDashboard();
            }}
        }}, 30000);
        
        // Hide loading on page load
        window.addEventListener('load', () => {{
            document.getElementById('loading').style.display = 'none';
        }});
    </script>
</body>
</html>"""
        
        return html
    
    def generate_stats_html(self, data):
        """Generate statistics HTML section"""
        stats = data.get('stats', {})
        total_sessions = stats.get('total_sessions', 0)
        total_messages = stats.get('total_messages', 0)
        total_suggestions = stats.get('total_ai_responses', 0)
        used_responses = stats.get('used_responses', 0)
        
        avg_confidence = 0
        if data['recent_responses']:
            avg_confidence = sum(s['confidence'] for s in data['recent_responses']) / len(data['recent_responses'])
        
        return f"""
        <div class="stats-grid">
            <div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
                <div class="stat-number">{total_sessions}</div>
                <div class="stat-label">Active Sessions</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);">
                <div class="stat-number">{total_messages}</div>
                <div class="stat-label">Total Messages</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);">
                <div class="stat-number">{total_suggestions}</div>
                <div class="stat-label">AI Suggestions</div>
            </div>
            <div class="stat-card" style="background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%);">
                <div class="stat-number">{avg_confidence:.1f}</div>
                <div class="stat-label">Avg Confidence</div>
            </div>
        </div>
        """
    
    def generate_sessions_html(self, sessions):
        """Generate sessions HTML section"""
        if not sessions:
            return """
            <div class="empty-state">
                <h3>No Active Sessions</h3>
                <p>Start a chat conversation to see sessions here.</p>
            </div>
            """
        
        sessions_html = ""
        for session in sessions[-10:]:  # Last 10 sessions
            # Get latest message
            latest_message = ""
            if session.get('messages'):
                latest_message = session['messages'][-1]['text'][:100] + "..." if len(session['messages'][-1]['text']) > 100 else session['messages'][-1]['text']
            
            time_ago = self.time_ago(session.get('last_activity', datetime.now().isoformat()))
            
            sessions_html += f"""
            <div class="session-item">
                <div class="session-header">
                    <div class="session-title">{session['title']}</div>
                    <div class="platform-badge">{session['platform']}</div>
                </div>
                <div class="session-details">
                    <strong>Participant:</strong> {session['participant']} | 
                    <strong>Messages:</strong> {session['total_messages']} |
                    <span class="timestamp">{time_ago}</span>
                </div>
                {f'<div class="message-preview">"{latest_message}"</div>' if latest_message else ''}
            </div>
            """
        
        return sessions_html
    
    def generate_ai_suggestions_html(self, suggestions):
        """Generate AI suggestions HTML section"""
        if not suggestions:
            return """
            <div class="empty-state">
                <h3>No AI Suggestions</h3>
                <p>AI suggestions will appear here as conversations progress.</p>
            </div>
            """
        
        suggestions_html = ""
        for suggestion in suggestions[-5:]:  # Last 5 suggestions
            time_ago = self.time_ago(suggestion['generated_at'])
            
            # Check if this is multi-mode format
            if 'all_modes' in suggestion:
                # Multi-mode format - show all 4 modes
                all_modes = suggestion['all_modes']
                phase = suggestion.get('phase', 'Unknown Phase')
                detection_method = suggestion.get('detection_method', 'unknown')
                
                responses_html = f"""
                <div style="margin-bottom: 15px; padding: 10px; background: #e3f2fd; border-radius: 8px;">
                    <strong>📊 Detected Phase:</strong> {phase} 
                    <span style="color: #666; font-size: 0.9em;">({detection_method})</span><br>
                    <strong>🎯 Total Options:</strong> {suggestion.get('total_options', 0)} responses across 4 modes
                </div>
                """
                
                # Template mode
                if 'template' in all_modes:
                    mode = all_modes['template']
                    responses_html += f"""
                    <div style="margin: 15px 0; padding: 15px; background: #f1f8e9; border-left: 4px solid #8bc34a; border-radius: 8px;">
                        <strong>✅ {mode['mode_name']}</strong> 
                        <span style="color: #666;">({mode['speed']})</span><br>
                        <em style="color: #666; font-size: 0.9em;">{mode['description']}</em>
                        <div style="margin-top: 10px;">
                    """
                    for i, response in enumerate(mode['responses'][:3], 1):
                        responses_html += f"""
                        <div class="response-option" onclick="copyResponse('{response.replace("'", "\\'")}')">
                            <strong>Option {i}:</strong> {response}
                        </div>
                        """
                    responses_html += "</div></div>"
                
                # Hybrid mode
                if 'hybrid' in all_modes:
                    mode = all_modes['hybrid']
                    responses_html += f"""
                    <div style="margin: 15px 0; padding: 15px; background: #fff3e0; border-left: 4px solid #ff9800; border-radius: 8px;">
                        <strong>🔗 {mode['mode_name']}</strong> 
                        <span style="color: #666;">({mode['speed']})</span><br>
                        <em style="color: #666; font-size: 0.9em;">{mode['description']}</em>
                        <div style="margin-top: 10px;">
                    """
                    for i, response in enumerate(mode['responses'][:1], 1):
                        responses_html += f"""
                        <div class="response-option" onclick="copyResponse('{response.replace("'", "\\'")}')">
                            <strong>Option {i}:</strong> {response}
                        </div>
                        """
                    responses_html += "</div></div>"
                
                # Pure AI mode
                if 'pure' in all_modes:
                    mode = all_modes['pure']
                    responses_html += f"""
                    <div style="margin: 15px 0; padding: 15px; background: #f3e5f5; border-left: 4px solid #9c27b0; border-radius: 8px;">
                        <strong>🤖 {mode['mode_name']}</strong> 
                        <span style="color: #666;">({mode['speed']})</span><br>
                        <em style="color: #666; font-size: 0.9em;">{mode['description']}</em>
                        <div style="margin-top: 10px;">
                    """
                    for i, response in enumerate(mode['responses'][:1], 1):
                        responses_html += f"""
                        <div class="response-option" onclick="copyResponse('{response.replace("'", "\\'")}')">
                            <strong>Option {i}:</strong> {response}
                        </div>
                        """
                    responses_html += "</div></div>"
                
                # Summary mode
                if 'summary' in all_modes:
                    mode = all_modes['summary']
                    responses_html += f"""
                    <div style="margin: 15px 0; padding: 15px; background: #e1f5fe; border-left: 4px solid #03a9f4; border-radius: 8px;">
                        <strong>📝 {mode['mode_name']}</strong> 
                        <span style="color: #666;">({mode['speed']})</span><br>
                        <em style="color: #666; font-size: 0.9em;">{mode['description']}</em>
                        <div style="margin-top: 10px;">
                    """
                    for i, response in enumerate(mode['responses'][:1], 1):
                        responses_html += f"""
                        <div class="response-option" onclick="copyResponse('{response.replace("'", "\\'")}')">
                            <strong>Option {i}:</strong> {response}
                        </div>
                        """
                    responses_html += "</div></div>"
                
                suggestions_html += f"""
                <div class="ai-suggestion">
                    <div class="suggestion-header">
                        <strong>All Response Modes</strong>
                        <div class="confidence-badge">{suggestion['confidence']:.1%}</div>
                    </div>
                    <div class="timestamp">{time_ago}</div>
                    <div class="response-options">
                        {responses_html}
                    </div>
                </div>
                """
            elif suggestion['suggestion_type'] == 'both':
                # New "both" format with template and AI responses
                phase = suggestion.get('phase', 'Unknown Phase')
                model_used = suggestion.get('model_used', 'unknown')
                
                responses_html = f"""
                <div style="margin-bottom: 15px; padding: 10px; background: #e3f2fd; border-radius: 8px;">
                    <strong>📊 Detected Phase:</strong> {phase} 
                    <span style="color: #666; font-size: 0.9em;">({model_used})</span><br>
                    <strong>🎯 Response Modes:</strong> Template + AI Comparison
                </div>
                """
                
                # Template response
                template_response = suggestion.get('template_response', '')
                if template_response:
                    responses_html += f"""
                    <div style="margin: 15px 0; padding: 15px; background: #f1f8e9; border-left: 4px solid #8bc34a; border-radius: 8px;">
                        <strong>✅ Template Response</strong> 
                        <span style="color: #666;">(Pre-written Professional)</span><br>
                        <div style="margin-top: 10px;">
                            <div class="response-option" onclick="copyResponse('{template_response.replace("'", "\\'")}')">
                                <strong>Template:</strong> {template_response}
                            </div>
                        </div>
                    </div>
                    """
                
                # AI response
                ai_response = suggestion.get('ai_response', '')
                if ai_response:
                    responses_html += f"""
                    <div style="margin: 15px 0; padding: 15px; background: #f3e5f5; border-left: 4px solid #9c27b0; border-radius: 8px;">
                        <strong>🤖 AI Response</strong> 
                        <span style="color: #666;">(GPT-2 Generated)</span><br>
                        <div style="margin-top: 10px;">
                            <div class="response-option" onclick="copyResponse('{ai_response.replace("'", "\\'")}')">
                                <strong>AI:</strong> {ai_response}
                            </div>
                        </div>
                    </div>
                    """
                
                suggestions_html += f"""
                <div class="ai-suggestion">
                    <div class="suggestion-header">
                        <strong>Template + AI Responses</strong>
                        <div class="confidence-badge">{suggestion['confidence']:.1%}</div>
                    </div>
                    <div class="timestamp">{time_ago}</div>
                    <div class="response-options">
                        {responses_html}
                    </div>
                </div>
                """
            else:
                # Old single-mode format
                responses_html = ""
                for i, response in enumerate(suggestion.get('responses', [])[:3], 1):
                    responses_html += f"""
                    <div class="response-option" onclick="copyResponse('{response.replace("'", "\\'")}')">
                        <strong>Option {i}:</strong> {response}
                    </div>
                    """
                
                suggestions_html += f"""
                <div class="ai-suggestion">
                    <div class="suggestion-header">
                        <strong>Type: {suggestion['suggestion_type'].title()}</strong>
                        <div class="confidence-badge">{suggestion['confidence']:.1f}</div>
                    </div>
                    <div class="timestamp">{time_ago}</div>
                    <div class="response-options">
                        {responses_html}
                    </div>
                </div>
                """
        
        return suggestions_html
    
    def time_ago(self, timestamp_str):
        """Calculate time ago string"""
        try:
            if isinstance(timestamp_str, str):
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            else:
                timestamp = timestamp_str
            
            now = datetime.now()
            diff = now - timestamp.replace(tzinfo=None)
            
            if diff.days > 0:
                return f"{diff.days} days ago"
            elif diff.seconds > 3600:
                hours = diff.seconds // 3600
                return f"{hours} hours ago"
            elif diff.seconds > 60:
                minutes = diff.seconds // 60
                return f"{minutes} minutes ago"
            else:
                return "Just now"
        except Exception:
            return "Unknown"
    
    def generate_empty_dashboard(self):
        """Generate empty dashboard when no data"""
        html = self.create_dashboard_html({
            'sessions': [],
            'ai_suggestions': []
        })
        
        # Save empty dashboard
        dashboard_path = os.path.join(os.path.dirname(__file__), 'chat_dashboard.html')
        
        with open(dashboard_path, 'w', encoding='utf-8') as f:
            f.write(html)
        
        return {
            'success': True,
            'dashboard_path': dashboard_path,
            'sessions_count': 0,
            'total_messages': 0,
            'ai_suggestions': 0,
            'empty': True,
            'timestamp': datetime.now().isoformat()
        }

def main():
    """Main dashboard generation function"""
    parser = argparse.ArgumentParser(description='Chat Dashboard Generator')
    parser.add_argument('--session-id', help='Specific session ID to focus on')
    
    args = parser.parse_args()
    
    try:
        generator = ChatDashboardGenerator()
        result = generator.generate_dashboard(session_id=args.session_id)
        
        # Print result for n8n
        print(json.dumps(result, ensure_ascii=False, indent=2))
        
        return result.get('success', False)
        
    except Exception as e:
        result = {
            'success': False,
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }
        print(json.dumps(result))
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)