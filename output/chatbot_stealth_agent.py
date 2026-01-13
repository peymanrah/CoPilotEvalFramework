"""
=============================================================================
CHATBOT EVALUATION AGENT - STEALTH MODE
=============================================================================
Uses playwright-stealth to avoid bot detection.
Also uses persistent browser profile to appear more like a real user.

Best practices for avoiding detection:
1. Use playwright-stealth to hide automation fingerprints
2. Use persistent browser context (appears as returning user)
3. Add human-like delays and randomization
4. Use realistic viewport and user agent

Author: Evaluation Framework
Date: January 12, 2026
=============================================================================
"""

import asyncio
import csv
import json
import random
import time
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth


# =============================================================================
# CONFIGURATION
# =============================================================================

# Directory for persistent browser profile
BROWSER_PROFILE_DIR = Path("./browser_profile")

# Chatbot URLs
CHATBOT_URLS = {
    "copilot": "https://copilot.microsoft.com/",
    "chatgpt": "https://chatgpt.com/",
    "gemini": "https://gemini.google.com/app",
    "claude": "https://claude.ai/new"
}

# Selectors for each chatbot (will need adjustment based on current UI)
CHATBOT_SELECTORS = {
    "copilot": {
        "input": '#userInput, textarea[placeholder*="Message"]',
        "submit": 'button[aria-label*="Submit"], button[type="submit"]',
        "response": 'div[data-content="ai-message"], .prose, .markdown, [class*="response-text"]'
    },
    "chatgpt": {
        "input": '#prompt-textarea, textarea[data-id], div[contenteditable="true"][class*="ProseMirror"]',
        "submit": 'button[data-testid="send-button"], button[aria-label*="Send"]',
        "response": '[data-message-author-role="assistant"], .markdown, .prose'
    },
    "gemini": {
        "input": '.ql-editor, div[contenteditable="true"], rich-textarea textarea',
        "submit": 'button[aria-label*="Send"], button[mattooltip*="Send"]',
        "response": '.model-response-text, .response-container, .markdown-main-panel'
    },
    "claude": {
        "input": 'div[contenteditable="true"].ProseMirror, textarea',
        "submit": 'button[aria-label*="Send Message"], button:has(svg[class*="send"])',
        "response": '[data-testid="assistant-message"], .font-claude-message, .prose'
    }
}


# =============================================================================
# STEALTH BROWSER HANDLER
# =============================================================================

