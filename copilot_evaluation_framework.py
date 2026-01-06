"""
Copilot Evaluation Framework
============================
A comprehensive framework for harvesting user prompts from multiple sources,
categorizing them by intent, difficulty, and Microsoft product relevance,
and providing an evaluation schema for comparing AI assistants.

Author: Evaluation Framework Team
Date: 2026-01-06
"""

import pandas as pd
import datetime
import re
import hashlib
import json
from collections import Counter
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# --- CONFIGURATION ---
OUTPUT_DIR = r"C:\Users\perahmat\OneDrive - Microsoft\Evaluation Framework\output"
BATCH_SIZE_PER_SOURCE = 250  # Prompts per source
TOTAL_TARGET = 1000  # Total target prompts

# --- DATA SOURCE CONFIGURATIONS ---
DATA_SOURCES = {
    "LMSYS_Arena": {
        "dataset": "lmsys/chatbot_arena_conversations",
        "description": "Gold standard - 33k+ battle-tested conversations",
        "prompt_field": "conversation_a",
        "is_conversation": True
    },
    "WildChat": {
        "dataset": "allenai/WildChat",
        "description": "1M+ real ChatGPT interactions, 68 languages",
        "prompt_field": "conversation",
        "is_conversation": True
    },
    "ShareGPT": {
        "dataset": "anon8231489123/ShareGPT_Vicuna_unfiltered",
        "description": "User-shared ChatGPT conversations",
        "prompt_field": "conversations",
        "is_conversation": True
    },
    "OpenAssistant": {
        "dataset": "OpenAssistant/oasst1",
        "description": "Crowdsourced, human-annotated instruction data",
        "prompt_field": "text",
        "is_conversation": False
    }
}

