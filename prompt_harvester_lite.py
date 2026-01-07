"""
Copilot Evaluation Framework - Lightweight Version
===================================================
Fetches user prompts from publicly available datasets and enriches them
with intent classification, difficulty scoring, and Microsoft product detection.
"""

import pandas as pd
import datetime
import re
import hashlib
import json
from collections import Counter, defaultdict
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
OUTPUT_DIR = r"C:\Users\perahmat\OneDrive - Microsoft\Evaluation Framework\output"
BATCH_SIZE_PER_SOURCE = 300

# --- INTENT CATEGORIES ---
INTENT_TAXONOMY = {
    "Coding & Development": {
        "keywords": ['code', 'python', 'java', 'javascript', 'function', 'bug', 'error', 'debug', 
                     'script', 'api', 'sql', 'database', 'html', 'css', 'react', 'algorithm',
                     'programming', 'developer', 'compile', 'syntax', 'github', 'git', 'deploy'],
    },
    "Creative Writing": {
        "keywords": ['write', 'essay', 'poem', 'draft', 'story', 'novel', 'creative', 'fiction',
                     'character', 'plot', 'dialogue', 'narrative', 'blog post', 'article'],
    },
    "Business Communication": {
        "keywords": ['email', 'letter', 'proposal', 'report', 'memo', 'professional', 'formal',
                     'meeting', 'presentation', 'pitch', 'resume', 'cv', 'cover letter', 'linkedin'],
    },
    "Education & Learning": {
        "keywords": ['explain', 'what is', 'how does', 'teach', 'learn', 'understand', 'study',
                     'homework', 'assignment', 'course', 'tutorial', 'lesson', 'concept'],
    },
    "Data Analysis & Research": {
        "keywords": ['analyze', 'data', 'statistics', 'research', 'study', 'survey', 'metrics',
                     'chart', 'graph', 'visualization', 'insight', 'trend', 'pattern'],
    },
    "Translation & Language": {
        "keywords": ['translate', 'translation', 'spanish', 'french', 'german', 'chinese',
                     'japanese', 'language', 'grammar', 'proofread', 'edit', 'rephrase'],
    },
    "Planning & Productivity": {
        "keywords": ['plan', 'schedule', 'itinerary', 'organize', 'manage', 'task', 'project',
                     'timeline', 'deadline', 'priority', 'workflow', 'efficiency'],
    },
    "Image & Visual Content": {
        "keywords": ['image', 'draw', 'picture', 'photo', 'design', 'logo', 'graphic', 'visual',
                     'illustration', 'art', 'generate image', 'create image', 'dalle', 'midjourney'],
    },
    "Web Search & Information": {
        "keywords": ['search', 'find', 'look up', 'browse', 'internet', 'website',
                     'news', 'current', 'latest', 'today', 'recent', 'what happened'],
    },
    "Conversational & Chat": {
        "keywords": ['chat', 'talk', 'hello', 'hi', 'hey', 'how are you', 'thanks',
                     'conversation', 'discuss', 'opinion', 'think about'],
    },
    "Math & Calculations": {
        "keywords": ['calculate', 'math', 'equation', 'solve', 'formula', 'compute', 'arithmetic',
                     'algebra', 'calculus', 'geometry', 'percentage', 'convert'],
    },
    "Advice & Recommendations": {
        "keywords": ['advice', 'recommend', 'suggest', 'should i', 'best', 'compare', 'versus',
                     'pros and cons', 'help me decide', 'which one', 'review'],
    },
    "Summarization": {
        "keywords": ['summarize', 'summary', 'tldr', 'brief', 'condense', 'key points', 'main ideas',
                     'overview', 'recap', 'shorten'],
    },
    "Automation & Agents": {
        "keywords": ['automate', 'automation', 'workflow', 'agent', 'bot', 'macro',
                     'schedule task', 'trigger', 'integration', 'zapier', 'power automate'],
    },
    "E-commerce & Business": {
        "keywords": ['store', 'shop', 'sell', 'ecommerce', 'product', 'inventory', 'order',
                     'customer', 'marketing', 'sales', 'business plan', 'startup'],
    },
    "Website & App Creation": {
        "keywords": ['website', 'web page', 'landing page', 'app', 'application', 'mobile app',
                     'build site', 'create website', 'wordpress', 'shopify', 'wix'],
    }
}

