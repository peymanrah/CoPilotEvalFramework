"""
Test different submission methods for Copilot.
"""
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import time

async def test_submission_methods():
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        
        context = await browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        page = await context.new_page()
        stealth = Stealth()
        await stealth.apply_stealth_async(page)
        
        print("1. Navigating to Copilot...")
        await page.goto('https://copilot.microsoft.com/', wait_until='domcontentloaded')
        await asyncio.sleep(4)
        
        # Take screenshot
        await page.screenshot(path="submit_test_initial.png")
        
        print("2. Finding input...")
        input_el = await page.wait_for_selector('#userInput', timeout=10000)
        
        if input_el:
            prompt = "Hello"
            print(f"3. Typing: {prompt}")
            await input_el.fill(prompt)
            await asyncio.sleep(1)
            
            await page.screenshot(path="submit_test_filled.png")
            
            # Method 1: Look for submit button with different selectors
            print("\n4. Looking for submit button...")
            submit_selectors = [
                'button[aria-label*="Submit"]',
                'button[aria-label="Submit message"]',
                'button[type="submit"]',
                '#submitButton',
                'button.submit',
                'button svg[class*="send"]',
                'form button:last-child',
                'button:has(svg)',  # Button with SVG icon
            ]
            
            for sel in submit_selectors:
                try:
                    btns = await page.query_selector_all(sel)
                    if btns:
                        for btn in btns:
                            is_visible = await btn.is_visible()
                            label = await btn.get_attribute('aria-label') or ""
                            html = await btn.evaluate("el => el.outerHTML")
                            print(f"   {sel}: visible={is_visible}, label='{label}'")
                            print(f"      HTML: {html[:200]}...")
                except Exception as e:
                    pass
            
            # Method 2: Try clicking with force
            print("\n5. Trying to click submit button with force=True...")
            try:
                submit_btn = await page.wait_for_selector('button[aria-label="Submit message"]', timeout=3000)
                if submit_btn:
                    await submit_btn.click(force=True)
                    print("   Clicked with force=True!")
            except Exception as e:
                print(f"   Failed: {e}")
            
            await asyncio.sleep(2)
            await page.screenshot(path="submit_test_after_force.png")
            
            # Method 3: Try JavaScript click
            print("\n6. Trying JavaScript click...")
            try:
                result = await page.evaluate("""
                    () => {
                        const btn = document.querySelector('button[aria-label="Submit message"]');
                        if (btn) {
                            btn.click();
                            return "Clicked via JS";
                        }
                        // Try finding any visible button near the input
                        const buttons = document.querySelectorAll('button');
                        for (const b of buttons) {
                            if (b.offsetParent && b.getAttribute('aria-label')?.includes('Submit')) {
                                b.click();
                                return "Clicked alternative button";
                            }
                        }
                        return "No button found";
                    }
                """)
                print(f"   JS click result: {result}")
            except Exception as e:
                print(f"   JS click failed: {e}")
            
            await asyncio.sleep(2)
            await page.screenshot(path="submit_test_after_js.png")
            
            # Method 4: Dispatch input/change events then submit
            print("\n7. Trying to dispatch events and submit form...")
            try:
                result = await page.evaluate("""
                    () => {
                        const input = document.querySelector('#userInput');
                        if (input) {
                            input.dispatchEvent(new Event('input', { bubbles: true }));
                            input.dispatchEvent(new Event('change', { bubbles: true }));
                            
                            // Find parent form and submit
                            const form = input.closest('form');
                            if (form) {
                                form.submit();
                                return "Form submitted";
                            }
                            
                            // Try pressing enter via dispatch
                            input.dispatchEvent(new KeyboardEvent('keydown', { key: 'Enter', keyCode: 13, bubbles: true }));
                            input.dispatchEvent(new KeyboardEvent('keyup', { key: 'Enter', keyCode: 13, bubbles: true }));
                            return "Dispatched Enter key events";
                        }
                        return "Input not found";
                    }
                """)
                print(f"   Result: {result}")
            except Exception as e:
                print(f"   Failed: {e}")
            
            await asyncio.sleep(3)
            await page.screenshot(path="submit_test_after_events.png")
            
            # Check if message was sent
            print("\n8. Checking page state...")
            body_text = await page.evaluate("() => document.body.innerText")
            if "Copilot said" in body_text:
                print("   ✓ MESSAGE WAS SENT! Response detected.")
                parts = body_text.split("Copilot said")
                if len(parts) > 1:
                    print(f"   Response: {parts[-1][:200]}...")
            elif "Thinking" in body_text:
                print("   ⏳ Message sent, Copilot is thinking...")
            else:
                print("   ❌ Message not sent. Still on initial page.")
                print(f"   Page text: {body_text[:300]}...")
            
        print("\nBrowser stays open for 60s...")
        await asyncio.sleep(60)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_submission_methods())
