#!/usr/bin/env python3
"""
No-Guardrail AI Browser Agent
Autonomous browser automation met AI - kan alles online doen!
"""

import asyncio
from playwright.async_api import async_playwright, Page, BrowserContext
import requests
import json
from typing import Dict, List, Any
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ollama config
OLLAMA_URL = 'http://localhost:11434'
MODEL = 'dolphin-uncensored'

class BrowserAgent:
    """
    Autonomous browser agent powered by no-guardrail AI.
    Kan ALLES online doen: scrapen, forms invullen, bots draaien, etc.
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.browser = None
        self.context = None
        self.page = None
        
    async def start(self):
        """Start browser instance"""
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(
            headless=self.headless,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox'
            ]
        )
        
        # Stealth context - looks like normal user
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        )
        
        # Anti-detection
        await self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
        """)
        
        self.page = await self.context.new_page()
        logger.info("Browser agent started")
        
    async def ask_ai(self, prompt: str, context: str = None) -> str:
        """Ask AI what to do next"""
        full_prompt = prompt
        if context:
            full_prompt = f"Context:\n{context}\n\nTask: {prompt}"
        
        try:
            response = requests.post(
                f'{OLLAMA_URL}/api/generate',
                json={
                    'model': MODEL,
                    'prompt': full_prompt,
                    'stream': False,
                    'options': {'temperature': 0.7}
                },
                timeout=120
            )
            response.raise_for_status()
            return response.json().get('response', '')
        except Exception as e:
            logger.error(f"AI request failed: {e}")
            return ""
    
    async def get_page_context(self) -> str:
        """Get current page info for AI"""
        url = self.page.url
        title = await self.page.title()
        content = await self.page.content()
        
        # Simplified context for AI
        return f"URL: {url}\nTitle: {title}\nContent length: {len(content)} chars"
    
    async def goto(self, url: str) -> None:
        """Navigate to URL"""
        logger.info(f"Navigating to {url}")
        await self.page.goto(url, wait_until='networkidle')
    
    async def click(self, selector: str) -> None:
        """Click element"""
        logger.info(f"Clicking {selector}")
        await self.page.click(selector)
    
    async def fill(self, selector: str, value: str) -> None:
        """Fill form field"""
        logger.info(f"Filling {selector} with: {value}")
        await self.page.fill(selector, value)
    
    async def scrape_text(self, selector: str = 'body') -> str:
        """Scrape text from page"""
        return await self.page.inner_text(selector)
    
    async def screenshot(self, path: str) -> None:
        """Take screenshot"""
        await self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")
    
    async def execute_task(self, task: str) -> Dict[str, Any]:
        """
        Let AI execute arbitrary task autonomously.
        Examples:
        - "Scrape all product prices from bol.com"
        - "Find cheapest flights to Barcelona"
        - "Monitor crypto prices and alert me"
        - "Fill out contact form on website X"
        """
        logger.info(f"Executing task: {task}")
        
        # Get AI's plan
        context = await self.get_page_context()
        plan_prompt = f"""
You are a browser automation AI. Plan how to execute this task:

{task}

Current browser state:
{context}

Respond with a JSON plan:
{{
  "steps": [
    {{"action": "goto", "url": "..."}},
    {{"action": "click", "selector": "..."}},
    {{"action": "fill", "selector": "...", "value": "..."}},
    {{"action": "scrape", "selector": "..."}}
  ]
}}
"""
        
        plan_response = await self.ask_ai(plan_prompt)
        
        try:
            # Parse AI's plan
            plan = json.loads(plan_response)
            results = []
            
            # Execute each step
            for step in plan.get('steps', []):
                action = step.get('action')
                
                if action == 'goto':
                    await self.goto(step['url'])
                elif action == 'click':
                    await self.click(step['selector'])
                elif action == 'fill':
                    await self.fill(step['selector'], step['value'])
                elif action == 'scrape':
                    text = await self.scrape_text(step.get('selector', 'body'))
                    results.append(text)
                elif action == 'wait':
                    await asyncio.sleep(step.get('seconds', 1))
                elif action == 'screenshot':
                    await self.screenshot(step.get('path', 'screenshot.png'))
            
            return {
                'success': True,
                'plan': plan,
                'results': results
            }
            
        except json.JSONDecodeError:
            logger.error("AI didn't return valid JSON")
            return {'success': False, 'error': 'Invalid plan from AI'}
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {'success': False, 'error': str(e)}
    
    async def autonomous_loop(self, goal: str, max_iterations: int = 10):
        """
        Fully autonomous mode: AI decides what to do until goal is reached.
        """
        logger.info(f"Starting autonomous mode with goal: {goal}")
        
        for i in range(max_iterations):
            context = await self.get_page_context()
            
            decision_prompt = f"""
Goal: {goal}

Current browser state:
{context}

Iteration {i+1}/{max_iterations}

What should you do next to reach the goal?
Respond with ONE action in JSON format:
{{
  "action": "goto|click|fill|scrape|done",
  "reasoning": "why you're doing this",
  "params": {{...}}
}}
"""
            
            decision = await self.ask_ai(decision_prompt)
            
            try:
                action_data = json.loads(decision)
                action = action_data.get('action')
                params = action_data.get('params', {})
                
                logger.info(f"AI decision: {action_data.get('reasoning')}")
                
                if action == 'done':
                    logger.info("Goal reached!")
                    break
                elif action == 'goto':
                    await self.goto(params.get('url'))
                elif action == 'click':
                    await self.click(params.get('selector'))
                elif action == 'fill':
                    await self.fill(params.get('selector'), params.get('value'))
                elif action == 'scrape':
                    result = await self.scrape_text(params.get('selector', 'body'))
                    logger.info(f"Scraped: {result[:200]}...")
                
                await asyncio.sleep(1)  # Be nice
                
            except Exception as e:
                logger.error(f"Autonomous iteration failed: {e}")
                continue
    
    async def close(self):
        """Cleanup"""
        if self.browser:
            await self.browser.close()
            logger.info("Browser closed")


# ====================
# USAGE EXAMPLES
# ====================

async def example_scraper():
    """Example: Scrape product data"""
    agent = BrowserAgent(headless=False)
    await agent.start()
    
    await agent.goto('https://bol.com')
    await agent.fill('input[type="search"]', 'laptop')
    await agent.click('button[type="submit"]')
    
    await asyncio.sleep(2)
    
    products = await agent.scrape_text('.product-item')
    print("Products found:", products)
    
    await agent.close()

async def example_autonomous():
    """Example: Fully autonomous task"""
    agent = BrowserAgent(headless=False)
    await agent.start()
    
    await agent.autonomous_loop(
        goal="Find the cheapest MacBook Pro on bol.com and save the price",
        max_iterations=15
    )
    
    await agent.close()

async def example_arbitrage_bot():
    """Example: Price comparison bot"""
    agent = BrowserAgent(headless=False)
    await agent.start()
    
    task = """
    Compare prices for 'iPhone 15 Pro' on:
    1. bol.com
    2. coolblue.nl
    3. mediamarkt.nl
    
    Return the cheapest option.
    """
    
    result = await agent.execute_task(task)
    print("Arbitrage result:", result)
    
    await agent.close()


if __name__ == '__main__':
    # Run example
    asyncio.run(example_autonomous())
