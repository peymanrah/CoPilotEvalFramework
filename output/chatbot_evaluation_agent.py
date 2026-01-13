"""
=============================================================================
CHATBOT EVALUATION BROWSER AGENT
=============================================================================
This agent automates testing prompts against multiple chatbots:
- Microsoft Copilot (copilot.microsoft.com)
- ChatGPT (chatgpt.com)
- Google Gemini (gemini.google.com)
- Claude (claude.ai)

Uses Playwright for browser automation with unauthenticated/guest access.

Author: Evaluation Framework
Date: January 12, 2026
=============================================================================
"""

import asyncio
import csv
import json
import time
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from playwright.async_api import async_playwright, Page, Browser, BrowserContext


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class ChatbotConfig:
    """Configuration for each chatbot."""
    name: str
    url: str
    input_selector: str
    submit_selector: str
    response_selector: str
    wait_for_response: str  # Selector or condition to wait for
    max_wait_seconds: int = 120
    needs_cookies_accept: bool = False
    cookie_selector: Optional[str] = None


# Chatbot configurations - updated with working selectors
CHATBOT_CONFIGS = {
    "copilot": ChatbotConfig(
        name="Microsoft Copilot",
        url="https://copilot.microsoft.com/",
        input_selector='textarea, [contenteditable="true"], #userInput, .cib-serp-main textarea',
        submit_selector='button[aria-label*="Submit"], button[aria-label*="Send"], button[type="submit"], .submit-button',
        response_selector='.ac-textBlock, [class*="text-message-content"], .response-message-group, cib-message-group[source="bot"]',
        wait_for_response='.ac-textBlock, [class*="text-message-content"]',
        max_wait_seconds=90
    ),
    "chatgpt": ChatbotConfig(
        name="ChatGPT",
        url="https://chatgpt.com/",
        input_selector='#prompt-textarea, textarea[placeholder*="Message"], div[contenteditable="true"], textarea',
        submit_selector='button[data-testid="send-button"], button[aria-label*="Send message"], form button[type="submit"]',
        response_selector='[data-message-author-role="assistant"], div[class*="markdown"], .prose, article[data-testid*="conversation"]',
        wait_for_response='[data-message-author-role="assistant"]',
        max_wait_seconds=120
    ),
    "gemini": ChatbotConfig(
        name="Google Gemini",
        url="https://gemini.google.com/app",
        input_selector='.ql-editor, rich-textarea div[contenteditable="true"], div[contenteditable="true"], textarea, p[data-placeholder]',
        submit_selector='button[aria-label*="Send"], button.send-button, mat-icon-button[aria-label*="Send"], button[mattooltip*="Send"]',
        response_selector='.model-response-text, .response-container, message-content, .markdown-main-panel',
        wait_for_response='.model-response-text, .response-container, message-content',
        max_wait_seconds=90
    ),
    "claude": ChatbotConfig(
        name="Claude",
        url="https://claude.ai/new",
        input_selector='div[contenteditable="true"], .ProseMirror, textarea, [data-testid="chat-input"]',
        submit_selector='button[aria-label*="Send"], button[type="submit"], [data-testid="send-button"], button:has(svg)',
        response_selector='[data-testid="assistant-message"], .font-claude-message, .prose, div[class*="response"]',
        wait_for_response='[data-testid="assistant-message"], .font-claude-message',
        max_wait_seconds=120
    )
}


# =============================================================================
# CHATBOT HANDLER BASE CLASS
# =============================================================================