class StealthChatbotAgent:
    """
    Chatbot automation agent using stealth techniques to avoid detection.
    """
    
    def __init__(self):
        self.browser = None
        self.context = None
        self.results = []
        self.stealth = Stealth()  # Create stealth instance
        self.screenshot_base_dir = Path("evaluation_results/screenshots")
        
    async def initialize(self, headless: bool = False):
        """Initialize the stealth browser."""
        print("Initializing stealth browser...")
        
        # Create profile directory
        BROWSER_PROFILE_DIR.mkdir(exist_ok=True)
        
        playwright = await async_playwright().start()
        
        # Launch with specific args to reduce detection
        self.browser = await playwright.chromium.launch(
            headless=headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-infobars',
                '--window-position=0,0',
                '--ignore-certificate-errors',
                '--ignore-certificate-errors-spki-list',
            ]
        )
        
        # Use persistent context to appear as returning user
        self.context = await self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="en-US",
            timezone_id="America/New_York",
            # These make it look more like a real browser
            has_touch=False,
            is_mobile=False,
            device_scale_factor=1,
            # Accept all permissions
            permissions=["geolocation", "notifications"]
        )
        
        print("Browser initialized with stealth settings")
        return self
    
    async def _human_delay(self, min_ms: int = 500, max_ms: int = 2000):
        """Add human-like random delay."""
        delay = random.randint(min_ms, max_ms) / 1000
        await asyncio.sleep(delay)
    
    async def _check_for_bot_detection(self, page: Page) -> bool:
        """
        Check if we've been detected as a bot (human verification needed).
        Checks for:
        1. Text indicators in page body
        2. CAPTCHA iframes (Cloudflare, reCAPTCHA, hCaptcha)
        3. Verification buttons/overlays
        4. Blocked/challenge pages
        """
        try:
            body_text = await page.evaluate("() => document.body.innerText")
            body_text_lower = body_text.lower()
            
            # Text indicators of bot detection
            bot_indicators = [
                "verify you are human",
                "verify you're human",
                "human verification",
                "prove you're human",
                "prove you are human",
                "captcha",
                "security check",
                "unusual traffic",
                "automated access",
                "bot detected",
                "please verify",
                "confirm you're not a robot",
                "i'm not a robot",
                "i am not a robot",
                "checking your browser",
                "just a moment",
                "please wait while we verify",
                "complete the security check",
                "verify your identity",
                "challenge required",
                "access denied",
                "too many requests",
                "rate limited",
            ]
            for indicator in bot_indicators:
                if indicator in body_text_lower:
                    print(f"      🔍 Bot detection text found: '{indicator}'")
                    return True
            
            # Check for CAPTCHA iframes (Cloudflare turnstile, reCAPTCHA, hCaptcha)
            captcha_iframe_selectors = [
                'iframe[src*="challenges.cloudflare"]',
                'iframe[src*="turnstile"]',
                'iframe[src*="recaptcha"]',
                'iframe[src*="hcaptcha"]',
                'iframe[src*="captcha"]',
                'iframe[title*="challenge"]',
                'iframe[title*="reCAPTCHA"]',
                '#cf-turnstile',
                '.cf-turnstile',
                '.g-recaptcha',
                '.h-captcha',
            ]
            for selector in captcha_iframe_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            print(f"      🔍 CAPTCHA element found: '{selector}'")
                            return True
                except:
                    continue
            
            # Check for verification buttons (common patterns)
            verify_button_selectors = [
                'button:has-text("Verify")',
                'button:has-text("I am human")',
                'button:has-text("I\'m not a robot")',
                'input[type="checkbox"][id*="captcha"]',
                '[role="button"]:has-text("verify")',
                '.challenge-container',
                '#challenge-running',
                '#challenge-stage',
            ]
            for selector in verify_button_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            print(f"      🔍 Verification button found: '{selector}'")
                            return True
                except:
                    continue
            
            # Check for overlay/modal that might contain CAPTCHA
            overlay_selectors = [
                '[class*="challenge"]',
                '[class*="captcha"]',
                '[id*="challenge"]',
                '[id*="captcha"]',
                '.modal[style*="visible"]',
            ]
            for selector in overlay_selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        is_visible = await element.is_visible()
                        if is_visible:
                            box = await element.bounding_box()
                            # Only count if it's a significant size (not a tiny hidden element)
                            if box and box['width'] > 100 and box['height'] > 100:
                                print(f"      🔍 Challenge overlay found: '{selector}'")
                                return True
                except:
                    continue
                    
        except Exception as e:
            pass
        return False
    
    async def _capture_response_screenshots(self, page: Page, prompt_id: str, chatbot: str, response_text: str = "") -> List[str]:
        """
        Capture multiple screenshots of the response by scrolling.
        Uses smart detection: scrolls until the last chunk of response text is visible.
        This ensures we capture tables, formatting, and long responses completely.
        
        IMPORTANT: First scrolls to the response element, then scrolls down
        within the page to capture the complete response.
        
        Args:
            page: Playwright page
            prompt_id: Unique ID from synthetic_prompt_id for folder naming
            chatbot: Name of the chatbot
            response_text: The full response text to detect end of scrolling
        
        Returns list of screenshot file paths.
        """
        # Create directory for this prompt
        prompt_dir = self.screenshot_base_dir / prompt_id / chatbot
        prompt_dir.mkdir(parents=True, exist_ok=True)
        
        screenshot_paths = []
        
        # Extract last chunk of response for end detection (use last 80 chars, cleaned)
        last_chunk = ""
        if response_text and len(response_text) > 50:
            # Get last portion, clean up whitespace/newlines for matching
            last_chunk = response_text[-80:].replace('\n', ' ').replace('\r', '').strip()
            # Take meaningful last 40 chars for matching
            if len(last_chunk) > 40:
                last_chunk = last_chunk[-40:]
            print(f"   📸 End detection chunk: '...{last_chunk[-25:]}'")
        
        try:
            # Get viewport dimensions
            viewport_height = await page.evaluate("() => window.innerHeight")
            
            # Detect which chatbot we're on for specific handling
            is_gemini = chatbot.lower() == 'gemini'
            is_chatgpt = chatbot.lower() == 'chatgpt'
            is_copilot = chatbot.lower() == 'copilot'
            
            # Find the scrollable chat container for each chatbot
            # These are the containers that scroll when you scroll the chat, NOT the page
            # Order matters - check most specific first
            scroll_container_selectors = [
                # ChatGPT - main scrollable container (most specific first)
                '[class*="react-scroll-to-bottom"]',
                'main .overflow-y-auto',
                # Copilot - scrollable chat area
                '#app-container .overflow-auto',
                'cib-serp',
                # Gemini - scrollable container (try multiple patterns)
                '.conversation-container',
                '[class*="conversation"]',
                '.chat-history',
                # More specific scroll patterns
                '[class*="overflow-y"]',
                '[class*="scroll"]',
                # Generic fallbacks
                'main > div > div',
                'main',
                '[role="main"]',
                '.chat-container',
            ]
            
            scroll_container = None
            scroll_container_selector = None
            
            for selector in scroll_container_selectors:
                try:
                    container = await page.query_selector(selector)
                    if container:
                        # Check if this container is actually scrollable
                        is_scrollable = await page.evaluate(f"""
                            (selector) => {{
                                const el = document.querySelector(selector);
                                if (!el) return false;
                                return el.scrollHeight > el.clientHeight;
                            }}
                        """, selector)
                        if is_scrollable:
                            scroll_container = container
                            scroll_container_selector = selector
                            print(f"   📸 Found scrollable container: {selector}")
                            break
                except:
                    continue
            
            # GEMINI SPECIAL HANDLING: Find scrollable parent dynamically
            if is_gemini and not scroll_container:
                print(f"   📸 Gemini: Finding scrollable parent of response...")
                gemini_scroll_info = await page.evaluate("""
                    () => {
                        // First, find the response element
                        const response = document.querySelector('.model-response-text');
                        if (!response) return { found: false, error: 'No response element' };
                        
                        // Walk up the DOM tree to find a scrollable parent
                        let current = response.parentElement;
                        let depth = 0;
                        const maxDepth = 15;
                        
                        while (current && current !== document.body && depth < maxDepth) {
                            const style = window.getComputedStyle(current);
                            const overflowY = style.overflowY;
                            const isScrollable = current.scrollHeight > current.clientHeight + 50;
                            const hasOverflow = overflowY === 'auto' || overflowY === 'scroll' || overflowY === 'overlay';
                            
                            if (isScrollable && hasOverflow) {
                                // Found a scrollable parent - create a unique selector
                                let selector = current.tagName.toLowerCase();
                                
                                // Prefer data-test-id for unique identification
                                if (current.dataset && current.dataset.testId) {
                                    selector = `[data-test-id="${current.dataset.testId}"]`;
                                } else if (current.id) {
                                    selector = '#' + current.id;
                                } else {
                                    // For Gemini's infinite-scroller, use the tag name with class
                                    if (current.tagName.toLowerCase() === 'infinite-scroller') {
                                        selector = 'infinite-scroller.chat-history';
                                    } else if (current.className) {
                                        // Use first few non-empty classes with tag
                                        const classes = current.className.split(' ').filter(c => c && !c.includes(' '));
                                        if (classes.length > 0) {
                                            selector = current.tagName.toLowerCase() + '.' + classes[0];
                                        }
                                    }
                                }
                                
                                return {
                                    found: true,
                                    selector: selector,
                                    scrollHeight: current.scrollHeight,
                                    clientHeight: current.clientHeight,
                                    depth: depth,
                                    classes: current.className,
                                    tagName: current.tagName.toLowerCase()
                                };
                            }
                            
                            current = current.parentElement;
                            depth++;
                        }
                        
                        // If no scrollable parent found, check if window/document is scrollable
                        const docScrollable = document.documentElement.scrollHeight > window.innerHeight;
                        return { 
                            found: false, 
                            docScrollable: docScrollable,
                            docScrollHeight: document.documentElement.scrollHeight,
                            windowHeight: window.innerHeight
                        };
                    }
                """)
                
                if gemini_scroll_info.get('found'):
                    selector = gemini_scroll_info['selector']
                    print(f"   📸 Gemini: Found scrollable parent at depth {gemini_scroll_info['depth']}: {selector}")
                    print(f"   📸 Gemini: Container scroll={gemini_scroll_info['scrollHeight']}h, visible={gemini_scroll_info['clientHeight']}h")
                    scroll_container = await page.query_selector(selector)
                    if scroll_container:
                        scroll_container_selector = selector
                else:
                    print(f"   📸 Gemini: No scrollable parent found, will use element-based scrolling")
                    if gemini_scroll_info.get('docScrollable'):
                        print(f"   📸 Gemini: Document is scrollable ({gemini_scroll_info.get('docScrollHeight')}h)")
            
            # Find the response element
            response_selectors = [
                '[data-content="ai-message"]',  # Copilot
                '[data-message-author-role="assistant"]',  # ChatGPT
                '.model-response-text',  # Gemini
                '.response-container',
                '.markdown',
                '.prose'
            ]
            
            response_element = None
            response_selector_used = None
            for selector in response_selectors:
                try:
                    elements = await page.query_selector_all(selector)
                    if elements and len(elements) > 0:
                        # Get the last (most recent) response element
                        response_element = elements[-1]
                        response_selector_used = selector
                        print(f"   📸 Found response element: {selector}")
                        break
                except:
                    continue
            
            # Calculate screenshots needed based on response element's ACTUAL HEIGHT
            response_height = 0
            screenshots_needed = 1
            scroll_step = int(viewport_height * 0.70)
            
            if response_element:
                try:
                    # Get the bounding box of the response element
                    bounding_box = await response_element.bounding_box()
                    if bounding_box:
                        response_height = bounding_box['height']
                        
                        # Calculate how many screenshots we need
                        screenshots_needed = max(1, int((response_height / scroll_step) + 1))
                        
                        print(f"   📸 Response element: height={response_height:.0f}px, viewport={viewport_height}px")
                        print(f"   📸 Screenshots needed: {screenshots_needed} (scroll step: {scroll_step}px)")
                except Exception as e:
                    print(f"   📸 Could not get bounding box: {e}")
                    response_height = 0
            
            # If we couldn't get response height, estimate from text length
            if response_height == 0:
                # Rough estimate: ~60 chars per line, ~25px per line height
                estimated_lines = len(response_text) / 60 if response_text else 10
                response_height = estimated_lines * 25
                screenshots_needed = max(1, int((response_height / scroll_step) + 1))
                print(f"   📸 Estimated height from text: {response_height:.0f}px, screenshots: {screenshots_needed}")
            
            # Scroll to the TOP of the response first (within the container)
            if scroll_container and response_element:
                try:
                    # Scroll the response element into view at the top of the container
                    await response_element.evaluate("el => el.scrollIntoView({block: 'start', behavior: 'instant'})")
                    await asyncio.sleep(0.3)
                    print(f"   📸 Scrolled response into view at top")
                except Exception as e:
                    print(f"   📸 Could not scroll to response: {e}")
            elif is_gemini and response_element:
                # Gemini: No scroll container, scroll response into view at top
                try:
                    await response_element.evaluate("el => el.scrollIntoView({block: 'start', behavior: 'instant'})")
                    await asyncio.sleep(0.3)
                    print(f"   📸 Gemini: Scrolled response into view at top (no container)")
                except Exception as e:
                    print(f"   📸 Gemini: Could not scroll to response: {e}")
            
            # Now capture screenshots using TEXT-ANCHORED SCROLLING
            # This approach ensures no content is missed:
            # 1. Capture current view
            # 2. Find last visible paragraph/text in the response
            # 3. Scroll so that text appears at TOP with small overlap
            # 4. Capture next screenshot
            # 5. Repeat until we reach the end of the response
            
            max_screenshots = 15  # Safety cap
            screenshots_taken = 0
            last_captured_text = ""
            overlap_lines = 2  # Number of lines overlap for continuity
            
            # Track previously seen text to detect duplicates
            previous_visible_texts = []
            
            for i in range(max_screenshots):
                # Take screenshot at current position FIRST
                timestamp = datetime.now().strftime('%H%M%S')
                screenshot_path = prompt_dir / f"response_{i+1}_{timestamp}.png"
                
                await page.screenshot(path=str(screenshot_path), full_page=False)
                screenshot_paths.append(str(screenshot_path))
                screenshots_taken += 1
                
                # Get the currently visible text content in the response
                visible_text_info = await page.evaluate(f"""
                    (params) => {{
                        const responseSelector = params.responseSelector;
                        const containerSelector = params.containerSelector;
                        
                        // Find the response element
                        const responseElements = document.querySelectorAll(responseSelector);
                        if (!responseElements || responseElements.length === 0) {{
                            return {{ success: false, reason: 'no response element' }};
                        }}
                        const response = responseElements[responseElements.length - 1];
                        
                        // Get viewport bounds
                        const viewportHeight = window.innerHeight;
                        const viewportTop = 0;
                        const viewportBottom = viewportHeight;
                        
                        // Find all text-containing elements within the response
                        const textElements = response.querySelectorAll('p, li, h1, h2, h3, h4, h5, h6, pre, code, td, th, span.text, div.text');
                        
                        let lastVisibleText = '';
                        let lastVisibleElement = null;
                        let lastVisibleRect = null;
                        let allVisibleText = '';
                        let firstVisibleElement = null;
                        
                        // Find elements that are visible in the current viewport
                        for (const el of textElements) {{
                            const rect = el.getBoundingClientRect();
                            const text = el.innerText || el.textContent || '';
                            
                            // Skip empty elements
                            if (!text.trim()) continue;
                            
                            // Check if element is visible in viewport
                            const isVisible = rect.top < viewportBottom && rect.bottom > viewportTop && rect.height > 0;
                            
                            if (isVisible) {{
                                if (!firstVisibleElement) {{
                                    firstVisibleElement = el;
                                }}
                                allVisibleText += text.trim() + '\\n';
                                
                                // Track the last visible element (for scrolling to next section)
                                if (rect.bottom <= viewportBottom + 50) {{  // Fully visible or nearly so
                                    lastVisibleText = text.trim();
                                    lastVisibleElement = el;
                                    lastVisibleRect = {{
                                        top: rect.top,
                                        bottom: rect.bottom,
                                        height: rect.height
                                    }};
                                }}
                            }}
                        }}
                        
                        // Get the response element's position relative to container/viewport
                        const responseRect = response.getBoundingClientRect();
                        const isAtEnd = responseRect.bottom <= viewportBottom + 10;
                        
                        // Get container scroll info if available
                        let containerInfo = null;
                        if (containerSelector) {{
                            const container = document.querySelector(containerSelector);
                            if (container) {{
                                containerInfo = {{
                                    scrollTop: container.scrollTop,
                                    scrollHeight: container.scrollHeight,
                                    clientHeight: container.clientHeight,
                                    atEnd: container.scrollTop + container.clientHeight >= container.scrollHeight - 10
                                }};
                            }}
                        }}
                        
                        return {{
                            success: true,
                            lastVisibleText: lastVisibleText.substring(0, 200),
                            allVisibleTextPreview: allVisibleText.substring(0, 100),
                            allVisibleTextEnd: allVisibleText.substring(Math.max(0, allVisibleText.length - 100)),
                            lastVisibleRect: lastVisibleRect,
                            isAtEnd: isAtEnd,
                            containerInfo: containerInfo,
                            responseBottom: responseRect.bottom,
                            viewportHeight: viewportHeight
                        }};
                    }}
                """, {
                    'responseSelector': response_selector_used or '.model-response-text, [data-message-author-role="assistant"], [data-content="ai-message"]',
                    'containerSelector': scroll_container_selector
                })
                
                # Check if we've reached the end of the response
                if visible_text_info.get('success'):
                    current_visible_text = visible_text_info.get('allVisibleTextEnd', '')
                    is_at_end = visible_text_info.get('isAtEnd', False)
                    container_info = visible_text_info.get('containerInfo')
                    
                    # For Gemini, only trust the container scroll position, not the element position
                    # The isAtEnd check based on element rect can trigger prematurely
                    if is_gemini:
                        # Only check container scroll position for Gemini
                        if container_info:
                            scroll_progress = container_info.get('scrollTop', 0) + container_info.get('clientHeight', 0)
                            total_scroll = container_info.get('scrollHeight', 0)
                            if container_info.get('atEnd'):
                                print(f"   📸 Gemini: Container reached end ({scroll_progress}/{total_scroll}) - captured {screenshots_taken} screenshots")
                                break
                            # Debug: Show progress
                            if i > 0:
                                print(f"   📸 Gemini: Scroll progress {scroll_progress}/{total_scroll}px")
                        else:
                            # No container info - rely on duplicate detection
                            pass
                    else:
                        # For other chatbots, use either check
                        if is_at_end or (container_info and container_info.get('atEnd')):
                            print(f"   📸 Reached end of response - captured {screenshots_taken} screenshots")
                            break
                    
                    # Check for duplicate content (same text as before = no scroll happened)
                    if current_visible_text in previous_visible_texts and i > 0:
                        print(f"   📸 Duplicate content detected - stopping at {screenshots_taken} screenshots")
                        break
                    
                    previous_visible_texts.append(current_visible_text)
                    
                    # Check if the response text ends with expected ending
                    # SKIP for Gemini - this can trigger false positives
                    if not is_gemini and response_text and last_chunk:
                        if last_chunk[-20:] in current_visible_text:
                            print(f"   📸 Found response end marker - captured {screenshots_taken} screenshots")
                            break
                
                # SCROLL TO NEXT SECTION using text-anchored approach
                # Scroll so the last visible text appears at the top with some overlap
                if scroll_container:
                    try:
                        # Use the last visible text to anchor the scroll
                        scroll_success = await page.evaluate(f"""
                            (params) => {{
                                const containerSelector = params.containerSelector;
                                const responseSelector = params.responseSelector;
                                const overlapPx = params.overlapPx;
                                
                                const container = document.querySelector(containerSelector);
                                if (!container) return {{ success: false, reason: 'no container' }};
                                
                                const response = document.querySelectorAll(responseSelector);
                                if (!response || response.length === 0) return {{ success: false, reason: 'no response' }};
                                
                                const responseEl = response[response.length - 1];
                                const responseRect = responseEl.getBoundingClientRect();
                                
                                // Calculate scroll amount: viewport height minus overlap
                                const viewportHeight = window.innerHeight;
                                const scrollAmount = viewportHeight - overlapPx;
                                
                                // Store current position
                                const beforeScroll = container.scrollTop;
                                
                                // Scroll by the calculated amount
                                container.scrollBy(0, scrollAmount);
                                
                                // Return result
                                return {{
                                    success: true,
                                    beforeScroll: beforeScroll,
                                    afterScroll: container.scrollTop,
                                    scrollAmount: scrollAmount
                                }};
                            }}
                        """, {
                            'containerSelector': scroll_container_selector,
                            'responseSelector': response_selector_used or '.model-response-text',
                            'overlapPx': 150  # 150px overlap for continuity
                        })
                        
                        await asyncio.sleep(0.4)
                        
                        # Verify scroll happened
                        if scroll_success.get('success'):
                            if scroll_success.get('beforeScroll') == scroll_success.get('afterScroll'):
                                # Try mouse wheel as fallback for Gemini
                                if is_gemini and scroll_container:
                                    try:
                                        container_box = await scroll_container.bounding_box()
                                        if container_box:
                                            center_x = container_box['x'] + container_box['width'] / 2
                                            center_y = container_box['y'] + container_box['height'] / 2
                                            await page.mouse.move(center_x, center_y)
                                            await asyncio.sleep(0.1)
                                            await page.mouse.wheel(0, viewport_height - 150)
                                            await asyncio.sleep(0.4)
                                    except:
                                        pass
                                else:
                                    print(f"   📸 Container scroll limit reached at {screenshots_taken}")
                                    break
                    except Exception as e:
                        print(f"   📸 Scroll error: {e}")
                        break
                else:
                    # No container - use page scroll with text-anchored approach
                    try:
                        scroll_amount = viewport_height - 150  # 150px overlap
                        current_scroll = await page.evaluate("() => window.scrollY")
                        await page.evaluate(f"() => window.scrollBy(0, {scroll_amount})")
                        await asyncio.sleep(0.3)
                        new_scroll = await page.evaluate("() => window.scrollY")
                        if new_scroll == current_scroll:
                            print(f"   📸 Page scroll limit reached at {screenshots_taken}")
                            break
                    except Exception as e:
                        print(f"   📸 Page scroll error: {e}")
                        break
            
            if screenshots_taken >= 15:
                print(f"   ⚠️ Hit max screenshots (15)")
            
            print(f"   📸 Saved {len(screenshot_paths)} screenshots to {prompt_dir}")
            
        except Exception as e:
            print(f"   ⚠️ Screenshot capture error: {e}")
            # Try a single full-page screenshot as fallback
            try:
                fallback_path = prompt_dir / f"response_full.png"
                await page.screenshot(path=str(fallback_path), full_page=True)
                screenshot_paths.append(str(fallback_path))
                print(f"   📸 Saved fallback full-page screenshot")
            except:
                pass
        
        return screenshot_paths
    
    async def _human_type(self, page: Page, element, text: str):
        """Type text with human-like behavior but faster."""
        await element.click()
        await self._human_delay(300, 600)
        
        # For longer texts, use fill() which is much faster
        # but add human-like pauses around it
        if len(text) > 100:
            # Clear any existing text first
            await element.fill("")
            await self._human_delay(100, 200)
            
            # Fill with the text
            await element.fill(text)
            await self._human_delay(500, 1000)
        else:
            # For short texts, type character by character
            for char in text:
                await page.keyboard.type(char, delay=random.randint(30, 80))
            await self._human_delay(300, 500)
    
    async def query_chatbot(self, chatbot: str, full_prompt: str, prompt_id: str = None) -> tuple:
        """
        Query a chatbot and get the response.
        IMPORTANT: Page stays open until full response is received.
        
        Args:
            chatbot: One of 'copilot', 'chatgpt', 'gemini', 'claude'
            full_prompt: The complete prompt to send (pre-built, identical for all chatbots)
            prompt_id: ID for organizing screenshots
            
        Returns:
            Tuple of (response_text, screenshot_paths, was_bot_detected, response_time_seconds)
        """
        if chatbot not in CHATBOT_URLS:
            return f"ERROR: Unknown chatbot '{chatbot}'", [], False, 0.0
        
        url = CHATBOT_URLS[chatbot]
        selectors = CHATBOT_SELECTORS[chatbot]
        
        print(f"\n{'='*60}")
        print(f"Querying {chatbot.upper()}")
        print(f"{'='*60}")
        
        # Create new page
        page = await self.context.new_page()
        
        # Apply stealth to the page
        await self.stealth.apply_stealth_async(page)
        
        response_text = "ERROR: Unknown error"
        screenshot_paths = []
        was_bot_detected = False
        response_time_seconds = 0.0  # Time from submit to full response received
        
        try:
            # Navigate
            print(f"1. Navigating to {url}...")
            await page.goto(url, wait_until="domcontentloaded", timeout=60000)
            
            # Human-like wait for page load
            await self._human_delay(3000, 5000)
            
            # Check for bot detection EARLY
            if await self._check_for_bot_detection(page):
                print("   ⚠️ BOT DETECTION: Human verification required!")
                await page.screenshot(path=f"debug_{chatbot}_bot_detected.png")
                was_bot_detected = True
                response_text = "ERROR: Bot detected - human verification required"
                await page.close()
                return response_text, [], was_bot_detected, 0.0
            
            # Take debug screenshot
            await page.screenshot(path=f"debug_{chatbot}_step1.png")
            
            # Look for input field
            print("2. Looking for input field...")
            input_element = None
            
            for selector in selectors["input"].split(", "):
                try:
                    input_element = await page.wait_for_selector(selector, timeout=5000, state="visible")
                    if input_element:
                        print(f"   Found input: {selector}")
                        break
                except:
                    continue
            
            if not input_element:
                # Check if this is due to bot detection
                if await self._check_for_bot_detection(page):
                    print("   ⚠️ BOT DETECTION: Human verification required!")
                    was_bot_detected = True
                    response_text = "ERROR: Bot detected - human verification required"
                else:
                    await page.screenshot(path=f"debug_{chatbot}_no_input.png")
                    response_text = "ERROR: Could not find input field"
                await page.close()
                return response_text, [], was_bot_detected, 0.0
            
            # Type the pre-built prompt (identical for all chatbots)
            print("3. Typing prompt...")
            await self._human_type(page, input_element, full_prompt)
            
            await page.screenshot(path=f"debug_{chatbot}_step2_filled.png")
            await self._human_delay(500, 1000)
            
            # Submit - click the submit button with force=True to bypass any overlays
            print("4. Submitting...")
            
            submitted = False
            # Try clicking submit button with force=True (bypasses overlay interception)
            try:
                submit_btn = await page.wait_for_selector('button[aria-label="Submit message"]', timeout=3000)
                if submit_btn:
                    await submit_btn.click(force=True)
                    print("   ✓ Clicked submit button (force=True)")
                    submitted = True
            except:
                pass
            
            # Fallback to Enter key
            if not submitted:
                await input_element.focus()
                await self._human_delay(200, 400)
                await page.keyboard.press("Enter")
                print("   Pressed Enter key (fallback)")
            
            # IMMEDIATE BOT CHECK: Check right after submission (before waiting)
            await asyncio.sleep(1.5)  # Brief wait for any CAPTCHA to appear
            if await self._check_for_bot_detection(page):
                print("   ⚠️ BOT DETECTION: CAPTCHA appeared immediately after submission!")
                await page.screenshot(path=f"debug_{chatbot}_bot_detected_submit.png")
                was_bot_detected = True
                response_text = "ERROR: Bot detected - CAPTCHA appeared after submission"
                await page.close()
                return response_text, [], was_bot_detected, 0.0
            
            # Wait for response - CRITICAL: Don't exit until full response received
            # Returns tuple: (response_text, accurate_latency_seconds)
            print("5. Waiting for response (will wait up to 120s for full response)...")
            response_text, response_time_seconds = await self._wait_for_response(page, selectors["response"], full_prompt, timeout=120)
            
            # Round the high-resolution latency for display
            response_time_seconds = round(response_time_seconds, 2)
            print(f"   ⏱️ Response time (high-res latency): {response_time_seconds}s")
            
            # Check if bot detection occurred during waiting
            if await self._check_for_bot_detection(page):
                print("   ⚠️ BOT DETECTION during response wait!")
                was_bot_detected = True
                if response_text.startswith("ERROR"):
                    response_text = "ERROR: Bot detected - human verification required"
            
            # Capture screenshots of the response ONLY after confirming full response
            if prompt_id and not response_text.startswith("ERROR"):
                # Wait a moment to ensure response is fully rendered on screen
                print("6. Confirming response is fully rendered...")
                await asyncio.sleep(1.5)  # Allow UI to fully render
                
                print("7. Capturing response screenshots (scrolling through full response)...")
                screenshot_paths = await self._capture_response_screenshots(page, prompt_id, chatbot, response_text)
            
            # Validate response
            if not response_text.startswith("ERROR"):
                await page.screenshot(path=f"debug_{chatbot}_step3_response.png")
                print(f"   ✓ Got valid response ({len(response_text)} chars)")
            else:
                await page.screenshot(path=f"debug_{chatbot}_error_response.png")
                print(f"   ❌ {response_text}")
            
        except Exception as e:
            await page.screenshot(path=f"debug_{chatbot}_error.png")
            response_text = f"ERROR: {str(e)}"
        
        # Close page only AFTER response is fully captured
        await page.close()
        
        return response_text, screenshot_paths, was_bot_detected, response_time_seconds
    
    async def _wait_for_response(self, page: Page, response_selector: str, original_prompt: str, timeout: int = 120) -> tuple:
        """
        Wait for and extract the chatbot response using smart completion detection.
        
        Uses TWO separate measurements:
        1. LATENCY (high-resolution): Fast 0.2s polling to detect exact moment text stops growing
        2. COMPLETENESS: Wait 8s stability threshold to confirm response is truly finished
        
        Args:
            page: Playwright page
            response_selector: CSS selectors for response element
            original_prompt: The prompt sent (to filter out echoes)
            timeout: Maximum wait time in seconds (safety cap)
        
        Returns:
            Tuple of (response_text, accurate_latency_seconds)
        """
        start_time = time.time()
        last_response = ""
        last_response_time = time.time()  # For stability confirmation
        last_growth_time = time.time()  # High-resolution tracking for latency
        accurate_latency = 0.0  # The moment text stopped growing
        latency_captured = False  # Flag to capture latency only once
        
        # Smart detection settings - TWO MODES
        # Mode 1: Fast polling for accurate latency measurement
        FAST_POLL_INTERVAL = 0.2  # 200ms for high-resolution latency capture
        # Mode 2: Stability confirmation for completeness
        STABILITY_THRESHOLD = 8  # Response stable for 8 seconds = complete
        MIN_RESPONSE_LENGTH = 30  # Minimum chars before considering stable
        BOT_CHECK_INTERVAL = 5  # Check for bot every 5 seconds
        last_bot_check = 0
        
        print(f"   Smart detection: high-res latency (0.2s poll) + {STABILITY_THRESHOLD}s stability confirmation")
        
        while time.time() - start_time < timeout:
            await asyncio.sleep(FAST_POLL_INTERVAL)
            elapsed = time.time() - start_time
            
            # Periodic bot detection check to fail fast
            if elapsed - last_bot_check >= BOT_CHECK_INTERVAL:
                last_bot_check = elapsed
                try:
                    if await self._check_for_bot_detection(page):
                        print(f"   ⚠️ BOT DETECTION during response wait (at {elapsed:.1f}s)!")
                        return "ERROR: Bot detected - human verification required", 0.0
                except:
                    pass
            
            try:
                # Check if still loading (spinner, animation, etc.)
                is_loading = await self._is_loading(page)
                
                # Extract full page text
                body_text = await page.evaluate("() => document.body.innerText")
                current_response = ""
                
                # Look for "Copilot said" pattern (for Copilot)
                if "Copilot said" in body_text:
                    parts = body_text.split("Copilot said")
                    if len(parts) > 1:
                        current_response = parts[-1].strip()
                        
                        # Clean up: stop at common end markers
                        end_markers = ["You said", "Smart", "Today", "Message Copilot"]
                        for marker in end_markers:
                            if marker in current_response:
                                current_response = current_response.split(marker)[0].strip()
                
                # Fallback: Try selectors for other chatbots (ChatGPT, Gemini)
                if not current_response or len(current_response) < MIN_RESPONSE_LENGTH:
                    for selector in response_selector.split(", "):
                        try:
                            elements = await page.query_selector_all(selector)
                            if elements:
                                text = await elements[-1].inner_text()
                                if text and len(text) > len(current_response):
                                    # Filter out if it contains the prompt (echo)
                                    if original_prompt[:30] not in text:
                                        current_response = text
                        except:
                            continue
                
                # Skip if still loading indicators present
                if "Thinking" in current_response or "Generating" in current_response:
                    last_response = ""  # Reset stability on loading
                    last_response_time = time.time()
                    continue
                
                # Check if response is too short
                if len(current_response) < MIN_RESPONSE_LENGTH:
                    continue
                
                # SMART STABILITY CHECK: Has response changed?
                if current_response == last_response:
                    # Response unchanged - check how long it's been stable
                    stable_duration = time.time() - last_response_time
                    time_since_last_growth = time.time() - last_growth_time
                    
                    # HIGH-RESOLUTION LATENCY: Capture the moment text stopped growing (0.5s threshold)
                    if not latency_captured and time_since_last_growth >= 0.5 and len(current_response) >= MIN_RESPONSE_LENGTH:
                        accurate_latency = last_growth_time - start_time
                        latency_captured = True
                        print(f"   ⏱️ Latency captured: {accurate_latency:.2f}s (text stopped growing)")
                    
                    # COMPLETENESS: If stable for threshold, we're done!
                    # IMPORTANT: Don't require is_loading=False - if text hasn't changed for 8s,
                    # the response IS complete regardless of loading indicators (which can be false positives)
                    if stable_duration >= STABILITY_THRESHOLD:
                        # Use the accurate latency we captured, or calculate now if not captured
                        final_latency = accurate_latency if latency_captured else (time.time() - start_time - STABILITY_THRESHOLD)
                        print(f"   ✓ Response complete! Stable for {stable_duration:.1f}s ({len(current_response)} chars)")
                        return current_response.strip(), final_latency
                    
                    # Show progress (less frequently since we poll faster now)
                    if int(elapsed) % 5 == 0 and int(elapsed) > 0 and int(elapsed * 5) % 5 == 0:
                        if is_loading and stable_duration < 3:
                            print(f"   Still generating... ({elapsed:.0f}s, {len(current_response)} chars so far)")
                        elif stable_duration >= 1.0:
                            print(f"   Confirming completion... ({stable_duration:.1f}s/{STABILITY_THRESHOLD}s stable)")
                else:
                    # Response changed - reset stability timer AND update growth time
                    prev_len = len(last_response) if last_response else 0
                    last_response = current_response
                    last_response_time = time.time()
                    last_growth_time = time.time()  # Track exact moment of last growth
                    latency_captured = False  # Reset latency capture if text grows again
                    
                    # Show progress every 3s for ALL chatbots equally (fair evaluation)
                    if int(elapsed) % 3 == 0 and int(elapsed) > 0:
                        growth_rate = (len(current_response) - prev_len)
                        print(f"   📝 Response growing... ({elapsed:.0f}s, {len(current_response)} chars, +{growth_rate})")
                        
            except Exception as e:
                pass
        
        # Timeout reached - return what we have
        if last_response and len(last_response) >= MIN_RESPONSE_LENGTH:
            final_latency = accurate_latency if latency_captured else (time.time() - start_time)
            print(f"   ⚠️ Timeout, returning partial response ({len(last_response)} chars)")
            return last_response.strip(), final_latency
        
        return "ERROR: Timeout waiting for response", 0.0
    
    async def _is_loading(self, page: Page) -> bool:
        """Check if the chatbot is still generating a response."""
        # Check for common loading/generating indicators
        loading_indicators = [
            '.loading', 
            '.generating', 
            '.typing',
            '.thinking',
            '[aria-busy="true"]', 
            '.cursor-blink',
            'svg.animate-spin', 
            '.animate-pulse',
            '.streaming',
            '[data-state="streaming"]',
            '.response-streaming',
        ]
        
        for indicator in loading_indicators:
            try:
                el = await page.query_selector(indicator)
                if el and await el.is_visible():
                    return True
            except:
                pass
        
        # Also check for text-based loading indicators in the response area
        try:
            body_text = await page.evaluate("() => document.body.innerText")
            loading_texts = ["Generating", "Thinking", "Searching", "Analyzing", "..."]
            # Only check if these appear at the END of the visible text (indicating still loading)
            last_100_chars = body_text[-100:] if len(body_text) > 100 else body_text
            for loading_text in loading_texts:
                if loading_text in last_100_chars:
                    return True
        except:
            pass
        
        return False
    
    async def close(self):
        """Close the browser properly with asyncio cleanup."""
        if self.browser:
            try:
                # Close all pages first
                for context in self.browser.contexts:
                    for page in context.pages:
                        try:
                            await page.close()
                        except:
                            pass
                    try:
                        await context.close()
                    except:
                        pass
                # Then close the browser
                await self.browser.close()
                # Give asyncio time to clean up
                await asyncio.sleep(0.5)
            except Exception as e:
                pass  # Suppress cleanup warnings