# --- INTENT CATEGORIES (Hierarchical) ---
INTENT_TAXONOMY = {
    "Coding & Development": {
        "keywords": ['code', 'python', 'java', 'javascript', 'function', 'bug', 'error', 'debug', 
                     'script', 'api', 'sql', 'database', 'html', 'css', 'react', 'algorithm',
                     'programming', 'developer', 'compile', 'syntax', 'github', 'git', 'deploy'],
        "subcategories": ["Bug Fixing", "Code Generation", "Code Review", "Architecture"]
    },
    "Creative Writing": {
        "keywords": ['write', 'essay', 'poem', 'draft', 'story', 'novel', 'creative', 'fiction',
                     'character', 'plot', 'dialogue', 'narrative', 'blog post', 'article'],
        "subcategories": ["Fiction", "Poetry", "Blog/Article", "Scriptwriting"]
    },
    "Business Communication": {
        "keywords": ['email', 'letter', 'proposal', 'report', 'memo', 'professional', 'formal',
                     'meeting', 'presentation', 'pitch', 'resume', 'cv', 'cover letter', 'linkedin'],
        "subcategories": ["Email", "Reports", "Presentations", "HR Documents"]
    },
    "Education & Learning": {
        "keywords": ['explain', 'what is', 'how does', 'teach', 'learn', 'understand', 'study',
                     'homework', 'assignment', 'course', 'tutorial', 'lesson', 'concept'],
        "subcategories": ["Explanation", "Tutoring", "Homework Help", "Research"]
    },
    "Data Analysis & Research": {
        "keywords": ['analyze', 'data', 'statistics', 'research', 'study', 'survey', 'metrics',
                     'chart', 'graph', 'visualization', 'insight', 'trend', 'pattern', 'excel'],
        "subcategories": ["Statistical Analysis", "Data Visualization", "Research Synthesis"]
    },
    "Translation & Language": {
        "keywords": ['translate', 'translation', 'spanish', 'french', 'german', 'chinese',
                     'japanese', 'language', 'grammar', 'proofread', 'edit', 'rephrase'],
        "subcategories": ["Translation", "Grammar Check", "Localization"]
    },
    "Planning & Productivity": {
        "keywords": ['plan', 'schedule', 'itinerary', 'organize', 'manage', 'task', 'project',
                     'timeline', 'deadline', 'priority', 'workflow', 'automate', 'efficiency'],
        "subcategories": ["Project Planning", "Travel Planning", "Task Management"]
    },
    "Image & Visual Content": {
        "keywords": ['image', 'draw', 'picture', 'photo', 'design', 'logo', 'graphic', 'visual',
                     'illustration', 'art', 'generate image', 'create image', 'dalle', 'midjourney'],
        "subcategories": ["Image Generation", "Image Editing", "Design"]
    },
    "Web Search & Information": {
        "keywords": ['search', 'find', 'look up', 'google', 'browse', 'internet', 'website',
                     'news', 'current', 'latest', 'today', 'recent', 'what happened'],
        "subcategories": ["Factual Lookup", "News/Current Events", "Research"]
    },
    "Conversational & Chat": {
        "keywords": ['chat', 'talk', 'hello', 'hi', 'hey', 'how are you', 'thanks', 'thank you',
                     'conversation', 'discuss', 'opinion', 'think about'],
        "subcategories": ["Small Talk", "Opinion Seeking", "Companionship"]
    },
    "Math & Calculations": {
        "keywords": ['calculate', 'math', 'equation', 'solve', 'formula', 'compute', 'arithmetic',
                     'algebra', 'calculus', 'geometry', 'percentage', 'convert'],
        "subcategories": ["Basic Math", "Advanced Math", "Unit Conversion"]
    },
    "Advice & Recommendations": {
        "keywords": ['advice', 'recommend', 'suggest', 'should i', 'best', 'compare', 'versus',
                     'pros and cons', 'help me decide', 'which one', 'review'],
        "subcategories": ["Product Recommendations", "Life Advice", "Decision Support"]
    },
    "Summarization": {
        "keywords": ['summarize', 'summary', 'tldr', 'brief', 'condense', 'key points', 'main ideas',
                     'overview', 'recap', 'shorten'],
        "subcategories": ["Document Summary", "Meeting Summary", "Article Summary"]
    },
    "Automation & Agents": {
        "keywords": ['automate', 'automation', 'workflow', 'agent', 'bot', 'script', 'macro',
                     'schedule task', 'trigger', 'integration', 'zapier', 'power automate'],
        "subcategories": ["Workflow Automation", "Bot Building", "Integration"]
    },
    "E-commerce & Business": {
        "keywords": ['store', 'shop', 'sell', 'ecommerce', 'product', 'inventory', 'order',
                     'customer', 'marketing', 'sales', 'business plan', 'startup'],
        "subcategories": ["Store Setup", "Marketing", "Business Strategy"]
    },
    "Website & App Creation": {
        "keywords": ['website', 'web page', 'landing page', 'app', 'application', 'mobile app',
                     'build site', 'create website', 'wordpress', 'shopify', 'wix'],
        "subcategories": ["Website Creation", "App Development", "Landing Pages"]
    }
}

# --- MICROSOFT PRODUCT DETECTION ---
MICROSOFT_PRODUCTS = {
    "Office Suite": {
        "keywords": ['word', 'microsoft word', 'docx', 'word document'],
        "product_code": "MS_WORD"
    },
    "Excel": {
        "keywords": ['excel', 'spreadsheet', 'xlsx', 'pivot table', 'vlookup', 'xlookup', 
                     'excel formula', 'excel function', 'excel macro', 'vba excel'],
        "product_code": "MS_EXCEL"
    },
    "PowerPoint": {
        "keywords": ['powerpoint', 'pptx', 'slides', 'presentation', 'slide deck'],
        "product_code": "MS_POWERPOINT"
    },
    "Outlook": {
        "keywords": ['outlook', 'outlook email', 'outlook calendar', 'microsoft email'],
        "product_code": "MS_OUTLOOK"
    },
    "Teams": {
        "keywords": ['teams', 'microsoft teams', 'teams meeting', 'teams chat'],
        "product_code": "MS_TEAMS"
    },
    "Copilot/BizChat": {
        "keywords": ['copilot', 'microsoft copilot', 'bizchat', 'bing chat', 'm365 copilot',
                     'copilot in word', 'copilot in excel', 'copilot in powerpoint'],
        "product_code": "MS_COPILOT"
    },
    "Azure": {
        "keywords": ['azure', 'azure cloud', 'azure devops', 'azure functions', 'azure ml'],
        "product_code": "MS_AZURE"
    },
    "Windows": {
        "keywords": ['windows', 'windows 11', 'windows 10', 'win11', 'win10', 'windows os'],
        "product_code": "MS_WINDOWS"
    },
    "OneDrive/SharePoint": {
        "keywords": ['onedrive', 'sharepoint', 'sharepoint online', 'one drive'],
        "product_code": "MS_ONEDRIVE_SHAREPOINT"
    },
    "Power Platform": {
        "keywords": ['power automate', 'power apps', 'power bi', 'power platform', 'flow'],
        "product_code": "MS_POWER_PLATFORM"
    },
    "Visual Studio": {
        "keywords": ['visual studio', 'vs code', 'vscode', 'visual studio code'],
        "product_code": "MS_VSCODE"
    },
    "GitHub Copilot": {
        "keywords": ['github copilot', 'copilot code', 'copilot suggestion'],
        "product_code": "MS_GITHUB_COPILOT"
    },
    "Bing": {
        "keywords": ['bing', 'bing search', 'bing ai', 'bing image'],
        "product_code": "MS_BING"
    },
    "Edge": {
        "keywords": ['edge', 'microsoft edge', 'edge browser'],
        "product_code": "MS_EDGE"
    },
    "Designer": {
        "keywords": ['microsoft designer', 'designer ai', 'bing image creator'],
        "product_code": "MS_DESIGNER"
    }
}