# --- MICROSOFT PRODUCT DETECTION ---
MICROSOFT_PRODUCTS = {
    "Word": ['word', 'microsoft word', 'docx', 'word document'],
    "Excel": ['excel', 'spreadsheet', 'xlsx', 'pivot table', 'vlookup', 'xlookup', 'excel formula', 'vba'],
    "PowerPoint": ['powerpoint', 'pptx', 'slides', 'presentation', 'slide deck'],
    "Outlook": ['outlook', 'outlook email', 'outlook calendar'],
    "Teams": ['teams', 'microsoft teams', 'teams meeting'],
    "Copilot": ['copilot', 'microsoft copilot', 'bizchat', 'bing chat', 'm365 copilot'],
    "Azure": ['azure', 'azure cloud', 'azure devops', 'azure functions'],
    "Windows": ['windows', 'windows 11', 'windows 10', 'win11'],
    "OneDrive/SharePoint": ['onedrive', 'sharepoint', 'one drive'],
    "Power Platform": ['power automate', 'power apps', 'power bi', 'power platform'],
    "VS Code": ['visual studio', 'vs code', 'vscode'],
    "GitHub Copilot": ['github copilot', 'copilot code'],
    "Bing": ['bing', 'bing search', 'bing ai'],
    "Edge": ['edge', 'microsoft edge'],
    "Designer": ['microsoft designer', 'bing image creator']
}

# --- CAPABILITY FLAGS ---
CAPABILITY_FLAGS = {
    "Image_Creation": ['generate image', 'create image', 'draw', 'picture of', 'dalle', 'midjourney', 'design logo'],
    "Web_Search": ['search for', 'look up', 'find online', 'current news', 'latest', 'recent news'],
    "Agent_Building": ['build agent', 'create agent', 'ai agent', 'autonomous', 'multi-step'],
    "Automation": ['automate', 'automation', 'workflow', 'trigger', 'power automate', 'zapier'],
    "Website_Creation": ['create website', 'build website', 'landing page', 'wordpress', 'shopify'],
    "Store_Creation": ['online store', 'ecommerce', 'sell online', 'shopify store'],
    "Code_Execution": ['run code', 'execute', 'python interpreter', 'code interpreter'],
    "File_Analysis": ['analyze file', 'read pdf', 'parse document', 'analyze spreadsheet'],
    "Real_Time_Data": ['current price', 'stock price', 'weather', 'live', 'real-time']
}


def categorize_intent(prompt: str) -> Tuple[str, float]:
    """Categorizes prompt intent using keyword matching."""
    prompt_lower = prompt.lower()
    intent_scores = {}
    
    for intent, config in INTENT_TAXONOMY.items():
        matches = sum(1 for kw in config["keywords"] if kw in prompt_lower)
        if matches > 0:
            weighted_score = sum(len(kw) for kw in config["keywords"] if kw in prompt_lower)
            intent_scores[intent] = (matches, weighted_score)
    
    if not intent_scores:
        return "General/Uncategorized", 0.3
    
    top_intent = max(intent_scores.items(), key=lambda x: (x[1][0], x[1][1]))
    confidence = min(1.0, top_intent[1][0] / 5)
    
    return top_intent[0], round(confidence, 2)


def calculate_difficulty(prompt: str) -> Tuple[str, int, str]:
    """Calculate prompt difficulty score (1-5)."""
    prompt_lower = prompt.lower()
    prompt_len = len(prompt)
    reasons = []
    score = 2
    
    # Length scoring
    if prompt_len < 30:
        score -= 1
        reasons.append("Short")
    elif prompt_len > 500:
        score += 2
        reasons.append("Long detailed")
    elif prompt_len > 200:
        score += 1
        reasons.append("Substantial length")
    
    # Multi-step detection
    multi_step = ['first', 'then', 'next', 'after', 'finally', 'step', 'additionally']
    if sum(1 for kw in multi_step if kw in prompt_lower) >= 2:
        score += 1
        reasons.append("Multi-step")
    
    # Constraints
    constraints = ['must', 'should', 'without', 'only', 'exactly', 'at least', 'maximum']
    if sum(1 for kw in constraints if kw in prompt_lower) >= 2:
        score += 1
        reasons.append("Has constraints")
    
    # Technical terms
    tech = ['api', 'algorithm', 'architecture', 'optimization', 'performance', 'database']
    if sum(1 for kw in tech if kw in prompt_lower) >= 2:
        score += 1
        reasons.append("Technical")
    
    # Multiple questions
    if prompt.count('?') >= 3:
        score += 1
        reasons.append("Multiple questions")
    
    score = max(1, min(5, score))
    
    levels = {1: "Simple", 2: "Medium", 3: "Complex", 4: "Advanced", 5: "Expert"}
    return levels[score], score, "; ".join(reasons) if reasons else "Default"


