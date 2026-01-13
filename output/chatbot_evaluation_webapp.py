"""
=============================================================================
CHATBOT EVALUATION FRAMEWORK - API & MANUAL HYBRID APPROACH
=============================================================================
This framework provides:
1. API-based evaluation for chatbots with APIs (OpenAI, Anthropic, Google)
2. A web interface for manual evaluation of chatbots without APIs
3. Results aggregation and comparison

For automated API calls, you need API keys for:
- OpenAI (ChatGPT): OPENAI_API_KEY
- Anthropic (Claude): ANTHROPIC_API_KEY  
- Google (Gemini): GOOGLE_API_KEY

For Microsoft Copilot, manual evaluation is required via the web interface.

Author: Evaluation Framework
Date: January 12, 2026
=============================================================================
"""

import os
import csv
import json
import time
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
import http.server
import socketserver
import webbrowser
import urllib.parse
import threading


# =============================================================================
# API CLIENTS (when API keys are available)
# =============================================================================

class OpenAIClient:
    """Client for OpenAI/ChatGPT API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.available = False
        
        if self.api_key:
            try:
                import openai
                self.client = openai.OpenAI(api_key=self.api_key)
                self.available = True
            except ImportError:
                print("Note: openai package not installed. Install with: pip install openai")
    
    def chat(self, prompt: str, context: str = "", model: str = "gpt-4o") -> str:
        """Send a chat message and get response."""
        if not self.available:
            return "API_NOT_AVAILABLE"
        
        try:
            full_message = f"{context}\n\n{prompt}" if context else prompt
            
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": full_message}],
                max_tokens=4096
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"API_ERROR: {str(e)}"


class AnthropicClient:
    """Client for Anthropic/Claude API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.available = False
        
        if self.api_key:
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
                self.available = True
            except ImportError:
                print("Note: anthropic package not installed. Install with: pip install anthropic")
    
    def chat(self, prompt: str, context: str = "", model: str = "claude-sonnet-4-20250514") -> str:
        """Send a chat message and get response."""
        if not self.available:
            return "API_NOT_AVAILABLE"
        
        try:
            full_message = f"{context}\n\n{prompt}" if context else prompt
            
            response = self.client.messages.create(
                model=model,
                max_tokens=4096,
                messages=[{"role": "user", "content": full_message}]
            )
            return response.content[0].text
        except Exception as e:
            return f"API_ERROR: {str(e)}"


class GoogleClient:
    """Client for Google/Gemini API."""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GOOGLE_API_KEY")
        self.available = False
        
        if self.api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel("gemini-1.5-pro")
                self.available = True
            except ImportError:
                print("Note: google-generativeai not installed. Install with: pip install google-generativeai")
    
    def chat(self, prompt: str, context: str = "") -> str:
        """Send a chat message and get response."""
        if not self.available:
            return "API_NOT_AVAILABLE"
        
        try:
            full_message = f"{context}\n\n{prompt}" if context else prompt
            response = self.model.generate_content(full_message)
            return response.text
        except Exception as e:
            return f"API_ERROR: {str(e)}"