# --- SPECIAL CAPABILITY FLAGS ---
CAPABILITY_FLAGS = {
    "Image_Creation": ['generate image', 'create image', 'draw', 'picture of', 'image of',
                       'dalle', 'midjourney', 'stable diffusion', 'ai art', 'design logo'],
    "Web_Search": ['search for', 'look up', 'find online', 'google', 'browse', 'current news',
                   'what happened today', 'latest', 'recent news', 'breaking'],
    "Agent_Building": ['build agent', 'create agent', 'ai agent', 'autonomous', 'multi-step',
                       'workflow agent', 'task agent', 'copilot agent'],
    "Automation": ['automate', 'automation', 'workflow', 'trigger', 'scheduled task',
                   'power automate', 'zapier', 'make.com', 'ifttt'],
    "Website_Creation": ['create website', 'build website', 'landing page', 'web page',
                         'wordpress', 'shopify', 'wix', 'squarespace'],
    "Store_Creation": ['online store', 'ecommerce', 'sell online', 'shopify store',
                       'create store', 'product listing'],
    "Code_Execution": ['run code', 'execute', 'python interpreter', 'code interpreter',
                       'run this', 'test this code'],
    "File_Analysis": ['analyze file', 'read pdf', 'parse document', 'extract from',
                      'analyze spreadsheet', 'read csv'],
    "Real_Time_Data": ['current price', 'stock price', 'weather', 'live', 'real-time',
                       'today\'s', 'right now']
}

# --- DIFFICULTY CLASSIFICATION ---
DIFFICULTY_INDICATORS = {
    "Simple": {
        "patterns": [
            r'^(what is|who is|when|where|define)\b',  # Simple factual questions
            r'^(hi|hello|hey|thanks|thank you)\b',      # Greetings
            r'^translate\s+\w+\s+to\s+\w+',             # Simple translation
            r'^(yes|no|ok|okay|sure)\b',                # Simple responses
        ],
        "max_length": 50,
        "score": 1
    },
    "Medium": {
        "patterns": [
            r'(explain|describe|how to|help me)\b',     # Explanation requests
            r'(write a|create a|make a)\b',             # Single creation tasks
            r'(compare|difference between)\b',         # Comparison
        ],
        "length_range": (50, 200),
        "score": 2
    },
    "Complex": {
        "patterns": [
            r'(step by step|detailed|comprehensive)\b', # Detailed requests
            r'(analyze|evaluate|assess)\b',            # Analysis tasks
            r'(multiple|several|various)\b',           # Multi-element tasks
            r'(and then|after that|next)\b',           # Sequential tasks
        ],
        "length_range": (200, 500),
        "score": 3
    },
    "Expert": {
        "patterns": [
            r'(optimize|refactor|architect)\b',        # Expert-level tasks
            r'(integration|system design)\b',          # System-level thinking
            r'(considering|taking into account)\b',    # Multi-factor reasoning
            r'(trade-?offs?|constraints?)\b',          # Complex decision making
        ],
        "min_length": 300,
        "multi_step_indicators": ['first', 'then', 'finally', 'step 1', 'step 2'],
        "score": 4
    }
}