def detect_microsoft_products(prompt: str) -> Tuple[bool, str]:
    """Detect Microsoft product mentions."""
    prompt_lower = prompt.lower()
    detected = []
    
    for product, keywords in MICROSOFT_PRODUCTS.items():
        if any(kw in prompt_lower for kw in keywords):
            detected.append(product)
    
    return len(detected) > 0, "|".join(detected)


def detect_capabilities(prompt: str) -> Dict[str, bool]:
    """Detect required capabilities."""
    prompt_lower = prompt.lower()
    return {cap: any(kw in prompt_lower for kw in keywords) 
            for cap, keywords in CAPABILITY_FLAGS.items()}


def detect_language(prompt: str) -> str:
    """Simple language detection."""
    if re.search(r'[\u4e00-\u9fff]', prompt): return "zh"
    if re.search(r'[\u3040-\u30ff]', prompt): return "ja"
    if re.search(r'[\uac00-\ud7af]', prompt): return "ko"
    if re.search(r'[\u0600-\u06ff]', prompt): return "ar"
    if re.search(r'[\u0400-\u04ff]', prompt): return "ru"
    return "en"


def generate_hash(prompt: str) -> str:
    """Generate unique hash for deduplication."""
    return hashlib.md5(' '.join(prompt.lower().split()).encode()).hexdigest()[:12]


def process_record(prompt: str, source: str) -> Optional[Dict]:
    """Process a single prompt and enrich it."""
    prompt = prompt.strip()
    
    if not prompt or len(prompt) < 15 or len(prompt) > 5000:
        return None
    
    intent, confidence = categorize_intent(prompt)
    difficulty, diff_score, diff_reasons = calculate_difficulty(prompt)
    is_ms, ms_products = detect_microsoft_products(prompt)
    caps = detect_capabilities(prompt)
    
    return {
        "prompt_id": generate_hash(prompt),
        "date_harvested": datetime.datetime.now().strftime("%Y-%m-%d"),
        "source": source,
        "prompt_text": prompt,
        "prompt_length": len(prompt),
        "language": detect_language(prompt),
        "primary_intent": intent,
        "intent_confidence": confidence,
        "difficulty_level": difficulty,
        "difficulty_score": diff_score,
        "difficulty_reasons": diff_reasons,
        "is_microsoft_related": is_ms,
        "microsoft_products": ms_products,
        "requires_image_creation": caps.get("Image_Creation", False),
        "requires_web_search": caps.get("Web_Search", False),
        "requires_agent_building": caps.get("Agent_Building", False),
        "requires_automation": caps.get("Automation", False),
        "requires_website_creation": caps.get("Website_Creation", False),
        "requires_store_creation": caps.get("Store_Creation", False),
        "requires_code_execution": caps.get("Code_Execution", False),
        "requires_file_analysis": caps.get("File_Analysis", False),
        "requires_real_time_data": caps.get("Real_Time_Data", False),
        # Evaluation columns (to be filled later)
        "copilot_rating": None,
        "chatgpt_rating": None,
        "gemini_rating": None,
        "claude_rating": None,
        "winner": None,
        "evaluation_notes": None
    }


def fetch_dolly():
    """Fetch prompts from Databricks Dolly dataset."""
    print("\n📥 Fetching Dolly-15k dataset...")
    from datasets import load_dataset
    
    records = []
    seen = set()
    
    try:
        dataset = load_dataset("databricks/databricks-dolly-15k", split="train")
        
        for i, record in enumerate(dataset):
            if len(records) >= BATCH_SIZE_PER_SOURCE:
                break
            
            prompt = record.get('instruction', '')
            context = record.get('context', '')
            if context and len(context) > 10:
                prompt = f"{prompt}\n\nContext: {context}"
            
            prompt_hash = generate_hash(prompt)
            if prompt_hash in seen:
                continue
            seen.add(prompt_hash)
            
            enriched = process_record(prompt, "Dolly")
            if enriched:
                records.append(enriched)
        
        print(f"   ✅ Collected {len(records)} prompts from Dolly")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return records


