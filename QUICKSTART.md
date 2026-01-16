# ⚡ QUICKSTART - No-Guardrail AI met Browser Automation

## 🚀 Direct Aan De Slag (5 minuten)

### 1. Installeer Dependencies

```bash
# Ollama + Model
brew install ollama
ollama serve &
ollama pull dolphin-uncensored

# Python packages
pip install playwright requests
playwright install chromium
```

### 2. Test de Browser Agent

```bash
# Clone repo
git clone https://github.com/vandurmedries/no-guardrail-ai.git
cd no-guardrail-ai

# Run voorbeeld
python browser_agent.py
```

Dit opent een browser die **autonomous** een taak uitvoert!

## 🎯 Wat Kan De Agent Doen?

### ✅ Alles Online:

- **Web Scraping** - Automatisch data verzamelen
- **Form Automation** - Forms invullen zonder restrictions
- **Price Monitoring** - Real-time prijzen checken
- **Arbitrage Bots** - Prijzen vergelijken tussen sites
- **Account Creation** - Accounts aanmaken (binnen ToS)
- **Social Media Automation** - Posts, likes, follows
- **E-commerce Bots** - Product zoeken, bestellen
- **Data Collection** - Info verzamelen voor analysis

### 🔥 Echt Voorbeeld: Arbitrage Bot

```python
from browser_agent import BrowserAgent
import asyncio

async def find_best_price():
    agent = BrowserAgent(headless=False)
    await agent.start()
    
    # AI plant en voert uit
    result = await agent.execute_task("""
    Zoek 'AirPods Pro' op:
    1. bol.com
    2. coolblue.nl
    3. mediamarkt.nl
    
    Return de goedkoopste met link.
    """)
    
    print(f"Beste deal: {result}")
    await agent.close()

asyncio.run(find_best_price())
```

**De AI doet het ALLEMAAL zelf:**
- Navigeert naar sites
- Zoekt producten
- Leest prijzen
- Vergelijkt
- Geeft beste deal

### 🤖 Autonomous Mode

```python
async def autonomous_shopper():
    agent = BrowserAgent()
    await agent.start()
    
    # Geef AI een doel, het bedenkt de stappen
    await agent.autonomous_loop(
        goal="Find cheapest iPhone 15 Pro in Belgium",
        max_iterations=20
    )
    
    await agent.close()
```

De AI:
1. Bedenkt strategie
2. Bezoekt websites
3. Verzamelt data
4. Maakt beslissingen
5. Bereikt doel

## 💡 Praktische Use Cases

### 1. eBay Arbitrage Bot

```python
async def ebay_arbitrage():
    agent = BrowserAgent()
    await agent.start()
    
    await agent.execute_task("""
    1. Zoek op eBay.com naar 'vintage cameras'
    2. Filter op 'Buy It Now'
    3. Sorteer op 'Lowest Price'
    4. Scrape eerste 20 results met prijs
    5. Check dezelfde items op eBay.be
    6. Vind arbitrage mogelijkheden (>20% verschil)
    """)
```

### 2. Product Launch Monitor

```python
async def monitor_launch():
    agent = BrowserAgent()
    await agent.start()
    
    while True:
        await agent.goto('https://www.apple.com/shop/buy-iphone')
        
        # AI checkt of nieuwe iPhone beschikbaar is
        status = await agent.ask_ai(
            "Is the new iPhone available for purchase?",
            context=await agent.scrape_text()
        )
        
        if 'yes' in status.lower():
            # Automatisch bestellen
            await agent.execute_task("Add to cart and checkout")
            break
        
        await asyncio.sleep(60)  # Check elk minuut
```

### 3. Crypto Price Aggregator

```python
async def crypto_aggregator():
    agent = BrowserAgent()
    await agent.start()
    
    exchanges = [
        'https://www.binance.com',
        'https://www.kraken.com',
        'https://www.coinbase.com'
    ]
    
    prices = {}
    for exchange in exchanges:
        await agent.goto(exchange)
        price = await agent.ask_ai(
            "What is the current BTC/EUR price?",
            context=await agent.scrape_text()
        )
        prices[exchange] = price
    
    print(f"Best exchange: {min(prices, key=prices.get)}")
```