def calculate_difficulty_score(prompt: str) -> Tuple[str, int, List[str]]:
    """
    Calculate prompt difficulty based on multiple factors.
    Returns: (difficulty_level, score, reasons)
    """
    prompt_lower = prompt.lower()
    prompt_len = len(prompt)
    reasons = []
    score = 2  # Default medium
    
    # Length-based scoring
    if prompt_len < 30:
        score -= 1
        reasons.append("Very short prompt")
    elif prompt_len > 500:
        score += 2
        reasons.append("Long detailed prompt")
    elif prompt_len > 200:
        score += 1
        reasons.append("Substantial prompt length")
    
    # Multi-step detection
    multi_step_keywords = ['first', 'then', 'next', 'after', 'finally', 'step', 
                           'and also', 'additionally', 'moreover', 'furthermore']
    multi_step_count = sum(1 for kw in multi_step_keywords if kw in prompt_lower)
    if multi_step_count >= 2:
        score += 1
        reasons.append(f"Multi-step task ({multi_step_count} indicators)")
    
    # Constraint detection
    constraint_keywords = ['must', 'should', 'without', 'only', 'exactly', 'no more than',
                          'at least', 'maximum', 'minimum', 'constraint', 'requirement']
    constraint_count = sum(1 for kw in constraint_keywords if kw in prompt_lower)
    if constraint_count >= 2:
        score += 1
        reasons.append(f"Has constraints ({constraint_count} found)")
    
    # Technical complexity
    technical_keywords = ['api', 'algorithm', 'architecture', 'optimization', 'performance',
                         'scalability', 'security', 'authentication', 'encryption', 'database']
    tech_count = sum(1 for kw in technical_keywords if kw in prompt_lower)
    if tech_count >= 2:
        score += 1
        reasons.append(f"Technical complexity ({tech_count} terms)")
    
    # Context requirements
    context_keywords = ['given that', 'assuming', 'in the context of', 'based on',
                       'considering', 'taking into account', 'with respect to']
    context_count = sum(1 for kw in context_keywords if kw in prompt_lower)
    if context_count >= 1:
        score += 1
        reasons.append("Requires context understanding")
    
    # Question complexity (multiple questions)
    question_marks = prompt.count('?')
    if question_marks >= 3:
        score += 1
        reasons.append(f"Multiple questions ({question_marks})")
    
    # Code-related complexity
    if '```' in prompt or 'function' in prompt_lower or 'class' in prompt_lower:
        if prompt_len > 200:
            score += 1
            reasons.append("Complex code context")
    
    # Normalize score
    score = max(1, min(5, score))
    
    # Map to difficulty level
    if score == 1:
        level = "Simple"
    elif score == 2:
        level = "Medium"
    elif score == 3:
        level = "Complex"
    elif score == 4:
        level = "Advanced"
    else:
        level = "Expert"
    
    return level, score, reasons


def categorize_intent(prompt: str) -> Tuple[str, str, float]:
    """
    Categorizes prompt intent using keyword matching with confidence scoring.
    Returns: (primary_intent, subcategory, confidence_score)
    """
    prompt_lower = prompt.lower()
    intent_scores = {}
    
    for intent, config in INTENT_TAXONOMY.items():
        matches = sum(1 for kw in config["keywords"] if kw in prompt_lower)
        if matches > 0:
            # Weight by keyword specificity (longer keywords = more specific)
            weighted_score = sum(len(kw) for kw in config["keywords"] if kw in prompt_lower)
            intent_scores[intent] = (matches, weighted_score)
    
    if not intent_scores:
        return "General/Uncategorized", "General", 0.3
    
    # Get top intent by weighted score
    top_intent = max(intent_scores.items(), key=lambda x: (x[1][0], x[1][1]))
    intent_name = top_intent[0]
    match_count = top_intent[1][0]
    
    # Calculate confidence (0-1 scale)
    confidence = min(1.0, match_count / 5)  # Max out at 5 matches
    
    # Determine subcategory (simplified - would use LLM in production)
    subcategories = INTENT_TAXONOMY[intent_name].get("subcategories", ["General"])
    subcategory = subcategories[0]  # Default to first; LLM would choose better
    
    return intent_name, subcategory, round(confidence, 2)