class ChatbotHandler:
    """Base handler for interacting with chatbots."""
    
    def __init__(self, config: ChatbotConfig, page: Page):
        self.config = config
        self.page = page
        self.is_ready = False
    
    async def navigate_and_prepare(self) -> bool:
        """Navigate to chatbot and prepare for interaction."""
        try:
            print(f"    Navigating to {self.config.name}...")
            await self.page.goto(self.config.url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(3)  # Wait for page to stabilize
            
            # Handle cookie consent if needed
            await self._handle_cookies()
            
            # Wait for input to be ready
            await self._wait_for_ready()
            
            self.is_ready = True
            return True
        except Exception as e:
            print(f"    ERROR navigating to {self.config.name}: {e}")
            return False
    
    async def _handle_cookies(self):
        """Handle cookie consent popups."""
        cookie_selectors = [
            'button:has-text("Accept")',
            'button:has-text("Accept all")',
            'button:has-text("I agree")',
            'button:has-text("Got it")',
            '[aria-label*="Accept"]',
            '.cookie-accept',
        ]
        for selector in cookie_selectors:
            try:
                btn = await self.page.wait_for_selector(selector, timeout=2000)
                if btn:
                    await btn.click()
                    await asyncio.sleep(1)
                    break
            except:
                pass
    
    async def _wait_for_ready(self):
        """Wait for input field to be ready."""
        selectors = self.config.input_selector.split(", ")
        for selector in selectors:
            try:
                await self.page.wait_for_selector(selector, timeout=10000)
                return
            except:
                continue
    
    async def send_prompt(self, prompt: str, context: str = "") -> str:
        """Send a prompt and get the response."""
        if not self.is_ready:
            return "ERROR: Chatbot not ready"
        
        try:
            # Combine prompt with context
            full_prompt = self._build_full_prompt(prompt, context)
            
            # Find and fill the input field
            input_filled = await self._fill_input(full_prompt)
            if not input_filled:
                return "ERROR: Could not fill input field"
            
            await asyncio.sleep(1)
            
            # Submit the prompt
            submitted = await self._submit()
            if not submitted:
                return "ERROR: Could not submit prompt"
            
            # Wait for and extract response
            response = await self._wait_and_extract_response()
            return response
            
        except Exception as e:
            return f"ERROR: {str(e)}"
    
    def _build_full_prompt(self, prompt: str, context: str) -> str:
        """Build the full prompt with context."""
        if context and len(context) > 100:
            # If context is long (synthetic document), include it
            return f"""Context/Reference Document:
{context[:4000]}

---

User Request:
{prompt}"""
        elif context:
            # If context is just a URL reference
            return f"""{prompt}

Reference: {context}"""
        else:
            return prompt
    
    async def _fill_input(self, text: str) -> bool:
        """Fill the input field with text."""
        selectors = self.config.input_selector.split(", ")
        
        for selector in selectors:
            try:
                element = await self.page.query_selector(selector)
                if element:
                    # Check if it's contenteditable
                    is_editable = await element.get_attribute("contenteditable")
                    
                    if is_editable == "true":
                        await element.click()
                        await self.page.keyboard.type(text[:2000], delay=5)  # Limit text length
                    else:
                        await element.fill(text[:2000])
                    
                    return True
            except Exception as e:
                continue
        
        return False
    
    async def _submit(self) -> bool:
        """Submit the prompt."""
        # Try pressing Enter first
        try:
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(0.5)
            
            # Check if that worked by looking for loading state
            return True
        except:
            pass
        
        # Try clicking submit button
        selectors = self.config.submit_selector.split(", ")
        for selector in selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn and await btn.is_enabled():
                    await btn.click()
                    return True
            except:
                continue
        
        return False
    
    async def _wait_and_extract_response(self) -> str:
        """Wait for response and extract it."""
        start_time = time.time()
        max_wait = self.config.max_wait_seconds
        
        # Wait for response to appear
        response_selectors = self.config.response_selector.split(", ")
        
        while time.time() - start_time < max_wait:
            for selector in response_selectors:
                try:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # Get the last response (most recent)
                        last_element = elements[-1]
                        
                        # Check if still generating (look for common patterns)
                        is_generating = await self._is_still_generating()
                        
                        if not is_generating:
                            # Extract text content
                            text = await last_element.inner_text()
                            if text and len(text) > 10:
                                return text.strip()
                except:
                    continue
            
            await asyncio.sleep(2)
        
        return "ERROR: Timeout waiting for response"
    
    async def _is_still_generating(self) -> bool:
        """Check if the chatbot is still generating a response."""
        generating_indicators = [
            '.loading', '.generating', '.typing', 
            '[aria-busy="true"]', '.cursor-blink',
            'button[disabled]'  # Send button disabled during generation
        ]
        
        for indicator in generating_indicators:
            try:
                element = await self.page.query_selector(indicator)
                if element and await element.is_visible():
                    return True
            except:
                pass
        
        return False


# =============================================================================
# SPECIALIZED HANDLERS FOR EACH CHATBOT
# =============================================================================

class CopilotHandler(ChatbotHandler):
    """Specialized handler for Microsoft Copilot."""
    
    async def navigate_and_prepare(self) -> bool:
        try:
            print(f"    Navigating to Microsoft Copilot...")
            await self.page.goto(self.config.url, timeout=60000, wait_until="networkidle")
            await asyncio.sleep(5)
            
            # Take screenshot for debugging
            await self.page.screenshot(path="debug_copilot.png")
            
            # Check if we need to dismiss any dialogs/welcome screens
            try:
                # Look for various dismiss buttons
                dismiss_selectors = [
                    'button:has-text("Accept")',
                    'button:has-text("Got it")', 
                    'button:has-text("Continue")',
                    'button:has-text("Skip")',
                    '[aria-label="Close"]',
                    '.close-button'
                ]
                for selector in dismiss_selectors:
                    try:
                        btn = await self.page.wait_for_selector(selector, timeout=2000)
                        if btn and await btn.is_visible():
                            await btn.click()
                            await asyncio.sleep(1)
                    except:
                        pass
            except:
                pass
            
            # Wait for the input field
            await asyncio.sleep(2)
            self.is_ready = True
            print(f"    Copilot ready")
            return True
        except Exception as e:
            print(f"    ERROR: {e}")
            return False
    
    async def _fill_input(self, text: str) -> bool:
        """Fill Copilot input."""
        try:
            # Try multiple selectors for Copilot's input
            selectors = [
                'textarea#searchbox',
                'textarea[name="searchbox"]', 
                '#userInput',
                'textarea',
                '[contenteditable="true"]'
            ]
            
            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        await element.click()
                        await asyncio.sleep(0.5)
                        
                        # Clear existing content
                        await self.page.keyboard.press("Control+a")
                        await asyncio.sleep(0.1)
                        
                        # Type the text
                        await element.fill(text[:2000])
                        print(f"    Filled input using: {selector}")
                        return True
                except:
                    continue
            
            # Fallback: try clicking in general area and typing
            try:
                await self.page.click('body')
                await self.page.keyboard.type(text[:500], delay=10)
                return True
            except:
                pass
                
            return False
        except Exception as e:
            print(f"    Fill input error: {e}")
            return False
    
    async def _submit(self) -> bool:
        """Submit to Copilot."""
        try:
            # First try Enter key
            await self.page.keyboard.press("Enter")
            await asyncio.sleep(1)
            return True
        except:
            pass
        
        # Try clicking submit button
        submit_selectors = [
            'button[aria-label*="Submit"]',
            'button[aria-label*="Send"]',
            'button[type="submit"]',
            '.submit-button'
        ]
        for selector in submit_selectors:
            try:
                btn = await self.page.query_selector(selector)
                if btn and await btn.is_enabled():
                    await btn.click()
                    return True
            except:
                continue
        return False
    
    async def _wait_and_extract_response(self) -> str:
        """Wait for and extract Copilot response."""
        print(f"    Waiting for response...")
        start_time = time.time()
        max_wait = self.config.max_wait_seconds
        last_response = ""
        stable_count = 0
        
        while time.time() - start_time < max_wait:
            try:
                # Look for response elements
                response_selectors = [
                    '.ac-textBlock',
                    '[class*="text-message-content"]',
                    'cib-message-group[source="bot"] .text-message-content',
                    '.response-message-group',
                    'p[class*="text-"]'
                ]
                
                for selector in response_selectors:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        # Get all text from last response group
                        all_text = []
                        for el in elements[-5:]:  # Get last few elements
                            try:
                                text = await el.inner_text()
                                if text and len(text) > 5:
                                    all_text.append(text.strip())
                            except:
                                pass
                        
                        if all_text:
                            current_response = "\n".join(all_text)
                            
                            # Check if response is stable (not still generating)
                            if current_response == last_response and len(current_response) > 20:
                                stable_count += 1
                                if stable_count >= 3:  # Stable for 3 checks
                                    print(f"    Got response: {len(current_response)} chars")
                                    return current_response
                            else:
                                stable_count = 0
                                last_response = current_response
                
            except Exception as e:
                pass
            
            await asyncio.sleep(2)
        
        if last_response:
            return last_response
        return "ERROR: Timeout waiting for response"


class ChatGPTHandler(ChatbotHandler):
    """Specialized handler for ChatGPT."""
    
    async def navigate_and_prepare(self) -> bool:
        try:
            print(f"    Navigating to ChatGPT...")
            await self.page.goto(self.config.url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            await self.page.screenshot(path="debug_chatgpt.png")
            
            # Handle any welcome/login prompts
            try:
                dismiss_selectors = [
                    'button:has-text("Stay logged out")',
                    'button:has-text("Continue without account")',
                    'button:has-text("Try ChatGPT")',
                    'button:has-text("Close")',
                    'button:has-text("Dismiss")',
                    '[aria-label="Close"]'
                ]
                for selector in dismiss_selectors:
                    try:
                        btn = await self.page.wait_for_selector(selector, timeout=3000)
                        if btn:
                            await btn.click()
                            await asyncio.sleep(2)
                    except:
                        pass
            except:
                pass
            
            await asyncio.sleep(2)
            self.is_ready = True
            print(f"    ChatGPT ready")
            return True
        except Exception as e:
            print(f"    ERROR: {e}")
            return False
    
    async def _fill_input(self, text: str) -> bool:
        """Fill ChatGPT input."""
        try:
            selectors = [
                '#prompt-textarea',
                'textarea[placeholder*="Message"]',
                'div[contenteditable="true"][id="prompt-textarea"]',
                'textarea',
                '[contenteditable="true"]'
            ]
            
            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        await element.click()
                        await asyncio.sleep(0.3)
                        
                        # Check if contenteditable
                        is_editable = await element.get_attribute("contenteditable")
                        if is_editable == "true":
                            await self.page.keyboard.type(text[:2000], delay=5)
                        else:
                            await element.fill(text[:2000])
                        
                        print(f"    Filled input using: {selector}")
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"    Fill input error: {e}")
            return False
    
    async def _submit(self) -> bool:
        """Submit to ChatGPT."""
        try:
            # Try button click first (more reliable than Enter)
            submit_selectors = [
                'button[data-testid="send-button"]',
                'button[aria-label*="Send"]',
                'form button[type="submit"]'
            ]
            for selector in submit_selectors:
                try:
                    btn = await self.page.query_selector(selector)
                    if btn:
                        await btn.click()
                        return True
                except:
                    continue
            
            # Fallback to Enter
            await self.page.keyboard.press("Enter")
            return True
        except:
            return False
    
    async def _wait_and_extract_response(self) -> str:
        """Wait for and extract ChatGPT response."""
        print(f"    Waiting for response...")
        start_time = time.time()
        max_wait = self.config.max_wait_seconds
        last_response = ""
        stable_count = 0
        
        while time.time() - start_time < max_wait:
            try:
                selectors = [
                    '[data-message-author-role="assistant"]',
                    'div[class*="markdown"]',
                    '.prose',
                    'article[data-testid*="conversation"]'
                ]
                
                for selector in selectors:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        last_el = elements[-1]
                        text = await last_el.inner_text()
                        
                        if text and len(text) > 10:
                            # Check stability
                            if text == last_response:
                                stable_count += 1
                                if stable_count >= 3:
                                    print(f"    Got response: {len(text)} chars")
                                    return text.strip()
                            else:
                                stable_count = 0
                                last_response = text
                
            except:
                pass
            
            await asyncio.sleep(2)
        
        if last_response:
            return last_response
        return "ERROR: Timeout waiting for response"


class GeminiHandler(ChatbotHandler):
    """Specialized handler for Google Gemini."""
    
    async def navigate_and_prepare(self) -> bool:
        try:
            print(f"    Navigating to Gemini...")
            await self.page.goto(self.config.url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            await self.page.screenshot(path="debug_gemini.png")
            
            # Handle any consent/welcome dialogs
            try:
                dismiss_selectors = [
                    'button:has-text("I agree")',
                    'button:has-text("Accept all")',
                    'button:has-text("Got it")',
                    'button:has-text("Continue")',
                    '[aria-label="Close"]'
                ]
                for selector in dismiss_selectors:
                    try:
                        btn = await self.page.wait_for_selector(selector, timeout=2000)
                        if btn:
                            await btn.click()
                            await asyncio.sleep(1)
                    except:
                        pass
            except:
                pass
            
            await asyncio.sleep(2)
            self.is_ready = True
            print(f"    Gemini ready")
            return True
        except Exception as e:
            print(f"    ERROR: {e}")
            return False
    
    async def _fill_input(self, text: str) -> bool:
        """Fill Gemini input."""
        try:
            selectors = [
                '.ql-editor',
                'rich-textarea div[contenteditable="true"]',
                'div[contenteditable="true"]',
                'p[data-placeholder]',
                'textarea'
            ]
            
            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        await element.click()
                        await asyncio.sleep(0.3)
                        await self.page.keyboard.type(text[:2000], delay=5)
                        print(f"    Filled input using: {selector}")
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"    Fill input error: {e}")
            return False
    
    async def _submit(self) -> bool:
        """Submit to Gemini."""
        try:
            # Try send button
            submit_selectors = [
                'button[aria-label*="Send"]',
                'button.send-button',
                'mat-icon-button[aria-label*="Send"]'
            ]
            for selector in submit_selectors:
                try:
                    btn = await self.page.query_selector(selector)
                    if btn:
                        await btn.click()
                        return True
                except:
                    continue
            
            # Fallback to Enter
            await self.page.keyboard.press("Enter")
            return True
        except:
            return False
    
    async def _wait_and_extract_response(self) -> str:
        """Wait for and extract Gemini response."""
        print(f"    Waiting for response...")
        start_time = time.time()
        max_wait = self.config.max_wait_seconds
        last_response = ""
        stable_count = 0
        
        while time.time() - start_time < max_wait:
            try:
                selectors = [
                    '.model-response-text',
                    '.response-container',
                    'message-content',
                    '.markdown-main-panel'
                ]
                
                for selector in selectors:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        last_el = elements[-1]
                        text = await last_el.inner_text()
                        
                        if text and len(text) > 10:
                            if text == last_response:
                                stable_count += 1
                                if stable_count >= 3:
                                    print(f"    Got response: {len(text)} chars")
                                    return text.strip()
                            else:
                                stable_count = 0
                                last_response = text
                
            except:
                pass
            
            await asyncio.sleep(2)
        
        if last_response:
            return last_response
        return "ERROR: Timeout waiting for response"


class ClaudeHandler(ChatbotHandler):
    """Specialized handler for Claude."""
    
    async def navigate_and_prepare(self) -> bool:
        try:
            print(f"    Navigating to Claude...")
            await self.page.goto(self.config.url, timeout=60000, wait_until="domcontentloaded")
            await asyncio.sleep(5)
            
            await self.page.screenshot(path="debug_claude.png")
            
            await asyncio.sleep(2)
            self.is_ready = True
            print(f"    Claude ready")
            return True
        except Exception as e:
            print(f"    ERROR: {e}")
            return False
    
    async def _fill_input(self, text: str) -> bool:
        """Fill Claude input."""
        try:
            selectors = [
                'div[contenteditable="true"].ProseMirror',
                '.ProseMirror',
                'div[contenteditable="true"]',
                'textarea'
            ]
            
            for selector in selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=5000)
                    if element and await element.is_visible():
                        await element.click()
                        await asyncio.sleep(0.3)
                        await self.page.keyboard.type(text[:2000], delay=5)
                        print(f"    Filled input using: {selector}")
                        return True
                except:
                    continue
            
            return False
        except Exception as e:
            print(f"    Fill input error: {e}")
            return False
    
    async def _submit(self) -> bool:
        """Submit to Claude."""
        try:
            # Try send button
            submit_selectors = [
                'button[aria-label*="Send"]',
                'button[type="submit"]',
                '[data-testid="send-button"]'
            ]
            for selector in submit_selectors:
                try:
                    btn = await self.page.query_selector(selector)
                    if btn:
                        await btn.click()
                        return True
                except:
                    continue
            
            # Fallback to Enter
            await self.page.keyboard.press("Enter")
            return True
        except:
            return False
    
    async def _wait_and_extract_response(self) -> str:
        """Wait for and extract Claude response."""
        print(f"    Waiting for response...")
        start_time = time.time()
        max_wait = self.config.max_wait_seconds
        last_response = ""
        stable_count = 0
        
        while time.time() - start_time < max_wait:
            try:
                selectors = [
                    '[data-testid="assistant-message"]',
                    '.font-claude-message',
                    '.prose'
                ]
                
                for selector in selectors:
                    elements = await self.page.query_selector_all(selector)
                    if elements:
                        last_el = elements[-1]
                        text = await last_el.inner_text()
                        
                        if text and len(text) > 10:
                            if text == last_response:
                                stable_count += 1
                                if stable_count >= 3:
                                    print(f"    Got response: {len(text)} chars")
                                    return text.strip()
                            else:
                                stable_count = 0
                                last_response = text
                
            except:
                pass
            
            await asyncio.sleep(2)
        
        if last_response:
            return last_response
        return "ERROR: Timeout waiting for response"