def fetch_alpaca():
    """Fetch prompts from Stanford Alpaca dataset."""
    print("\n📥 Fetching Alpaca dataset...")
    from datasets import load_dataset
    
    records = []
    seen = set()
    
    try:
        dataset = load_dataset("tatsu-lab/alpaca", split="train")
        
        for i, record in enumerate(dataset):
            if len(records) >= BATCH_SIZE_PER_SOURCE:
                break
            
            prompt = record.get('instruction', '')
            input_text = record.get('input', '')
            if input_text and len(input_text) > 10:
                prompt = f"{prompt}\n\nInput: {input_text}"
            
            prompt_hash = generate_hash(prompt)
            if prompt_hash in seen:
                continue
            seen.add(prompt_hash)
            
            enriched = process_record(prompt, "Alpaca")
            if enriched:
                records.append(enriched)
        
        print(f"   ✅ Collected {len(records)} prompts from Alpaca")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return records


def fetch_openassistant():
    """Fetch prompts from OpenAssistant dataset."""
    print("\n📥 Fetching OpenAssistant dataset...")
    from datasets import load_dataset
    
    records = []
    seen = set()
    
    try:
        dataset = load_dataset("OpenAssistant/oasst1", split="train")
        
        for i, record in enumerate(dataset):
            if len(records) >= BATCH_SIZE_PER_SOURCE:
                break
            
            # Only get user prompts (prompter role)
            if record.get('role') != 'prompter':
                continue
            
            prompt = record.get('text', '')
            
            prompt_hash = generate_hash(prompt)
            if prompt_hash in seen:
                continue
            seen.add(prompt_hash)
            
            enriched = process_record(prompt, "OpenAssistant")
            if enriched:
                records.append(enriched)
        
        print(f"   ✅ Collected {len(records)} prompts from OpenAssistant")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return records


def fetch_gsm8k():
    """Fetch math prompts from GSM8K dataset."""
    print("\n📥 Fetching GSM8K (math) dataset...")
    from datasets import load_dataset
    
    records = []
    seen = set()
    
    try:
        dataset = load_dataset("gsm8k", "main", split="train")
        
        for i, record in enumerate(dataset):
            if len(records) >= BATCH_SIZE_PER_SOURCE:
                break
            
            prompt = record.get('question', '')
            
            prompt_hash = generate_hash(prompt)
            if prompt_hash in seen:
                continue
            seen.add(prompt_hash)
            
            enriched = process_record(prompt, "GSM8K")
            if enriched:
                records.append(enriched)
        
        print(f"   ✅ Collected {len(records)} prompts from GSM8K")
    except Exception as e:
        print(f"   ❌ Error: {e}")
    
    return records


def generate_statistics(df: pd.DataFrame) -> Dict:
    """Generate summary statistics."""
    return {
        "total_prompts": len(df),
        "by_source": df['source'].value_counts().to_dict(),
        "by_intent": df['primary_intent'].value_counts().to_dict(),
        "by_difficulty": df['difficulty_level'].value_counts().to_dict(),
        "by_language": df['language'].value_counts().head(10).to_dict(),
        "microsoft_related": {
            "count": int(df['is_microsoft_related'].sum()),
            "percentage": round(df['is_microsoft_related'].mean() * 100, 2)
        },
        "capability_requirements": {
            "image_creation": int(df['requires_image_creation'].sum()),
            "web_search": int(df['requires_web_search'].sum()),
            "agent_building": int(df['requires_agent_building'].sum()),
            "automation": int(df['requires_automation'].sum()),
            "website_creation": int(df['requires_website_creation'].sum()),
            "store_creation": int(df['requires_store_creation'].sum()),
            "code_execution": int(df['requires_code_execution'].sum()),
            "file_analysis": int(df['requires_file_analysis'].sum()),
            "real_time_data": int(df['requires_real_time_data'].sum())
        },
        "avg_prompt_length": int(df['prompt_length'].mean()),
        "avg_difficulty_score": round(df['difficulty_score'].mean(), 2)
    }