def detect_microsoft_products(prompt: str) -> Tuple[bool, List[str], List[str]]:
    """
    Detect Microsoft product mentions in the prompt.
    Returns: (is_ms_related, product_names, product_codes)
    """
    prompt_lower = prompt.lower()
    detected_products = []
    product_codes = []
    
    for product_name, config in MICROSOFT_PRODUCTS.items():
        for keyword in config["keywords"]:
            if keyword in prompt_lower:
                if product_name not in detected_products:
                    detected_products.append(product_name)
                    product_codes.append(config["product_code"])
                break
    
    return len(detected_products) > 0, detected_products, product_codes


def detect_capability_flags(prompt: str) -> Dict[str, bool]:
    """
    Detect special capability requirements in the prompt.
    Returns dict of capability flags.
    """
    prompt_lower = prompt.lower()
    flags = {}
    
    for capability, keywords in CAPABILITY_FLAGS.items():
        flags[capability] = any(kw in prompt_lower for kw in keywords)
    
    return flags


def generate_prompt_hash(prompt: str) -> str:
    """Generate a unique hash for deduplication."""
    normalized = ' '.join(prompt.lower().split())
    return hashlib.md5(normalized.encode()).hexdigest()[:12]


def detect_language(prompt: str) -> str:
    """Simple language detection based on character patterns."""
    # Check for non-ASCII characters
    if re.search(r'[\u4e00-\u9fff]', prompt):
        return "zh"  # Chinese
    elif re.search(r'[\u3040-\u309f\u30a0-\u30ff]', prompt):
        return "ja"  # Japanese
    elif re.search(r'[\uac00-\ud7af]', prompt):
        return "ko"  # Korean
    elif re.search(r'[\u0600-\u06ff]', prompt):
        return "ar"  # Arabic
    elif re.search(r'[\u0400-\u04ff]', prompt):
        return "ru"  # Russian
    elif re.search(r'[àâäéèêëïîôùûüÿœæç]', prompt.lower()):
        return "fr"  # French
    elif re.search(r'[äöüß]', prompt.lower()):
        return "de"  # German
    elif re.search(r'[áéíóúñ¿¡]', prompt.lower()):
        return "es"  # Spanish
    else:
        return "en"  # Default English


def estimate_response_complexity(prompt: str, difficulty_score: int) -> Dict:
    """
    Estimate expected response characteristics for evaluation planning.
    """
    prompt_lower = prompt.lower()
    
    return {
        "expected_length": "long" if difficulty_score >= 4 else "medium" if difficulty_score >= 2 else "short",
        "requires_creativity": any(kw in prompt_lower for kw in ['creative', 'novel', 'unique', 'original', 'story', 'poem']),
        "requires_accuracy": any(kw in prompt_lower for kw in ['exact', 'precise', 'accurate', 'factual', 'correct']),
        "requires_code": any(kw in prompt_lower for kw in ['code', 'script', 'function', 'program', 'implement']),
        "requires_reasoning": any(kw in prompt_lower for kw in ['why', 'explain', 'reason', 'because', 'analyze']),
        "requires_current_info": any(kw in prompt_lower for kw in ['current', 'latest', 'today', 'recent', 'now', '2024', '2025', '2026']),
        "is_subjective": any(kw in prompt_lower for kw in ['opinion', 'think', 'feel', 'believe', 'prefer', 'best'])
    }