# =============================================================================
# MAIN EVALUATION AGENT
# =============================================================================

class ChatbotEvaluationAgent:
    """Main agent that orchestrates chatbot evaluation."""
    
    def __init__(self, input_csv: str, output_dir: str = "evaluation_results"):
        self.input_csv = Path(input_csv)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.results: List[Dict] = []
        
    async def run_evaluation(self, limit: int = 10, chatbots: List[str] = None):
        """Run the evaluation on specified number of rows."""
        if chatbots is None:
            chatbots = ["copilot", "chatgpt", "gemini", "claude"]
        
        print("=" * 70)
        print("CHATBOT EVALUATION AGENT")
        print("=" * 70)
        print(f"Input file: {self.input_csv}")
        print(f"Testing rows: {limit}")
        print(f"Chatbots: {', '.join(chatbots)}")
        print()
        
        # Load input data
        rows = self._load_input_data(limit)
        if not rows:
            print("ERROR: No data to process")
            return
        
        print(f"Loaded {len(rows)} rows for testing")
        print()
        
        async with async_playwright() as p:
            # Launch browser with visible UI for debugging
            browser = await p.chromium.launch(
                headless=False,  # Show browser for debugging
                slow_mo=100  # Slow down for visibility
            )
            
            # Create a context with reasonable viewport
            context = await browser.new_context(
                viewport={"width": 1400, "height": 900},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            
            # Process each row
            for idx, row in enumerate(rows):
                print(f"\n{'='*70}")
                print(f"Processing Row {idx + 1}/{len(rows)}")
                print(f"Prompt: {row.get('synthetic_prompt', '')[:80]}...")
                print("=" * 70)
                
                result = row.copy()
                
                # Get context for this prompt
                context_text = row.get("context_text", "")
                context_url = row.get("context_url", "")
                prompt = row.get("synthetic_prompt", "")
                
                # Build the full prompt with context
                if context_url:
                    context_for_prompt = f"Reference document: {context_url}"
                else:
                    context_for_prompt = context_text
                
                # Test each chatbot
                for chatbot_key in chatbots:
                    config = CHATBOT_CONFIGS.get(chatbot_key)
                    if not config:
                        continue
                    
                    print(f"\n  Testing {config.name}...")
                    
                    # Create new page for each chatbot
                    page = await context.new_page()
                    
                    try:
                        # Create appropriate handler
                        if chatbot_key == "copilot":
                            handler = CopilotHandler(config, page)
                        elif chatbot_key == "chatgpt":
                            handler = ChatGPTHandler(config, page)
                        elif chatbot_key == "gemini":
                            handler = GeminiHandler(config, page)
                        elif chatbot_key == "claude":
                            handler = ClaudeHandler(config, page)
                        else:
                            handler = ChatbotHandler(config, page)
                        
                        # Navigate and prepare
                        ready = await handler.navigate_and_prepare()
                        
                        if ready:
                            # Send prompt and get response
                            response = await handler.send_prompt(prompt, context_for_prompt)
                            result[f"response_{chatbot_key}"] = response
                            
                            # Log preview
                            preview = response[:100] + "..." if len(response) > 100 else response
                            print(f"    Response preview: {preview}")
                        else:
                            result[f"response_{chatbot_key}"] = "ERROR: Could not initialize chatbot"
                            
                    except Exception as e:
                        result[f"response_{chatbot_key}"] = f"ERROR: {str(e)}"
                        print(f"    ERROR: {e}")
                    finally:
                        await page.close()
                    
                    # Small delay between chatbots
                    await asyncio.sleep(2)
                
                self.results.append(result)
                
                # Save intermediate results
                self._save_results(f"evaluation_test_{len(rows)}_rows")
            
            await browser.close()
        
        print("\n" + "=" * 70)
        print("EVALUATION COMPLETE")
        print("=" * 70)
        self._print_summary()
        
        return self.results
    
    def _load_input_data(self, limit: int) -> List[Dict]:
        """Load input CSV data."""
        rows = []
        with open(self.input_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if i >= limit:
                    break
                rows.append(row)
        return rows
    
    def _save_results(self, prefix: str):
        """Save results to CSV and JSON."""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Determine fieldnames (original + new response columns)
        if self.results:
            fieldnames = list(self.results[0].keys())
        else:
            return
        
        # Save CSV
        csv_path = self.output_dir / f"{prefix}_{timestamp}.csv"
        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(self.results)
        
        # Save JSON
        json_path = self.output_dir / f"{prefix}_{timestamp}.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print(f"\n  Saved intermediate results to: {csv_path}")
    
    def _print_summary(self):
        """Print evaluation summary."""
        print(f"\nTotal rows processed: {len(self.results)}")
        
        chatbots = ["copilot", "chatgpt", "gemini", "claude"]
        for chatbot in chatbots:
            col = f"response_{chatbot}"
            if self.results and col in self.results[0]:
                success = sum(1 for r in self.results if not r.get(col, "").startswith("ERROR"))
                print(f"  {chatbot}: {success}/{len(self.results)} successful")


# =============================================================================
# SIMPLE TEST MODE
# =============================================================================

async def test_single_chatbot(chatbot: str = "copilot"):
    """Test a single chatbot with a simple prompt."""
    print(f"\n{'='*60}")
    print(f"TESTING {chatbot.upper()}")
    print('='*60)
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, slow_mo=200)
        context = await browser.new_context(
            viewport={"width": 1400, "height": 900}
        )
        page = await context.new_page()
        
        config = CHATBOT_CONFIGS[chatbot]
        
        if chatbot == "copilot":
            handler = CopilotHandler(config, page)
        elif chatbot == "chatgpt":
            handler = ChatGPTHandler(config, page)
        elif chatbot == "gemini":
            handler = GeminiHandler(config, page)
        else:
            handler = ClaudeHandler(config, page)
        
        # Navigate
        ready = await handler.navigate_and_prepare()
        print(f"Ready: {ready}")
        
        if ready:
            # Try a simple prompt
            response = await handler.send_prompt(
                "What is 2 + 2? Please respond with just the number.",
                ""
            )
            print(f"\nResponse:\n{response}")
        
        # Keep browser open for inspection
        print("\nBrowser will stay open for 30 seconds for inspection...")
        await asyncio.sleep(30)
        
        await browser.close()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def main():
    """Main entry point."""
    import sys
    
    # Default to test mode with 10 rows
    if len(sys.argv) > 1 and sys.argv[1] == "--single":
        # Test single chatbot
        chatbot = sys.argv[2] if len(sys.argv) > 2 else "copilot"
        await test_single_chatbot(chatbot)
    else:
        # Find latest V4 file
        v4_files = list(Path("synthetic_prompts").glob("synthetic_prompts_v4_enhanced_*.csv"))
        if not v4_files:
            print("ERROR: No V4 enhanced file found!")
            return
        
        latest_v4 = max(v4_files, key=lambda p: p.stat().st_mtime)
        print(f"Using input file: {latest_v4}")
        
        # Run evaluation on 10 rows
        agent = ChatbotEvaluationAgent(str(latest_v4))
        
        # Start with just Copilot to test
        await agent.run_evaluation(
            limit=10,
            chatbots=["copilot"]  # Start with one to test
        )


if __name__ == "__main__":
    asyncio.run(main())
