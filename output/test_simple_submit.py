"""
Simple test to verify Copilot submission works.
"""
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import Stealth
import time

async def test_simple_submit():
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
        
        print("2. Finding input...")
        input_el = await page.wait_for_selector('#userInput', timeout=10000)
        
        if input_el:
            print("3. Filling input with simple prompt...")
            # Use a simple prompt
            prompt = "What is the capital of France? Answer in one word."
            await input_el.fill(prompt)
            await asyncio.sleep(1)
            
            print("4. Pressing Enter...")
            await input_el.focus()
            await asyncio.sleep(0.3)
            await page.keyboard.press("Enter")
            
            print("5. Waiting for response...")
            start_time = time.time()
            last_response = ""
            stable_count = 0
            
            while time.time() - start_time < 60:
                await asyncio.sleep(2)
                
                try:
                    body_text = await page.evaluate("() => document.body.innerText")
                    
                    if "Copilot said" in body_text:
                        parts = body_text.split("Copilot said")
                        if len(parts) > 1:
                            response = parts[-1].strip()
                            
                            # Clean up
                            for marker in ["You said", "Smart", "Today", "Message Copilot"]:
                                if marker in response:
                                    response = response.split(marker)[0].strip()
                            
                            # Skip if loading
                            if "Thinking" in response or len(response) < 10:
                                print(f"   Still generating... ({int(time.time() - start_time)}s)")
                                continue
                            
                            if response == last_response:
                                stable_count += 1
                                if stable_count >= 2:
                                    print(f"\n✓ RESPONSE CAPTURED ({len(response)} chars):")
                                    print("="*60)
                                    print(response[:500])
                                    print("="*60)
                                    break
                            else:
                                last_response = response
                                stable_count = 0
                                print(f"   Response changing... ({len(response)} chars so far)")
                except Exception as e:
                    print(f"   Error: {e}")
                
                elapsed = int(time.time() - start_time)
                if elapsed % 10 == 0:
                    print(f"   Waiting... ({elapsed}s)")
            
            if not last_response:
                print("❌ Timeout - no response detected")
                # Dump page text to debug
                body = await page.evaluate("() => document.body.innerText")
                print("\nPage content:")
                print(body[:1000])
        
        print("\nBrowser stays open for 30s...")
        await asyncio.sleep(30)
        await browser.close()

if __name__ == "__main__":
    asyncio.run(test_simple_submit())