def extract_user_prompt(record: dict, source_config: dict) -> Optional[str]:
    """Extract the user prompt from various dataset formats."""
    field = source_config["prompt_field"]
    
    try:
        if source_config["is_conversation"]:
            conversation = record.get(field, [])
            if not conversation:
                # Try alternative field names
                for alt_field in ['conversation', 'conversations', 'messages', 'dialogue']:
                    conversation = record.get(alt_field, [])
                    if conversation:
                        break
            
            if not conversation:
                return None
            
            # Handle different conversation formats
            if isinstance(conversation, list) and len(conversation) > 0:
                first_msg = conversation[0]
                if isinstance(first_msg, dict):
                    # Format: [{"role": "user", "content": "..."}]
                    return first_msg.get('content') or first_msg.get('value') or first_msg.get('text')
                elif isinstance(first_msg, str):
                    return first_msg
        else:
            # Direct text field (like OpenAssistant)
            text = record.get(field, '')
            # For OpenAssistant, filter to only prompter messages
            if record.get('role') == 'prompter' or source_config.get('filter_role') is None:
                return text
    except Exception as e:
        return None
    
    return None


def process_dataset(source_name: str, source_config: dict, batch_size: int) -> List[Dict]:
    """Process a single dataset source and return enriched prompt records."""
    from datasets import load_dataset
    
    print(f"\n📥 Processing {source_name}...")
    print(f"   Dataset: {source_config['dataset']}")
    
    records = []
    seen_hashes = set()
    
    try:
        # Load dataset with streaming to manage memory
        dataset = load_dataset(
            source_config['dataset'], 
            split="train", 
            streaming=True,
            trust_remote_code=True
        )
        
        count = 0
        skipped = 0
        
        for record in dataset:
            if count >= batch_size:
                break
            
            # Extract prompt
            prompt = extract_user_prompt(record, source_config)
            
            if not prompt or len(prompt.strip()) < 15:
                skipped += 1
                continue
            
            prompt = prompt.strip()
            
            # Deduplicate
            prompt_hash = generate_prompt_hash(prompt)
            if prompt_hash in seen_hashes:
                skipped += 1
                continue
            seen_hashes.add(prompt_hash)
            
            # Skip prompts that are too long (likely contain code dumps)
            if len(prompt) > 5000:
                skipped += 1
                continue
            
            # Enrich the prompt
            intent, subcategory, intent_confidence = categorize_intent(prompt)
            difficulty, diff_score, diff_reasons = calculate_difficulty_score(prompt)
            is_ms_related, ms_products, ms_codes = detect_microsoft_products(prompt)
            capability_flags = detect_capability_flags(prompt)
            language = record.get('language') or detect_language(prompt)
            response_complexity = estimate_response_complexity(prompt, diff_score)
            
            # Build record
            enriched_record = {
                # Core Fields
                "prompt_id": prompt_hash,
                "date_harvested": datetime.datetime.now().strftime("%Y-%m-%d"),
                "source": source_name,
                "prompt_text": prompt,
                "prompt_length": len(prompt),
                "language": language,
                
                # Intent Classification
                "primary_intent": intent,
                "subcategory": subcategory,
                "intent_confidence": intent_confidence,
                
                # Difficulty Classification
                "difficulty_level": difficulty,
                "difficulty_score": diff_score,
                "difficulty_reasons": "; ".join(diff_reasons) if diff_reasons else "Default",
                
                # Microsoft Product Flags
                "is_microsoft_related": is_ms_related,
                "microsoft_products": "|".join(ms_products) if ms_products else "",
                "microsoft_product_codes": "|".join(ms_codes) if ms_codes else "",
                
                # Capability Flags
                "requires_image_creation": capability_flags.get("Image_Creation", False),
                "requires_web_search": capability_flags.get("Web_Search", False),
                "requires_agent_building": capability_flags.get("Agent_Building", False),
                "requires_automation": capability_flags.get("Automation", False),
                "requires_website_creation": capability_flags.get("Website_Creation", False),
                "requires_store_creation": capability_flags.get("Store_Creation", False),
                "requires_code_execution": capability_flags.get("Code_Execution", False),
                "requires_file_analysis": capability_flags.get("File_Analysis", False),
                "requires_real_time_data": capability_flags.get("Real_Time_Data", False),
                
                # Response Expectations (for evaluation)
                "expected_response_length": response_complexity["expected_length"],
                "requires_creativity": response_complexity["requires_creativity"],
                "requires_accuracy": response_complexity["requires_accuracy"],
                "requires_code_output": response_complexity["requires_code"],
                "requires_reasoning": response_complexity["requires_reasoning"],
                "requires_current_info": response_complexity["requires_current_info"],
                "is_subjective": response_complexity["is_subjective"],
                
                # Evaluation Fields (to be filled during comparison)
                "copilot_rating": None,
                "chatgpt_rating": None,
                "gemini_rating": None,
                "claude_rating": None,
                "winner": None,
                "evaluation_notes": None
            }
            
            records.append(enriched_record)
            count += 1
            
            if count % 50 == 0:
                print(f"   ✅ Processed {count} prompts...")
        
        print(f"   ✅ Completed: {count} prompts extracted, {skipped} skipped")
        
    except Exception as e:
        print(f"   ❌ Error processing {source_name}: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return records


def create_evaluation_schema():
    """Generate the evaluation schema documentation."""
    schema = {
        "evaluation_criteria": {
            "accuracy": {
                "weight": 0.25,
                "description": "Factual correctness and precision of the response",
                "scale": "1-5 (1=Incorrect, 5=Perfectly accurate)"
            },
            "helpfulness": {
                "weight": 0.25,
                "description": "How well the response addresses the user's actual need",
                "scale": "1-5 (1=Unhelpful, 5=Extremely helpful)"
            },
            "completeness": {
                "weight": 0.20,
                "description": "Coverage of all aspects of the query",
                "scale": "1-5 (1=Incomplete, 5=Comprehensive)"
            },
            "clarity": {
                "weight": 0.15,
                "description": "Readability and organization of the response",
                "scale": "1-5 (1=Confusing, 5=Crystal clear)"
            },
            "safety": {
                "weight": 0.10,
                "description": "Avoidance of harmful, biased, or inappropriate content",
                "scale": "1-5 (1=Harmful, 5=Safe and appropriate)"
            },
            "efficiency": {
                "weight": 0.05,
                "description": "Conciseness without losing important information",
                "scale": "1-5 (1=Too verbose/brief, 5=Just right)"
            }
        },
        "comparison_methodology": {
            "blind_evaluation": "Evaluators should not know which AI generated which response",
            "sample_size": "Minimum 30 prompts per category for statistical significance",
            "evaluator_count": "At least 3 evaluators per prompt for reliability",
            "inter_rater_reliability": "Calculate Fleiss' Kappa to ensure consistency"
        },
        "capability_specific_metrics": {
            "coding": ["Code correctness", "Best practices", "Explanation quality"],
            "creative_writing": ["Creativity", "Engagement", "Style adherence"],
            "image_creation": ["Prompt adherence", "Aesthetic quality", "Technical quality"],
            "web_search": ["Source quality", "Recency", "Relevance"],
            "analysis": ["Insight depth", "Methodology", "Actionability"]
        },
        "competitors": {
            "Microsoft_Copilot": {"vendor": "Microsoft", "versions": ["Consumer", "M365", "Enterprise"]},
            "ChatGPT": {"vendor": "OpenAI", "versions": ["GPT-4", "GPT-4o", "GPT-4-turbo"]},
            "Gemini": {"vendor": "Google", "versions": ["Pro", "Ultra", "Advanced"]},
            "Claude": {"vendor": "Anthropic", "versions": ["Claude 3 Opus", "Claude 3.5 Sonnet"]}
        }
    }
    return schema


def generate_summary_statistics(df: pd.DataFrame) -> Dict:
    """Generate summary statistics for the harvested data."""
    stats = {
        "total_prompts": len(df),
        "by_source": df['source'].value_counts().to_dict(),
        "by_intent": df['primary_intent'].value_counts().to_dict(),
        "by_difficulty": df['difficulty_level'].value_counts().to_dict(),
        "by_language": df['language'].value_counts().head(10).to_dict(),
        "microsoft_related": {
            "count": df['is_microsoft_related'].sum(),
            "percentage": round(df['is_microsoft_related'].mean() * 100, 2)
        },
        "capability_requirements": {
            "image_creation": df['requires_image_creation'].sum(),
            "web_search": df['requires_web_search'].sum(),
            "agent_building": df['requires_agent_building'].sum(),
            "automation": df['requires_automation'].sum(),
            "website_creation": df['requires_website_creation'].sum(),
            "store_creation": df['requires_store_creation'].sum(),
            "code_execution": df['requires_code_execution'].sum(),
            "file_analysis": df['requires_file_analysis'].sum(),
            "real_time_data": df['requires_real_time_data'].sum()
        },
        "avg_prompt_length": round(df['prompt_length'].mean(), 0),
        "avg_difficulty_score": round(df['difficulty_score'].mean(), 2)
    }
    return stats


def run_harvester():
    """Main function to run the prompt harvesting and enrichment pipeline."""
    print("=" * 70)
    print("🚀 COPILOT EVALUATION FRAMEWORK - PROMPT HARVESTER")
    print("=" * 70)
    print(f"📅 Run Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Target: {TOTAL_TARGET} prompts across {len(DATA_SOURCES)} sources")
    print("=" * 70)
    
    all_records = []
    batch_per_source = BATCH_SIZE_PER_SOURCE
    
    # Process each data source
    for source_name, source_config in DATA_SOURCES.items():
        records = process_dataset(source_name, source_config, batch_per_source)
        all_records.extend(records)
    
    if not all_records:
        print("\n❌ No records harvested. Check your internet connection and dataset availability.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(all_records)
    
    # Global deduplication
    initial_count = len(df)
    df = df.drop_duplicates(subset=['prompt_id'])
    print(f"\n🔄 Global deduplication: {initial_count} → {len(df)} prompts")
    
    # Generate statistics
    stats = generate_summary_statistics(df)
    
    # Generate evaluation schema
    eval_schema = create_evaluation_schema()
    
    # Save outputs
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Main dataset
    main_csv_path = f"{OUTPUT_DIR}\\evaluation_prompts_{timestamp}.csv"
    df.to_csv(main_csv_path, index=False, encoding='utf-8-sig')
    print(f"\n💾 Main dataset saved: {main_csv_path}")
    
    # Statistics summary
    stats_path = f"{OUTPUT_DIR}\\harvest_statistics_{timestamp}.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2, ensure_ascii=False)
    print(f"📊 Statistics saved: {stats_path}")
    
    # Evaluation schema
    schema_path = f"{OUTPUT_DIR}\\evaluation_schema_{timestamp}.json"
    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(eval_schema, f, indent=2, ensure_ascii=False)
    print(f"📋 Evaluation schema saved: {schema_path}")
    
    # Create subset CSVs by difficulty
    for difficulty in df['difficulty_level'].unique():
        subset = df[df['difficulty_level'] == difficulty]
        subset_path = f"{OUTPUT_DIR}\\prompts_{difficulty.lower()}_{timestamp}.csv"
        subset.to_csv(subset_path, index=False, encoding='utf-8-sig')
        print(f"   📁 {difficulty} prompts ({len(subset)}): {subset_path}")
    
    # Create Microsoft-related subset
    ms_subset = df[df['is_microsoft_related'] == True]
    if len(ms_subset) > 0:
        ms_path = f"{OUTPUT_DIR}\\prompts_microsoft_related_{timestamp}.csv"
        ms_subset.to_csv(ms_path, index=False, encoding='utf-8-sig')
        print(f"   📁 Microsoft-related prompts ({len(ms_subset)}): {ms_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("📊 HARVEST SUMMARY")
    print("=" * 70)
    print(f"Total Prompts: {stats['total_prompts']}")
    print(f"\nBy Source:")
    for source, count in stats['by_source'].items():
        print(f"   • {source}: {count}")
    print(f"\nBy Primary Intent (Top 5):")
    for intent, count in list(stats['by_intent'].items())[:5]:
        print(f"   • {intent}: {count}")
    print(f"\nBy Difficulty:")
    for diff, count in stats['by_difficulty'].items():
        print(f"   • {diff}: {count}")
    print(f"\nMicrosoft Related: {stats['microsoft_related']['count']} ({stats['microsoft_related']['percentage']}%)")
    print(f"\nCapability Requirements:")
    for cap, count in stats['capability_requirements'].items():
        if count > 0:
            print(f"   • {cap.replace('_', ' ').title()}: {count}")
    print(f"\nAverage Prompt Length: {stats['avg_prompt_length']} characters")
    print(f"Average Difficulty Score: {stats['avg_difficulty_score']}/5")
    print("=" * 70)
    print("✅ HARVESTING COMPLETE!")
    print("=" * 70)


if __name__ == "__main__":
    run_harvester()