# =============================================================================
# EVALUATION RUNNER
# =============================================================================

async def run_evaluation(input_csv: str, limit: int = 10, chatbots: List[str] = None, max_retries: int = 3):
    """
    Run evaluation on prompts from CSV using ROUND-ROBIN approach.
    
    Instead of querying one chatbot multiple times in a row (which triggers bot detection),
    we query all chatbots with the same prompt before moving to the next prompt.
    This ensures significant time gap between sequential queries to the same chatbot.
    
    After initial pass, retries any bot-detected entries up to max_retries times.
    """
    if chatbots is None:
        # All 3 chatbots that work without sign-in
        chatbots = ["copilot", "chatgpt", "gemini"]
    
    print("=" * 70)
    print("CHATBOT EVALUATION - STEALTH MODE (ROUND-ROBIN)")
    print("=" * 70)
    
    # Load prompts
    print(f"\nLoading prompts from: {input_csv}")
    rows = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            if i >= limit:
                break
            rows.append(row)
    
    print(f"Loaded {len(rows)} prompts")
    print(f"Chatbots to query: {chatbots}")
    print(f"Strategy: Round-robin (query each chatbot per prompt before moving to next)")
    
    # Initialize agent
    agent = StealthChatbotAgent()
    await agent.initialize(headless=False)
    
    # Delay settings to avoid bot detection (reduced by half for faster execution)
    DELAY_BETWEEN_CHATBOTS = 5   # seconds between querying different chatbots
    DELAY_BETWEEN_PROMPTS = 15   # seconds between prompts (gives each chatbot ~15s gap)
    
    # Statistics tracking
    stats = {
        "total_queries": 0,
        "successful_responses": 0,
        "bot_detections": 0,
        "errors": 0
    }
    
    try:
        # ROUND-ROBIN: For each prompt, query ALL chatbots before moving to next prompt
        for idx, row in enumerate(rows):
            print(f"\n{'#'*70}")
            print(f"Processing Prompt {idx + 1}/{len(rows)}")
            print(f"{'#'*70}")
            
            # Use synthetic_prompt_id from V4 CSV for folder naming (unique identifier)
            prompt_id = row.get("synthetic_prompt_id", f"SP_{idx+1:06d}")
            
            prompt = row.get("synthetic_prompt", "")
            context_url = row.get("context_url", "")
            context_text = row.get("context_text", "")
            
            # Build the FULL PROMPT ONCE before chatbot loop - ensures identical prompt for ALL chatbots
            # This is critical for fair evaluation - every chatbot must receive EXACTLY the same input
            if context_url:
                context = f"Reference: {context_url}"
            elif context_text and len(context_text) > 50:
                context = context_text[:1500]  # Consistent truncation
            else:
                context = ""
            
            # Build full prompt with context (same for ALL chatbots)
            if context:
                full_prompt = f"Context: {context}\n\n---\n\n{prompt}"
            else:
                full_prompt = prompt
            
            # Truncate to max length (same for ALL chatbots)
            full_prompt = full_prompt[:2000]
            
            # Store the exact prompt sent for audit/verification
            row["prompt_sent"] = full_prompt
            row["prompt_length"] = str(len(full_prompt))
            
            print(f"Prompt ID: {prompt_id}")
            print(f"Prompt length: {len(full_prompt)} chars (same for all chatbots)")
            print(f"Prompt preview: {prompt[:80]}...")
            
            # Query EACH chatbot with this prompt (round-robin)
            for chatbot_idx, chatbot in enumerate(chatbots):
                print(f"\n--- Chatbot {chatbot_idx + 1}/{len(chatbots)}: {chatbot.upper()} ---")
                
                stats["total_queries"] += 1
                
                # Query with pre-built full_prompt (identical for all chatbots)
                response, screenshot_paths, was_bot_detected, response_time = await agent.query_chatbot(
                    chatbot, full_prompt, prompt_id=prompt_id
                )
                
                # Store results
                row[f"response_{chatbot}"] = response
                row[f"screenshots_{chatbot}"] = ";".join(screenshot_paths) if screenshot_paths else ""
                row[f"bot_detected_{chatbot}"] = str(was_bot_detected)
                row[f"response_time_seconds_{chatbot}"] = str(response_time)
                
                # Update stats and preview response
                if was_bot_detected:
                    stats["bot_detections"] += 1
                    print(f"   ⚠️ BOT DETECTION ENCOUNTERED")
                elif response.startswith("ERROR"):
                    stats["errors"] += 1
                    print(f"   ❌ {response}")
                else:
                    stats["successful_responses"] += 1
                    preview = response[:150].replace('\n', ' ')
                    print(f"   ✓ Got response ({len(response)} chars) in {response_time}s: {preview}...")
                    if screenshot_paths:
                        print(f"   📸 Captured {len(screenshot_paths)} screenshot(s)")
                
                # Delay between chatbots (to look human)
                if chatbot_idx < len(chatbots) - 1:
                    print(f"   ⏳ Waiting {DELAY_BETWEEN_CHATBOTS}s before next chatbot...")
                    await asyncio.sleep(DELAY_BETWEEN_CHATBOTS)
            
            # Save intermediate results after each prompt
            save_results(rows[:idx+1], "evaluation_results")
            print(f"\n   💾 Progress saved ({idx+1}/{len(rows)} prompts completed)")
            
            # Print running stats
            success_rate = (stats["successful_responses"] / stats["total_queries"] * 100) if stats["total_queries"] > 0 else 0
            print(f"   📊 Stats: {stats['successful_responses']}/{stats['total_queries']} successful ({success_rate:.1f}%), {stats['bot_detections']} bot detections")
            
            # Longer delay between prompts (to space out requests to each chatbot)
            if idx < len(rows) - 1:
                print(f"\n   ⏳ Waiting {DELAY_BETWEEN_PROMPTS}s before next prompt (anti-bot measure)...")
                await asyncio.sleep(DELAY_BETWEEN_PROMPTS)
        
        # =================================================================
        # RETRY PASS: Revisit entries with bot detection and retry
        # =================================================================
        for retry_round in range(1, max_retries + 1):
            # Find all entries that need retry (bot_detected = True)
            retry_needed = []
            for idx, row in enumerate(rows):
                for chatbot in chatbots:
                    if row.get(f"bot_detected_{chatbot}") == "True":
                        retry_needed.append((idx, row, chatbot))
            
            if not retry_needed:
                print(f"\n✓ No bot detections remaining - all queries successful!")
                break
            
            print(f"\n{'='*70}")
            print(f"RETRY PASS {retry_round}/{max_retries} - {len(retry_needed)} queries need retry")
            print(f"{'='*70}")
            
            # Wait before retry pass to reduce bot detection (reduced by half)
            print(f"⏳ Waiting 30s before retry pass (to reset bot detection)...")
            await asyncio.sleep(30)
            
            for retry_idx, (row_idx, row, chatbot) in enumerate(retry_needed):
                print(f"\n--- Retry {retry_idx + 1}/{len(retry_needed)}: {row.get('synthetic_prompt_id')} -> {chatbot.upper()} ---")
                
                # Get the same full_prompt that was used before (stored in prompt_sent)
                full_prompt = row.get("prompt_sent", row.get("synthetic_prompt", ""))
                prompt_id = row.get("synthetic_prompt_id", f"SP_{row_idx+1:06d}")
                
                stats["total_queries"] += 1
                
                # Retry the query
                response, screenshot_paths, was_bot_detected, response_time = await agent.query_chatbot(
                    chatbot, full_prompt, prompt_id=prompt_id
                )
                
                # Update results
                row[f"response_{chatbot}"] = response
                row[f"screenshots_{chatbot}"] = ";".join(screenshot_paths) if screenshot_paths else ""
                row[f"bot_detected_{chatbot}"] = str(was_bot_detected)
                row[f"response_time_seconds_{chatbot}"] = str(response_time)
                row[f"retry_count_{chatbot}"] = str(retry_round)
                
                # Update stats
                if was_bot_detected:
                    stats["bot_detections"] += 1
                    print(f"   ⚠️ Still bot detected (will retry next round if available)")
                elif response.startswith("ERROR"):
                    stats["errors"] += 1
                    print(f"   ❌ {response}")
                else:
                    stats["successful_responses"] += 1
                    preview = response[:100].replace('\\n', ' ')
                    print(f"   ✓ RETRY SUCCESS! Got response ({len(response)} chars) in {response_time}s")
                    if screenshot_paths:
                        print(f"   📸 Captured {len(screenshot_paths)} screenshot(s)")
                
                # Delay between retries
                if retry_idx < len(retry_needed) - 1:
                    print(f"   ⏳ Waiting {DELAY_BETWEEN_CHATBOTS}s before next retry...")
                    await asyncio.sleep(DELAY_BETWEEN_CHATBOTS)
            
            # Save after each retry round
            save_results(rows, "evaluation_results")
            print(f"\n💾 Saved after retry round {retry_round}")
        
    finally:
        # DON'T close browser prematurely - only after all responses collected
        print("\n" + "="*70)
        print("All prompts processed. Closing browser...")
        print("="*70)
        await agent.close()
    
    # Final stats
    print("\n" + "="*70)
    print("FINAL STATISTICS")
    print("="*70)
    print(f"Total queries: {stats['total_queries']}")
    print(f"Successful responses: {stats['successful_responses']}")
    print(f"Bot detections: {stats['bot_detections']}")
    print(f"Errors: {stats['errors']}")
    success_rate = (stats["successful_responses"] / stats["total_queries"] * 100) if stats["total_queries"] > 0 else 0
    print(f"Success rate: {success_rate:.1f}%")
    
    # Final save
    output_path = save_results(rows, "evaluation_results")
    print(f"\n✓ Results saved to: {output_path}")
    
    return rows