def create_evaluation_schema() -> Dict:
    """Create the evaluation framework schema."""
    return {
        "evaluation_criteria": {
            "accuracy": {"weight": 0.25, "scale": "1-5", "description": "Factual correctness"},
            "helpfulness": {"weight": 0.25, "scale": "1-5", "description": "Addresses user need"},
            "completeness": {"weight": 0.20, "scale": "1-5", "description": "Coverage of all aspects"},
            "clarity": {"weight": 0.15, "scale": "1-5", "description": "Readability and organization"},
            "safety": {"weight": 0.10, "scale": "1-5", "description": "No harmful content"},
            "efficiency": {"weight": 0.05, "scale": "1-5", "description": "Appropriate length"}
        },
        "competitors": {
            "Microsoft_Copilot": {"focus": ["M365 Integration", "Enterprise", "Productivity"]},
            "ChatGPT": {"focus": ["General purpose", "Plugins", "Custom GPTs"]},
            "Gemini": {"focus": ["Google integration", "Search", "Multi-modal"]},
            "Claude": {"focus": ["Safety", "Long context", "Reasoning"]}
        },
        "methodology": {
            "blind_evaluation": True,
            "min_sample_per_category": 30,
            "evaluators_per_prompt": 3
        }
    }


def run_harvester():
    """Main harvesting function."""
    print("=" * 70)
    print("🚀 COPILOT EVALUATION FRAMEWORK - PROMPT HARVESTER")
    print("=" * 70)
    print(f"📅 Run Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target: ~{BATCH_SIZE_PER_SOURCE * 4} prompts across 4 sources")
    print("=" * 70)
    
    all_records = []
    
    # Fetch from each source
    all_records.extend(fetch_dolly())
    all_records.extend(fetch_alpaca())
    all_records.extend(fetch_openassistant())
    all_records.extend(fetch_gsm8k())
    
    if not all_records:
        print("\n❌ No records harvested!")
        return
    
    # Create DataFrame
    df = pd.DataFrame(all_records)
    
    # Global deduplication
    initial = len(df)
    df = df.drop_duplicates(subset=['prompt_id'])
    print(f"\n🔄 Deduplication: {initial} → {len(df)} prompts")
    
    # Generate outputs
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Main dataset
    main_path = f"{OUTPUT_DIR}\\evaluation_prompts_{timestamp}.csv"
    df.to_csv(main_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 Main dataset: {main_path}")
    
    # Statistics
    stats = generate_statistics(df)
    stats_path = f"{OUTPUT_DIR}\\harvest_statistics_{timestamp}.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    print(f"📊 Statistics: {stats_path}")
    
    # Evaluation schema
    schema = create_evaluation_schema()
    schema_path = f"{OUTPUT_DIR}\\evaluation_schema_{timestamp}.json"
    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)
    print(f"📋 Schema: {schema_path}")
    
    # Subsets by difficulty
    for diff in df['difficulty_level'].unique():
        subset = df[df['difficulty_level'] == diff]
        path = f"{OUTPUT_DIR}\\prompts_{diff.lower()}_{timestamp}.csv"
        subset.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"   📁 {diff}: {len(subset)} prompts")
    
    # Microsoft subset
    ms_df = df[df['is_microsoft_related'] == True]
    if len(ms_df) > 0:
        path = f"{OUTPUT_DIR}\\prompts_microsoft_{timestamp}.csv"
        ms_df.to_csv(path, index=False, encoding='utf-8-sig')
        print(f"   📁 Microsoft: {len(ms_df)} prompts")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    print(f"Total: {stats['total_prompts']}")
    print(f"\nBy Source:")
    for src, cnt in stats['by_source'].items():
        print(f"   • {src}: {cnt}")
    print(f"\nBy Intent (Top 5):")
    for intent, cnt in list(stats['by_intent'].items())[:5]:
        print(f"   • {intent}: {cnt}")
    print(f"\nBy Difficulty:")
    for diff, cnt in stats['by_difficulty'].items():
        print(f"   • {diff}: {cnt}")
    print(f"\nMicrosoft Related: {stats['microsoft_related']['count']} ({stats['microsoft_related']['percentage']}%)")
    print(f"Avg Difficulty: {stats['avg_difficulty_score']}/5")
    print("=" * 70)
    print("✅ COMPLETE!")


if __name__ == "__main__":
    run_harvester()