# =============================================================================
# WEB INTERFACE FOR MANUAL EVALUATION
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Chatbot Evaluation Interface</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            color: #e0e0e0;
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1600px;
            margin: 0 auto;
        }
        h1 {
            text-align: center;
            color: #00d4ff;
            margin-bottom: 20px;
            font-size: 2em;
        }
        .progress-bar {
            background: #2a2a4a;
            border-radius: 10px;
            padding: 5px;
            margin-bottom: 20px;
        }
        .progress-fill {
            background: linear-gradient(90deg, #00d4ff, #00ff88);
            height: 20px;
            border-radius: 8px;
            transition: width 0.3s;
        }
        .progress-text {
            text-align: center;
            margin-top: 5px;
            color: #888;
        }
        .main-content {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .left-panel, .right-panel {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 20px;
        }
        .section-title {
            color: #00d4ff;
            font-size: 1.2em;
            margin-bottom: 15px;
            border-bottom: 2px solid #00d4ff;
            padding-bottom: 10px;
        }
        .prompt-card {
            background: rgba(0,0,0,0.3);
            border-radius: 10px;
            padding: 15px;
            margin-bottom: 15px;
        }
        .prompt-card label {
            color: #00ff88;
            display: block;
            margin-bottom: 5px;
            font-size: 0.9em;
        }
        .prompt-card .content {
            background: rgba(255,255,255,0.05);
            padding: 10px;
            border-radius: 5px;
            max-height: 200px;
            overflow-y: auto;
            white-space: pre-wrap;
            font-size: 0.95em;
            line-height: 1.5;
        }
        .context-url {
            color: #00d4ff;
            word-break: break-all;
        }
        .context-url a {
            color: #00d4ff;
        }
        .chatbot-links {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 20px;
        }
        .chatbot-link {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 15px;
            border-radius: 10px;
            text-decoration: none;
            color: white;
            font-weight: bold;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .chatbot-link:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(0,0,0,0.3);
        }
        .chatbot-link.copilot {
            background: linear-gradient(135deg, #0078d4, #00bcf2);
        }
        .chatbot-link.chatgpt {
            background: linear-gradient(135deg, #10a37f, #1a7f64);
        }
        .chatbot-link.gemini {
            background: linear-gradient(135deg, #4285f4, #ea4335);
        }
        .chatbot-link.claude {
            background: linear-gradient(135deg, #d4a574, #c19660);
        }
        .copy-prompt-btn {
            background: #00d4ff;
            color: #1a1a2e;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            font-weight: bold;
            width: 100%;
            margin-bottom: 15px;
        }
        .copy-prompt-btn:hover {
            background: #00ff88;
        }
        .response-section {
            margin-bottom: 15px;
        }
        .response-section label {
            color: #00ff88;
            display: block;
            margin-bottom: 5px;
        }
        .response-section textarea {
            width: 100%;
            height: 150px;
            background: rgba(0,0,0,0.3);
            border: 1px solid #444;
            border-radius: 5px;
            padding: 10px;
            color: #e0e0e0;
            font-family: inherit;
            resize: vertical;
        }
        .response-section textarea:focus {
            outline: none;
            border-color: #00d4ff;
        }
        .nav-buttons {
            display: flex;
            gap: 10px;
            margin-top: 20px;
        }
        .nav-btn {
            flex: 1;
            padding: 15px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 1em;
            font-weight: bold;
            transition: all 0.2s;
        }
        .nav-btn.prev {
            background: #444;
            color: white;
        }
        .nav-btn.save {
            background: #00ff88;
            color: #1a1a2e;
        }
        .nav-btn.next {
            background: #00d4ff;
            color: #1a1a2e;
        }
        .nav-btn:hover {
            transform: translateY(-2px);
        }
        .nav-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .status-pending { background: #ff9800; }
        .status-complete { background: #00ff88; }
        .metadata {
            color: #888;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 Chatbot Evaluation Interface</h1>
        
        <div class="progress-bar">
            <div class="progress-fill" id="progressFill" style="width: PROGRESS_PERCENT%;"></div>
        </div>
        <div class="progress-text">Row CURRENT_ROW of TOTAL_ROWS (COMPLETED_COUNT completed)</div>
        
        <div class="main-content">
            <div class="left-panel">
                <div class="section-title">📝 Prompt & Context</div>
                
                <div class="metadata">
                    <strong>ID:</strong> PROMPT_ID | 
                    <strong>Action:</strong> PROMPT_ACTION | 
                    <strong>Object:</strong> PROMPT_OBJECT
                </div>
                
                <div class="prompt-card">
                    <label>Synthetic Prompt:</label>
                    <div class="content" id="promptText">PROMPT_TEXT</div>
                </div>
                
                <div class="prompt-card">
                    <label>Context URL (click to open):</label>
                    <div class="content context-url">
                        <a href="CONTEXT_URL" target="_blank">CONTEXT_URL_DISPLAY</a>
                    </div>
                </div>
                
                <div class="prompt-card">
                    <label>Context Text:</label>
                    <div class="content" id="contextText">CONTEXT_TEXT</div>
                </div>
                
                <button class="copy-prompt-btn" onclick="copyFullPrompt()">
                    📋 Copy Full Prompt (with context) to Clipboard
                </button>
                
                <div class="section-title">🔗 Open Chatbots</div>
                <div class="chatbot-links">
                    <a href="https://copilot.microsoft.com/" target="_blank" class="chatbot-link copilot">
                        Microsoft Copilot
                    </a>
                    <a href="https://chatgpt.com/" target="_blank" class="chatbot-link chatgpt">
                        ChatGPT
                    </a>
                    <a href="https://gemini.google.com/" target="_blank" class="chatbot-link gemini">
                        Google Gemini
                    </a>
                    <a href="https://claude.ai/" target="_blank" class="chatbot-link claude">
                        Claude
                    </a>
                </div>
            </div>
            
            <div class="right-panel">
                <div class="section-title">📊 Responses</div>
                <p style="color: #888; margin-bottom: 15px; font-size: 0.9em;">
                    Paste the full response from each chatbot below. Leave empty if not evaluated.
                </p>
                
                <div class="response-section">
                    <label><span class="status-indicator COPILOT_STATUS"></span>Microsoft Copilot Response:</label>
                    <textarea id="response_copilot" placeholder="Paste Copilot's response here...">RESPONSE_COPILOT</textarea>
                </div>
                
                <div class="response-section">
                    <label><span class="status-indicator CHATGPT_STATUS"></span>ChatGPT Response:</label>
                    <textarea id="response_chatgpt" placeholder="Paste ChatGPT's response here...">RESPONSE_CHATGPT</textarea>
                </div>
                
                <div class="response-section">
                    <label><span class="status-indicator GEMINI_STATUS"></span>Gemini Response:</label>
                    <textarea id="response_gemini" placeholder="Paste Gemini's response here...">RESPONSE_GEMINI</textarea>
                </div>
                
                <div class="response-section">
                    <label><span class="status-indicator CLAUDE_STATUS"></span>Claude Response:</label>
                    <textarea id="response_claude" placeholder="Paste Claude's response here...">RESPONSE_CLAUDE</textarea>
                </div>
                
                <div class="nav-buttons">
                    <button class="nav-btn prev" onclick="navigate('prev')" PREV_DISABLED>← Previous</button>
                    <button class="nav-btn save" onclick="saveResponses()">💾 Save</button>
                    <button class="nav-btn next" onclick="navigate('next')" NEXT_DISABLED>Next →</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const promptData = {
            prompt: `PROMPT_TEXT_JS`,
            context: `CONTEXT_TEXT_JS`,
            contextUrl: `CONTEXT_URL`
        };
        
        function copyFullPrompt() {
            let fullPrompt = '';
            if (promptData.contextUrl && promptData.contextUrl !== '') {
                fullPrompt = `Reference Document: ${promptData.contextUrl}\\n\\n${promptData.prompt}`;
            } else if (promptData.context && promptData.context !== '') {
                fullPrompt = `Context:\\n${promptData.context}\\n\\n---\\n\\nUser Request:\\n${promptData.prompt}`;
            } else {
                fullPrompt = promptData.prompt;
            }
            
            navigator.clipboard.writeText(fullPrompt).then(() => {
                alert('Full prompt copied to clipboard!');
            });
        }
        
        function saveResponses() {
            const responses = {
                copilot: document.getElementById('response_copilot').value,
                chatgpt: document.getElementById('response_chatgpt').value,
                gemini: document.getElementById('response_gemini').value,
                claude: document.getElementById('response_claude').value
            };
            
            fetch('/save', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    row_index: CURRENT_ROW_INDEX,
                    responses: responses
                })
            }).then(r => r.json()).then(data => {
                if (data.success) {
                    alert('Responses saved successfully!');
                    location.reload();
                }
            });
        }
        
        function navigate(direction) {
            const newIndex = direction === 'next' ? CURRENT_ROW_INDEX + 1 : CURRENT_ROW_INDEX - 1;
            window.location.href = '/row/' + newIndex;
        }
    </script>
</body>
</html>
"""


class EvaluationHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP handler for the evaluation web interface."""
    
    evaluator = None  # Will be set by the server
    
    def do_GET(self):
        if self.path == '/' or self.path.startswith('/row/'):
            self.send_evaluation_page()
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/save':
            self.save_responses()
        else:
            self.send_error(404)
    
    def send_evaluation_page(self):
        try:
            # Get row index
            if self.path.startswith('/row/'):
                row_index = int(self.path.split('/')[-1])
            else:
                row_index = 0
            
            # Get row data
            row = self.evaluator.get_row(row_index)
            if not row:
                self.send_error(404, "Row not found")
                return
            
            # Build page
            html = HTML_TEMPLATE
            
            # Progress
            total = self.evaluator.total_rows
            completed = self.evaluator.completed_count
            progress = (completed / total * 100) if total > 0 else 0
            
            html = html.replace('PROGRESS_PERCENT', str(int(progress)))
            html = html.replace('CURRENT_ROW', str(row_index + 1))
            html = html.replace('TOTAL_ROWS', str(total))
            html = html.replace('COMPLETED_COUNT', str(completed))
            html = html.replace('CURRENT_ROW_INDEX', str(row_index))
            
            # Prompt data
            html = html.replace('PROMPT_ID', str(row.get('synthetic_prompt_id', 'N/A')))
            html = html.replace('PROMPT_ACTION', str(row.get('input_action', 'N/A')))
            html = html.replace('PROMPT_OBJECT', str(row.get('input_object', 'N/A')))
            
            prompt_text = row.get('synthetic_prompt', '')
            context_text = row.get('context_text', '')
            context_url = row.get('context_url', '')
            
            html = html.replace('PROMPT_TEXT', self._escape_html(prompt_text))
            html = html.replace('CONTEXT_TEXT', self._escape_html(context_text[:2000] if context_text else 'No context'))
            html = html.replace('CONTEXT_URL_DISPLAY', context_url if context_url else 'No URL')
            html = html.replace('CONTEXT_URL', context_url if context_url else '#')
            
            # JS-safe versions
            html = html.replace('PROMPT_TEXT_JS', self._escape_js(prompt_text))
            html = html.replace('CONTEXT_TEXT_JS', self._escape_js(context_text[:2000] if context_text else ''))
            
            # Responses
            html = html.replace('RESPONSE_COPILOT', self._escape_html(row.get('response_copilot', '')))
            html = html.replace('RESPONSE_CHATGPT', self._escape_html(row.get('response_chatgpt', '')))
            html = html.replace('RESPONSE_GEMINI', self._escape_html(row.get('response_gemini', '')))
            html = html.replace('RESPONSE_CLAUDE', self._escape_html(row.get('response_claude', '')))
            
            # Status indicators
            html = html.replace('COPILOT_STATUS', 'status-complete' if row.get('response_copilot') else 'status-pending')
            html = html.replace('CHATGPT_STATUS', 'status-complete' if row.get('response_chatgpt') else 'status-pending')
            html = html.replace('GEMINI_STATUS', 'status-complete' if row.get('response_gemini') else 'status-pending')
            html = html.replace('CLAUDE_STATUS', 'status-complete' if row.get('response_claude') else 'status-pending')
            
            # Navigation
            html = html.replace('PREV_DISABLED', 'disabled' if row_index == 0 else '')
            html = html.replace('NEXT_DISABLED', 'disabled' if row_index >= total - 1 else '')
            
            # Send response
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(html.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def save_responses(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))
            
            row_index = data['row_index']
            responses = data['responses']
            
            self.evaluator.save_responses(row_index, responses)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'success': True}).encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def _escape_html(self, text: str) -> str:
        return (text or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')
    
    def _escape_js(self, text: str) -> str:
        return (text or '').replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('\n', '\\n').replace('\r', '')
    
    def log_message(self, format, *args):
        pass  # Suppress logging


class ManualEvaluator:
    """Manual evaluation coordinator with web interface."""
    
    def __init__(self, input_csv: str, output_dir: str = "evaluation_results"):
        self.input_csv = Path(input_csv)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.rows: List[Dict] = []
        self.total_rows = 0
        self.completed_count = 0
        
        self._load_data()
    
    def _load_data(self):
        """Load input data."""
        with open(self.input_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.rows = list(reader)
        
        self.total_rows = len(self.rows)
        
        # Add response columns if not present
        for row in self.rows:
            for chatbot in ['copilot', 'chatgpt', 'gemini', 'claude']:
                if f'response_{chatbot}' not in row:
                    row[f'response_{chatbot}'] = ''
        
        self._count_completed()
    
    def _count_completed(self):
        """Count rows with at least one response."""
        self.completed_count = sum(
            1 for row in self.rows 
            if any(row.get(f'response_{cb}') for cb in ['copilot', 'chatgpt', 'gemini', 'claude'])
        )
    
    def get_row(self, index: int) -> Optional[Dict]:
        """Get a row by index."""
        if 0 <= index < len(self.rows):
            return self.rows[index]
        return None
    
    def save_responses(self, index: int, responses: Dict):
        """Save responses for a row."""
        if 0 <= index < len(self.rows):
            for chatbot, response in responses.items():
                self.rows[index][f'response_{chatbot}'] = response
            
            self._count_completed()
            self._save_to_file()
    
    def _save_to_file(self):
        """Save current state to file."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save CSV
        csv_path = self.output_dir / f"evaluation_results_latest.csv"
        fieldnames = list(self.rows[0].keys()) if self.rows else []
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)
        
        # Also save timestamped version
        csv_backup = self.output_dir / f"evaluation_results_{timestamp}.csv"
        with open(csv_backup, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)
    
    def start_server(self, port: int = 8080, limit: int = 10):
        """Start the web server for manual evaluation."""
        # Limit rows if specified
        if limit and limit < len(self.rows):
            self.rows = self.rows[:limit]
            self.total_rows = limit
        
        # Set up handler
        EvaluationHandler.evaluator = self
        
        print(f"\n{'='*60}")
        print("CHATBOT EVALUATION - MANUAL INTERFACE")
        print('='*60)
        print(f"Input file: {self.input_csv}")
        print(f"Rows to evaluate: {self.total_rows}")
        print(f"\nStarting web server on http://localhost:{port}")
        print("Opening browser...")
        print("\nInstructions:")
        print("1. Copy the prompt using the button")
        print("2. Click each chatbot link to open in new tab")
        print("3. Paste prompt and get response")
        print("4. Copy response back to the text area")
        print("5. Click Save and move to next row")
        print("\nPress Ctrl+C to stop the server")
        print('='*60)
        
        # Open browser
        webbrowser.open(f'http://localhost:{port}')
        
        # Start server
        with socketserver.TCPServer(("", port), EvaluationHandler) as httpd:
            try:
                httpd.serve_forever()
            except KeyboardInterrupt:
                print("\nServer stopped.")
                self._save_to_file()
                print(f"Results saved to: {self.output_dir / 'evaluation_results_latest.csv'}")


# =============================================================================
# API-BASED AUTOMATED EVALUATION
# =============================================================================

class AutomatedEvaluator:
    """Automated evaluation using APIs (requires API keys)."""
    
    def __init__(self, input_csv: str, output_dir: str = "evaluation_results"):
        self.input_csv = Path(input_csv)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        # Initialize API clients
        self.openai_client = OpenAIClient()
        self.anthropic_client = AnthropicClient()
        self.google_client = GoogleClient()
        
        self.rows: List[Dict] = []
        
    def run(self, limit: int = 10):
        """Run automated evaluation using available APIs."""
        print(f"\n{'='*60}")
        print("AUTOMATED CHATBOT EVALUATION")
        print('='*60)
        
        # Check which APIs are available
        print("\nAPI Status:")
        print(f"  OpenAI (ChatGPT): {'✓ Available' if self.openai_client.available else '✗ Not configured'}")
        print(f"  Anthropic (Claude): {'✓ Available' if self.anthropic_client.available else '✗ Not configured'}")
        print(f"  Google (Gemini): {'✓ Available' if self.google_client.available else '✗ Not configured'}")
        print(f"  Microsoft Copilot: ✗ No API (use manual evaluation)")
        
        if not any([self.openai_client.available, self.anthropic_client.available, self.google_client.available]):
            print("\nNo APIs configured. Please set environment variables:")
            print("  OPENAI_API_KEY for ChatGPT")
            print("  ANTHROPIC_API_KEY for Claude")
            print("  GOOGLE_API_KEY for Gemini")
            print("\nOr use the manual evaluation mode instead.")
            return
        
        # Load data
        with open(self.input_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            self.rows = list(reader)[:limit]
        
        print(f"\nProcessing {len(self.rows)} rows...")
        
        for i, row in enumerate(self.rows):
            print(f"\n  Row {i+1}/{len(self.rows)}:")
            
            prompt = row.get('synthetic_prompt', '')
            context_url = row.get('context_url', '')
            context_text = row.get('context_text', '')
            
            # Build context
            if context_url:
                context = f"Reference document: {context_url}"
            else:
                context = context_text[:2000] if context_text else ""
            
            # Query available APIs
            if self.openai_client.available:
                print("    Querying ChatGPT...", end=" ", flush=True)
                response = self.openai_client.chat(prompt, context)
                row['response_chatgpt'] = response
                print(f"Got {len(response)} chars")
                time.sleep(1)  # Rate limiting
            
            if self.anthropic_client.available:
                print("    Querying Claude...", end=" ", flush=True)
                response = self.anthropic_client.chat(prompt, context)
                row['response_claude'] = response
                print(f"Got {len(response)} chars")
                time.sleep(1)
            
            if self.google_client.available:
                print("    Querying Gemini...", end=" ", flush=True)
                response = self.google_client.chat(prompt, context)
                row['response_gemini'] = response
                print(f"Got {len(response)} chars")
                time.sleep(1)
            
            # Copilot needs manual evaluation
            row['response_copilot'] = "MANUAL_EVALUATION_REQUIRED"
        
        # Save results
        self._save_results()
        
    def _save_results(self):
        """Save evaluation results."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        csv_path = self.output_dir / f"automated_evaluation_{timestamp}.csv"
        fieldnames = list(self.rows[0].keys()) if self.rows else []
        
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.rows)
        
        print(f"\n✓ Results saved to: {csv_path}")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    import sys
    
    # Find latest V4 file
    v4_files = list(Path("synthetic_prompts").glob("synthetic_prompts_v4_enhanced_*.csv"))
    if not v4_files:
        print("ERROR: No V4 enhanced file found!")
        return
    
    latest_v4 = max(v4_files, key=lambda p: p.stat().st_mtime)
    print(f"Using input file: {latest_v4}")
    
    # Check command line args
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        # Automated mode with APIs
        evaluator = AutomatedEvaluator(str(latest_v4))
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 10
        evaluator.run(limit=limit)
    else:
        # Manual mode with web interface (default)
        evaluator = ManualEvaluator(str(latest_v4))
        limit = int(sys.argv[1]) if len(sys.argv) > 1 else 10
        evaluator.start_server(port=8080, limit=limit)


if __name__ == "__main__":
    main()