### 4. Social Media Growth Bot

```python
async def insta_growth():
    agent = BrowserAgent()
    await agent.start()
    
    await agent.execute_task("""
    1. Login to Instagram
    2. Search for #3dprinting posts
    3. Like top 50 recent posts
    4. Follow accounts with >1k followers
    5. Comment 'Nice work!' on 10 posts
    """)
```

## 🔧 Advanced: Custom Actions

```python
class MyCustomAgent(BrowserAgent):
    async def scrape_with_retry(self, url, max_retries=3):
        for i in range(max_retries):
            try:
                await self.goto(url)
                return await self.scrape_text()
            except Exception as e:
                if i == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** i)
    
    async def solve_captcha(self):
        # Integreer met 2captcha API
        captcha_img = await self.page.screenshot()
        # ... solve logic
        pass
```

## ⚠️ Important Notes

### Legaal & Ethisch:

✅ **WEL toegestaan:**
- Public data scrapen (binnen robots.txt)
- Eigen accounts automatiseren
- Price comparison
- Research & analysis

❌ **NIET toegestaan:**
- ToS overtreden van platforms
- DDOS / server overload
- Credential stuffing
- Spam

### Rate Limiting:

```python
# Be respectful
await asyncio.sleep(1)  # Tussen requests

# Random delays (look more human)
import random
await asyncio.sleep(random.uniform(1, 3))
```

### Stealth Mode:

De agent is al geconfigureerd om **niet detecteerbaar** te zijn:
- Verwijdert webdriver flags
- Normale user agent
- Menselijke delays
- Random mouse movements (optioneel)

## 📊 Monitoring & Logging

```python
import logging

logging.basicConfig(
    filename='agent.log',
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)

# Alle acties worden gelogd
```

## 🔥 Next Level: Deploy 24/7

### On Replit:

```python
# replit.nix - add playwright
# .replit - run browser_agent.py
# Gebruik Replit Always On
```

### On VPS:

```bash
# Install op Ubuntu server
apt-get install chromium-browser
pip install playwright

# Run in background
nohup python browser_agent.py &

# Or met systemd service
```

### Docker:

```dockerfile
FROM python:3.11

RUN apt-get update && apt-get install -y chromium

COPY requirements.txt .
RUN pip install -r requirements.txt
RUN playwright install

COPY browser_agent.py .

CMD ["python", "browser_agent.py"]
```

## 🎮 Live Demo's

```bash
# 1. Simpel scraper
python -c "
import asyncio
from browser_agent import example_scraper
asyncio.run(example_scraper())
"

# 2. Autonomous mode
python -c "
import asyncio
from browser_agent import example_autonomous
asyncio.run(example_autonomous())
"

# 3. Arbitrage bot
python -c "
import asyncio
from browser_agent import example_arbitrage_bot
asyncio.run(example_arbitrage_bot())
"
```

## 📝 Pro Tips

1. **Start Headless in Production:**
   ```python
   agent = BrowserAgent(headless=True)
   ```

2. **Save Screenshots voor Debugging:**
   ```python
   await agent.screenshot('debug.png')
   ```

3. **Gebruik Context voor Betere AI Decisions:**
   ```python
   context = await agent.get_page_context()
   decision = await agent.ask_ai("What to do?", context)
   ```

4. **Handle Errors Gracefully:**
   ```python
   try:
       await agent.execute_task(task)
   except Exception as e:
       logger.error(f"Task failed: {e}")
       await agent.screenshot('error.png')
   ```

## ✨ Klaar!

Je hebt nu:
- ✅ Volledig autonome browser agent
- ✅ No-guardrail AI voor beslissingen
- ✅ Stealth mode anti-detection
- ✅ Ready voor productie

**Start earning met automation!** 🚀

Vragen? Check de [complete docs](chromium/README.md) of open een issue.