def save_results(rows: List[Dict], output_dir: str) -> str:
    """Save results to a single consolidated CSV file.
    
    Output: evaluation_results/evaluation_consolidated.csv
    
    This file contains ALL original V4 columns PLUS:
    - prompt_sent, prompt_length
    - response_copilot, response_chatgpt, response_gemini (FULL TEXT responses)
    - screenshots_copilot, screenshots_chatgpt, screenshots_gemini (paths)
    - bot_detected_copilot, bot_detected_chatgpt, bot_detected_gemini
    - response_time_seconds_copilot, response_time_seconds_chatgpt, response_time_seconds_gemini
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    # Single consolidated file - overwrites each run with latest results
    csv_path = Path(output_dir) / "evaluation_consolidated.csv"
    
    if rows:
        fieldnames = list(rows[0].keys())
        
        # Try to save, with fallback to timestamped file if permission denied
        for attempt in range(3):
            try:
                with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(rows)
                
                print(f"\n📄 Saved consolidated results to: {csv_path}")
                print(f"   Columns with full responses: response_copilot, response_chatgpt, response_gemini")
                return str(csv_path)
            except PermissionError:
                if attempt < 2:
                    print(f"\n⚠️ File is locked, retrying in 2s... (close Excel if open)")
                    import time
                    time.sleep(2)
                else:
                    # Fall back to timestamped file
                    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    csv_path = Path(output_dir) / f"evaluation_consolidated_{timestamp}.csv"
                    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(rows)
                    print(f"\n⚠️ Original file locked. Saved to: {csv_path}")
                    print(f"   Columns with full responses: response_copilot, response_chatgpt, response_gemini")
                    return str(csv_path)
    
    return str(csv_path)


# =============================================================================
# MAIN
# =============================================================================

async def main():
    import sys
    
    # Find latest V4 file
    v4_files = list(Path("synthetic_prompts").glob("synthetic_prompts_v4_enhanced_*.csv"))
    if not v4_files:
        print("ERROR: No V4 enhanced file found!")
        return
    
    latest_v4 = max(v4_files, key=lambda p: p.stat().st_mtime)
    
    # Get limit from command line
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    
    # Check for --chatbots flag
    chatbots_to_use = ["copilot", "chatgpt", "gemini"]
    for i, arg in enumerate(sys.argv):
        if arg == "--chatbots" and i + 1 < len(sys.argv):
            chatbots_to_use = [cb.strip().lower() for cb in sys.argv[i+1].split(",")]
            # Validate chatbots
            valid_chatbots = []
            for cb in chatbots_to_use:
                if cb in ["copilot", "chatgpt", "gemini", "claude"]:
                    valid_chatbots.append(cb)
                else:
                    print(f"Warning: Unknown chatbot '{cb}', skipping")
            chatbots_to_use = valid_chatbots if valid_chatbots else ["copilot", "chatgpt", "gemini"]
            break
    
    # Run evaluation
    await run_evaluation(
        str(latest_v4),
        limit=limit,
        chatbots=chatbots_to_use,
        max_retries=3  # Retry bot-detected entries up to 3 times
    )


if __name__ == "__main__":
    asyncio.run(main())
