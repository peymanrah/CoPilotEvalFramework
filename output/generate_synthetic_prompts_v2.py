"""
Synthetic Prompt Generator v2 - High Quality Generation
=========================================================

This version focuses on generating clear, natural, high-quality prompts
that avoid common issues like redundancy, vagueness, and grammatical errors.

Key Improvements:
- Better handling of missing/invalid values (?, empty)
- Natural language flow without redundancy
- Diverse prompts per intent (no duplicates)
- Added source_intent column for traceability
- Professional enterprise context
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set
import random
import hashlib


@dataclass
class IntentRow:
    """Parsed intent row from CSV"""
    action_rank: int
    rank_in_action: int
    reliable: bool
    inv_quality: bool
    inv_retention: bool
    unreliable: bool
    action: str
    object_: str
    subject: str
    output: str
    pct_users: str
    user_count: str
    pct_impressions: str
    impression_count: str
    sat_rate: str
    feedback_count: int
    apology_rate: str
    no_citation_rate: str
    active_weeks_p75: float
    active_weeks_p90: float
    active_weeks_p95: float
    active_weeks_p99: float
    pct_active_weeks_p75: str
    pct_active_weeks_p90: str
    pct_active_weeks_p95: str
    pct_active_weeks_p99: str
    active_days_p75: float
    active_days_p90: float
    active_days_p95: float
    active_days_p99: float
    focus_days_p75: str
    focus_days_p90: str
    focus_days_p95: str
    focus_days_p99: str
    tenant_count: int
    conversation_count: float
    day_count: str
    week_count: str
    thumbs_up_count: int
    thumbs_down_count: int


class HighQualitySyntheticPromptGenerator:
    """
    Generates high-quality, clear, natural synthetic prompts.
    
    Design Principles:
    1. Natural language - prompts should read like real user queries
    2. No redundancy - avoid "X from X" or "X related to X" patterns
    3. Clear intent - every prompt should have unambiguous meaning
    4. Diverse variants - 10 unique prompts per intent
    5. Professional context - enterprise/workplace scenarios
    """
    
    # Action verb mappings for natural language
    ACTION_VERB_FORMS = {
        'GET': {'base': 'get', 'gerund': 'getting', 'noun': 'retrieval of'},
        'CREATE': {'base': 'create', 'gerund': 'creating', 'noun': 'creation of'},
        'LIST': {'base': 'list', 'gerund': 'listing', 'noun': 'list of'},
        'FIND': {'base': 'find', 'gerund': 'finding', 'noun': 'search for'},
        'SUMMARIZE': {'base': 'summarize', 'gerund': 'summarizing', 'noun': 'summary of'},
        'EXPLAIN': {'base': 'explain', 'gerund': 'explaining', 'noun': 'explanation of'},
        'PROVIDE': {'base': 'provide', 'gerund': 'providing', 'noun': 'provision of'},
        'SUGGEST': {'base': 'suggest', 'gerund': 'suggesting', 'noun': 'suggestions for'},
        'ANALYZE': {'base': 'analyze', 'gerund': 'analyzing', 'noun': 'analysis of'},
        'COMPARE': {'base': 'compare', 'gerund': 'comparing', 'noun': 'comparison of'},
        'USE': {'base': 'use', 'gerund': 'using', 'noun': 'usage of'},
        'MODIFY': {'base': 'modify', 'gerund': 'modifying', 'noun': 'modification of'},
        'CONVERT': {'base': 'convert', 'gerund': 'converting', 'noun': 'conversion of'},
        'SHARE': {'base': 'share', 'gerund': 'sharing', 'noun': 'sharing of'},
        'SCHEDULE': {'base': 'schedule', 'gerund': 'scheduling', 'noun': 'scheduling of'},
        'DRAFT': {'base': 'draft', 'gerund': 'drafting', 'noun': 'draft of'},
        'REVIEW': {'base': 'review', 'gerund': 'reviewing', 'noun': 'review of'},
        'PREPARE': {'base': 'prepare', 'gerund': 'preparing', 'noun': 'preparation of'},
        'RECOMMEND': {'base': 'recommend', 'gerund': 'recommending', 'noun': 'recommendations for'},
        'IDENTIFY': {'base': 'identify', 'gerund': 'identifying', 'noun': 'identification of'},
    }
    
    # Object type contextualizers - make objects more specific
    OBJECT_CONTEXT = {
        'DOCUMENT': ['my document', 'this document', 'the document', 'a document'],
        'EMAIL': ['my email', 'this email', 'the email draft', 'my message'],
        'FILE': ['my file', 'this file', 'the file', 'the attached file'],
        'MEETING': ['my meeting', 'the upcoming meeting', 'this meeting', 'the team meeting'],
        'MEETINGS': ['my meetings', 'upcoming meetings', 'team meetings', 'scheduled meetings'],
        'DATA': ['the data', 'this data', 'my data', 'the dataset'],
        'PEOPLE': ['team members', 'colleagues', 'contacts', 'people'],
        'COMPANIES': ['companies', 'organizations', 'vendors', 'partners'],
        'TASKS': ['my tasks', 'pending tasks', 'assigned tasks', 'open tasks'],
        'UPDATES': ['recent updates', 'latest updates', 'new updates', 'status updates'],
        'BENEFITS': ['the benefits', 'key benefits', 'available benefits', 'employee benefits'],
        'IDEAS': ['ideas', 'new ideas', 'creative ideas', 'brainstorming ideas'],
        'TABLE': ['a table', 'the data in table format', 'a formatted table'],
        'ACTION ITEMS': ['action items', 'next steps', 'to-do items', 'follow-up actions'],
        'SUMMARY': ['a summary', 'the summary', 'a brief summary', 'an overview'],
        'REPORT': ['a report', 'the report', 'a detailed report', 'the analysis report'],
        'KEY TAKEAWAYS': ['key takeaways', 'main points', 'highlights', 'key insights'],
        'QUESTIONS': ['questions', 'discussion questions', 'key questions', 'clarifying questions'],
        'INSIGHTS': ['insights', 'key insights', 'actionable insights', 'data insights'],
        'FEEDBACK': ['feedback', 'my feedback', 'the feedback', 'review feedback'],
    }
    
    # Professional context phrases
    WORK_CONTEXTS = [
        "for my upcoming presentation",
        "for the team meeting",
        "for my manager",
        "for the quarterly review",
        "for the project status update",
        "to share with stakeholders",
        "for the client call",
        "for our team discussion",
        "before the deadline",
        "for the executive briefing",
    ]
    
    # Temporal contexts
    TIME_CONTEXTS = [
        "from this week",
        "from the past month",
        "from recent discussions",
        "from the last quarter",
        "since our last meeting",
        "from today",
        "from yesterday's session",
    ]
    
    def __init__(self):
        self.prompt_counter = 0
        self.generated_hashes: Set[str] = set()
    
    def _clean_value(self, value: str) -> str:
        """Clean input value - remove ?, empty handling"""
        if not value or value.strip() in ['?', '-', 'N/A', 'null', 'undefined']:
            return ''
        return value.strip()
    
    def _get_action_verb(self, action: str, form: str = 'base') -> str:
        """Get the appropriate verb form for an action"""
        action_upper = action.upper()
        if action_upper in self.ACTION_VERB_FORMS:
            return self.ACTION_VERB_FORMS[action_upper].get(form, action.lower())
        return action.lower()
    
    def _get_object_phrase(self, obj: str, variation: int = 0) -> str:
        """Get a natural phrase for the object"""
        obj_upper = obj.upper()
        if obj_upper in self.OBJECT_CONTEXT:
            options = self.OBJECT_CONTEXT[obj_upper]
            return options[variation % len(options)]
        return obj.lower()
    
    def _is_subject_redundant(self, obj: str, subject: str) -> bool:
        """Check if subject is redundant (same as object)"""
        if not subject:
            return True
        obj_clean = obj.strip().lower()
        subj_clean = subject.strip().lower()
        return obj_clean == subj_clean or obj_clean in subj_clean or subj_clean in obj_clean
    
    def _get_hash(self, text: str) -> str:
        """Get hash of prompt text to check for duplicates"""
        return hashlib.md5(text.lower().encode()).hexdigest()
    
    def _is_duplicate(self, text: str) -> bool:
        """Check if prompt is duplicate"""
        h = self._get_hash(text)
        if h in self.generated_hashes:
            return True
        self.generated_hashes.add(h)
        return False
    
    def generate_prompts_for_intent(self, intent: IntentRow, num_prompts: int = 10) -> List[Dict[str, Any]]:
        """Generate high-quality synthetic prompts for a single intent row"""
        
        # Clean and validate inputs
        action = self._clean_value(intent.action).upper()
        obj = self._clean_value(intent.object_)
        subject = self._clean_value(intent.subject)
        output = self._clean_value(intent.output)
        
        # Skip invalid rows
        if not action or not obj:
            return []
        
        # Check if subject is meaningful (not same as object)
        has_subject = subject and not self._is_subject_redundant(obj, subject)
        has_output = bool(output) and output.upper() != obj.upper()
        
        # Build source intent string for traceability
        source_intent = f"{action} + {obj}"
        if has_subject:
            source_intent += f" (Subject: {subject})"
        if has_output:
            source_intent += f" → {output}"
        
        # Generate prompts with different strategies
        prompts = []
        generators = [
            self._gen_direct_simple_1,
            self._gen_direct_simple_2,
            self._gen_contextual_1,
            self._gen_contextual_2,
            self._gen_conditional,
            self._gen_multi_step,
            self._gen_analytical,
            self._gen_comparative,
            self._gen_hypothetical,
            self._gen_creative,
        ]
        
        for i, generator in enumerate(generators):
            self.prompt_counter += 1
            
            # Generate prompt text
            prompt_text, variant_type, complexity = generator(
                action, obj, subject if has_subject else None, 
                output if has_output else None, i
            )
            
            # Skip if duplicate (regenerate with variation)
            attempt = 0
            while self._is_duplicate(prompt_text) and attempt < 3:
                prompt_text, variant_type, complexity = generator(
                    action, obj, subject if has_subject else None,
                    output if has_output else None, i + attempt + 10
                )
                attempt += 1
            
            # Get evaluation criteria
            criteria = self._get_evaluation_criteria(action, variant_type, obj, output)
            
            # Create prompt record with all metadata
            prompt_record = {
                'synthetic_prompt_id': f'SP_{self.prompt_counter:06d}',
                'source_intent': source_intent,
                'synthetic_prompt': prompt_text,
                'prompt_variant_type': variant_type,
                'complexity_level': complexity,
                'expected_response_criteria': json.dumps(criteria['criteria']),
                'evaluation_dimensions': json.dumps(criteria['dimensions']),
                # Original input components (for traceability)
                'input_action': intent.action,
                'input_object': intent.object_,
                'input_subject': intent.subject,
                'input_output': intent.output,
                # Preserve all original metadata
                'action_rank': intent.action_rank,
                'rank_in_action': intent.rank_in_action,
                'reliable': intent.reliable,
                'inv_quality': intent.inv_quality,
                'inv_retention': intent.inv_retention,
                'unreliable': intent.unreliable,
                'action': intent.action,
                'object': intent.object_,
                'subject': intent.subject,
                'output': intent.output,
                'pct_users': intent.pct_users,
                'user_count': intent.user_count,
                'pct_impressions': intent.pct_impressions,
                'impression_count': intent.impression_count,
                'sat_rate': intent.sat_rate,
                'feedback_count': intent.feedback_count,
                'apology_rate': intent.apology_rate,
                'no_citation_rate': intent.no_citation_rate,
                'active_weeks_p75': intent.active_weeks_p75,
                'active_weeks_p90': intent.active_weeks_p90,
                'active_weeks_p95': intent.active_weeks_p95,
                'active_weeks_p99': intent.active_weeks_p99,
                'pct_active_weeks_p75': intent.pct_active_weeks_p75,
                'pct_active_weeks_p90': intent.pct_active_weeks_p90,
                'pct_active_weeks_p95': intent.pct_active_weeks_p95,
                'pct_active_weeks_p99': intent.pct_active_weeks_p99,
                'active_days_p75': intent.active_days_p75,
                'active_days_p90': intent.active_days_p90,
                'active_days_p95': intent.active_days_p95,
                'active_days_p99': intent.active_days_p99,
                'focus_days_p75': intent.focus_days_p75,
                'focus_days_p90': intent.focus_days_p90,
                'focus_days_p95': intent.focus_days_p95,
                'focus_days_p99': intent.focus_days_p99,
                'tenant_count': intent.tenant_count,
                'conversation_count': intent.conversation_count,
                'day_count': intent.day_count,
                'week_count': intent.week_count,
                'thumbs_up_count': intent.thumbs_up_count,
                'thumbs_down_count': intent.thumbs_down_count
            }
            
            prompts.append(prompt_record)
        
        return prompts
    
    # ==========================================================================
    # PROMPT GENERATORS - Each returns (prompt_text, variant_type, complexity)
    # ==========================================================================
    
    def _gen_direct_simple_1(self, action: str, obj: str, subject: str, output: str, var: int):
        """Direct simple request - polite form"""
        verb = self._get_action_verb(action)
        obj_phrase = self._get_object_phrase(obj, var)
        
        templates = [
            f"Can you {verb} {obj_phrase}?",
            f"Please {verb} {obj_phrase}.",
            f"I need you to {verb} {obj_phrase}.",
            f"Could you help me {verb} {obj_phrase}?",
        ]
        
        prompt = templates[var % len(templates)]
        
        if subject:
            prompt = prompt.rstrip('.?') + f" related to {subject.lower()}."
        if output:
            prompt = prompt.rstrip('.?') + f" Format the result as {output.lower()}."
        
        return prompt, 'direct_request', 'simple'
    
    def _gen_direct_simple_2(self, action: str, obj: str, subject: str, output: str, var: int):
        """Direct simple request - imperative form"""
        verb = self._get_action_verb(action)
        obj_phrase = self._get_object_phrase(obj, var + 1)
        
        templates = [
            f"{action.capitalize()} {obj_phrase} for me.",
            f"Help me {verb} {obj_phrase}.",
            f"I'd like to {verb} {obj_phrase}.",
            f"Show me {obj_phrase}." if action.upper() in ['GET', 'FIND', 'LIST'] else f"{action.capitalize()} {obj_phrase}.",
        ]
        
        prompt = templates[var % len(templates)]
        
        if subject:
            prompt = prompt.rstrip('.') + f" about {subject.lower()}."
        if output:
            prompt = prompt.rstrip('.') + f" I need it as {output.lower()}."
        
        return prompt, 'direct_request', 'simple'
    
    def _gen_contextual_1(self, action: str, obj: str, subject: str, output: str, var: int):
        """Contextual request - with work situation"""
        verb = self._get_action_verb(action)
        obj_phrase = self._get_object_phrase(obj, var)
        context = self.WORK_CONTEXTS[var % len(self.WORK_CONTEXTS)]
        
        templates = [
            f"I'm preparing {context} and need to {verb} {obj_phrase}.",
            f"{context.capitalize()}, I need to {verb} {obj_phrase}. Can you help?",
            f"For {context.replace('for ', '')}, could you {verb} {obj_phrase}?",
        ]
        
        prompt = templates[var % len(templates)]
        
        if subject:
            prompt = prompt.rstrip('.?') + f" The focus should be on {subject.lower()}."
        if output:
            prompt = prompt.rstrip('.?') + f" Please format as {output.lower()}."
        
        return prompt, 'contextual', 'medium'
    
    def _gen_contextual_2(self, action: str, obj: str, subject: str, output: str, var: int):
        """Contextual request - with time context"""
        verb = self._get_action_verb(action)
        obj_phrase = self._get_object_phrase(obj, var + 2)
        time_ctx = self.TIME_CONTEXTS[var % len(self.TIME_CONTEXTS)]
        
        templates = [
            f"Can you {verb} {obj_phrase} {time_ctx}?",
            f"I need to {verb} {obj_phrase} {time_ctx} for a quick update.",
            f"Please {verb} {obj_phrase} {time_ctx} and highlight the important points.",
        ]
        
        prompt = templates[var % len(templates)]
        
        if subject:
            prompt = prompt.rstrip('.?') + f" Focus on {subject.lower()}."
        if output:
            prompt = prompt.rstrip('.?') + f" Output as {output.lower()}."
        
        return prompt, 'contextual', 'medium'
    
    def _gen_conditional(self, action: str, obj: str, subject: str, output: str, var: int):
        """Conditional request"""
        verb = self._get_action_verb(action)
        obj_phrase = self._get_object_phrase(obj, var)
        
        conditions = [
            "if there are any available",
            "only if they're relevant",
            "but only the most recent ones",
            "if they exist in the system",
            "only from the past week",
        ]
        condition = conditions[var % len(conditions)]
        
        templates = [
            f"Can you {verb} {obj_phrase}, {condition}?",
            f"Please {verb} {obj_phrase} {condition}.",
            f"I'd like to {verb} {obj_phrase}, {condition}.",
        ]
        
        prompt = templates[var % len(templates)]
        
        if subject:
            prompt = prompt.rstrip('.?') + f" Related to {subject.lower()}."
        if output:
            prompt = prompt.rstrip('.?') + f" Format: {output.lower()}."
        
        return prompt, 'conditional', 'medium'
    
    def _gen_multi_step(self, action: str, obj: str, subject: str, output: str, var: int):
        """Multi-step request"""
        verb = self._get_action_verb(action)
        obj_phrase = self._get_object_phrase(obj, var)
        
        second_steps = [
            "then summarize the key findings",
            "and organize them by priority",
            "then identify any patterns or trends",
            "and highlight the most important items",
            "then create an action plan based on them",
        ]
        second_step = second_steps[var % len(second_steps)]
        
        templates = [
            f"First, {verb} {obj_phrase}, {second_step}.",
            f"Please {verb} {obj_phrase} and {second_step.replace('then ', '')}.",
            f"Can you {verb} {obj_phrase}? After that, {second_step.replace('then ', '')}.",
        ]
        
        prompt = templates[var % len(templates)]
        
        if subject:
            prompt = prompt.replace(obj_phrase, f"{obj_phrase} about {subject.lower()}")
        if output:
            prompt = prompt.rstrip('.') + f" Present the final result as {output.lower()}."
        
        return prompt, 'multi_step', 'complex'
    
    def _gen_analytical(self, action: str, obj: str, subject: str, output: str, var: int):
        """Analytical request"""
        verb = self._get_action_verb(action)
        obj_phrase = self._get_object_phrase(obj, var)
        
        analysis_asks = [
            "and identify the key insights",
            "and analyze what stands out",
            "and tell me what patterns you notice",
            "and provide your assessment",
            "and explain the implications",
        ]
        analysis = analysis_asks[var % len(analysis_asks)]
        
        templates = [
            f"Can you {verb} {obj_phrase} {analysis}?",
            f"Please {verb} {obj_phrase} {analysis}.",
            f"I need you to {verb} {obj_phrase}. {analysis.capitalize().replace('and ', '')}.",
        ]
        
        prompt = templates[var % len(templates)]
        
        if subject:
            prompt = prompt.replace(obj_phrase, f"{obj_phrase} regarding {subject.lower()}")
        if output:
            prompt = prompt.rstrip('.?') + f" Provide the analysis as {output.lower()}."
        
        return prompt, 'analytical', 'complex'
    
    def _gen_comparative(self, action: str, obj: str, subject: str, output: str, var: int):
        """Comparative request"""
        verb = self._get_action_verb(action)
        obj_phrase = self._get_object_phrase(obj, var)
        
        comparisons = [
            "and compare with last week's results",
            "and show how they differ from previous versions",
            "and contrast with what we had before",
            "and highlight any changes from the baseline",
            "and compare across different time periods",
        ]
        comparison = comparisons[var % len(comparisons)]
        
        templates = [
            f"Can you {verb} {obj_phrase} {comparison}?",
            f"Please {verb} {obj_phrase} {comparison}.",
            f"I'd like to {verb} {obj_phrase}. Also, {comparison.replace('and ', '')}.",
        ]
        
        prompt = templates[var % len(templates)]
        
        if subject:
            prompt = prompt.replace(obj_phrase, f"{obj_phrase} for {subject.lower()}")
        if output:
            prompt = prompt.rstrip('.?') + f" Format as {output.lower()}."
        
        return prompt, 'comparative', 'complex'
    
    def _gen_hypothetical(self, action: str, obj: str, subject: str, output: str, var: int):
        """Hypothetical/scenario-based request"""
        verb = self._get_action_verb(action)
        obj_phrase = self._get_object_phrase(obj, var)
        
        scenarios = [
            "If I were presenting to executives,",
            "Imagine I'm explaining this to a new team member.",
            "Let's say I need to brief the CEO.",
            "Suppose I have to present this to stakeholders.",
            "If this were for a board meeting,",
        ]
        scenario = scenarios[var % len(scenarios)]
        
        templates = [
            f"{scenario} how should I {verb} {obj_phrase}?",
            f"{scenario} Please {verb} {obj_phrase} accordingly.",
            f"{scenario} Can you {verb} {obj_phrase} in a way that would be appropriate?",
        ]
        
        prompt = templates[var % len(templates)]
        
        if subject:
            prompt = prompt.replace(obj_phrase, f"{obj_phrase} about {subject.lower()}")
        if output:
            prompt = prompt.rstrip('.?') + f" The final format should be {output.lower()}."
        
        return prompt, 'hypothetical', 'expert'
    
    def _gen_creative(self, action: str, obj: str, subject: str, output: str, var: int):
        """Creative/open-ended request"""
        verb = self._get_action_verb(action)
        obj_phrase = self._get_object_phrase(obj, var)
        
        creative_asks = [
            "in the most impactful way possible",
            "with a fresh perspective",
            "in a way that would stand out",
            "that would really engage the audience",
            "with innovative ideas and suggestions",
        ]
        creative = creative_asks[var % len(creative_asks)]
        
        templates = [
            f"Can you {verb} {obj_phrase} {creative}?",
            f"I want to {verb} {obj_phrase} {creative}. What would you suggest?",
            f"Help me {verb} {obj_phrase} {creative}.",
        ]
        
        prompt = templates[var % len(templates)]
        
        if subject:
            prompt = prompt.replace(obj_phrase, f"{obj_phrase} regarding {subject.lower()}")
        if output:
            prompt = prompt.rstrip('.?') + f" Deliver as {output.lower()}."
        
        return prompt, 'creative', 'expert'
    
    def _get_evaluation_criteria(
        self, action: str, variant_type: str, obj: str, output: str
    ) -> Dict[str, List[str]]:
        """Determine evaluation criteria based on action and variant type"""
        
        action_upper = action.upper()
        specific_criteria = []
        
        # Action-specific criteria
        if action_upper in ['CREATE', 'WRITE', 'GENERATE', 'DRAFT']:
            specific_criteria.extend([
                f"Response should create appropriate {obj.lower()} content",
                "Content should be original, well-structured, and professional",
                "Format and tone should match the request context"
            ])
            
        elif action_upper in ['FIND', 'GET', 'LOCATE', 'SEARCH']:
            specific_criteria.extend([
                f"Response should identify and present relevant {obj.lower()}",
                "Information should be accurate and from reliable sources",
                "Results should be clearly organized and easy to understand"
            ])
            
        elif action_upper in ['SUMMARIZE', 'RECAP']:
            specific_criteria.extend([
                "Summary should capture all key points concisely",
                "Important details should not be omitted",
                "Summary should be well-organized and actionable"
            ])
            
        elif action_upper in ['EXPLAIN', 'DEFINE', 'DESCRIBE']:
            specific_criteria.extend([
                "Explanation should be clear and understandable",
                "Complex concepts should be broken down appropriately",
                "Technical terms should be defined when used"
            ])
            
        elif action_upper in ['LIST', 'ENUMERATE']:
            specific_criteria.extend([
                f"Response should provide a complete list of {obj.lower()}",
                "Items should be organized logically (priority, category, etc.)",
                "Each item should be clearly described"
            ])
            
        elif action_upper in ['SUGGEST', 'RECOMMEND', 'PROPOSE']:
            specific_criteria.extend([
                "Suggestions should be relevant and actionable",
                "Multiple options should be provided when appropriate",
                "Recommendations should be justified with reasoning"
            ])
            
        elif action_upper in ['ANALYZE', 'EVALUATE', 'ASSESS', 'REVIEW']:
            specific_criteria.extend([
                "Analysis should provide meaningful insights",
                "Conclusions should be supported by evidence",
                "Recommendations should be practical and actionable"
            ])
            
        elif action_upper in ['COMPARE', 'CONTRAST']:
            specific_criteria.extend([
                "Comparison should be balanced and fair",
                "Key differences and similarities should be highlighted",
                "Analysis should help inform decision-making"
            ])
        
        else:
            specific_criteria.extend([
                f"Response should appropriately address the {action.lower()} request",
                "Response should be complete and helpful",
                "Information should be accurate and well-presented"
            ])
        
        # Output-specific criteria
        if output:
            specific_criteria.append(f"Output should be formatted as {output.lower()}")
        
        # Variant-specific criteria
        if variant_type == 'multi_step':
            specific_criteria.append("All requested steps should be addressed in sequence")
        elif variant_type == 'analytical':
            specific_criteria.append("Analysis should include actionable insights")
        elif variant_type == 'comparative':
            specific_criteria.append("Comparison should be balanced and informative")
        elif variant_type == 'hypothetical':
            specific_criteria.append("Response should be tailored to the specified scenario")
        elif variant_type == 'creative':
            specific_criteria.append("Response should demonstrate creativity and originality")
        
        # Determine evaluation dimensions
        dimensions = ['accuracy', 'completeness', 'relevance', 'clarity', 'helpfulness']
        if action_upper in ['CREATE', 'WRITE', 'SUGGEST', 'DRAFT']:
            dimensions.append('creativity')
        if action_upper in ['SUGGEST', 'RECOMMEND', 'ANALYZE']:
            dimensions.append('actionability')
        
        return {
            'criteria': specific_criteria,
            'dimensions': dimensions
        }


def load_intents_from_csv(csv_path: str) -> List[IntentRow]:
    """Load and parse intent rows from CSV file"""
    intents = []
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            # Skip empty or invalid rows
            action = row.get('Action', '').strip()
            obj = row.get('Object', '').strip()
            
            if not action or not obj or action == '?' or obj == '?':
                continue
            
            try:
                intent = IntentRow(
                    action_rank=int(row.get('action_rank', 0) or 0),
                    rank_in_action=int(row.get('rank_in_action', 0) or 0),
                    reliable=row.get('Reliable', 'FALSE').upper() == 'TRUE',
                    inv_quality=row.get('Inv_Quality', 'FALSE').upper() == 'TRUE',
                    inv_retention=row.get('Inv_Retention', 'FALSE').upper() == 'TRUE',
                    unreliable=row.get('Unreliable', 'FALSE').upper() == 'TRUE',
                    action=action,
                    object_=obj,
                    subject=row.get('Subject', '').strip(),
                    output=row.get('Output', '').strip(),
                    pct_users=row.get('%_Users', '').strip(),
                    user_count=row.get(' UserCount ', '').strip(),
                    pct_impressions=row.get('%_Impressions', '').strip(),
                    impression_count=row.get(' ImpressionCount ', '').strip(),
                    sat_rate=row.get('SatRate', '').strip(),
                    feedback_count=int(row.get('FeedbackCount', 0) or 0),
                    apology_rate=row.get('ApologyRate', '').strip(),
                    no_citation_rate=row.get('NoCitationRate', '').strip(),
                    active_weeks_p75=float(row.get('Active_Weeks_p75', 1.0) or 1.0),
                    active_weeks_p90=float(row.get('Active_Weeks_p90', 1.0) or 1.0),
                    active_weeks_p95=float(row.get('Active_Weeks_p95', 1.0) or 1.0),
                    active_weeks_p99=float(row.get('Active_Weeks_p99', 1.0) or 1.0),
                    pct_active_weeks_p75=row.get('%_Active_weeks_p75', '').strip(),
                    pct_active_weeks_p90=row.get('%_Active_weeks_p90', '').strip(),
                    pct_active_weeks_p95=row.get('%_Active_weeks_p95', '').strip(),
                    pct_active_weeks_p99=row.get('%_Active_weeks_p99', '').strip(),
                    active_days_p75=float(row.get('Active_Days_p75', 1.0) or 1.0),
                    active_days_p90=float(row.get('Active_Days_p90', 1.0) or 1.0),
                    active_days_p95=float(row.get('Active_Days_p95', 1.0) or 1.0),
                    active_days_p99=float(row.get('Active_Days_p99', 1.0) or 1.0),
                    focus_days_p75=row.get('Focus_Days_p75', '').strip(),
                    focus_days_p90=row.get('Focus_Days_p90', '').strip(),
                    focus_days_p95=row.get('Focus_Days_p95', '').strip(),
                    focus_days_p99=row.get('Focus_Days_p99', '').strip(),
                    tenant_count=int(row.get('TenantCount', 0) or 0),
                    conversation_count=float(row.get('ConversationCount', 0) or 0),
                    day_count=row.get('DayCount', '').strip(),
                    week_count=row.get('WeekCount', '').strip(),
                    thumbs_up_count=int(row.get('ThumbsUpCountClipped', 0) or 0),
                    thumbs_down_count=int(row.get('ThumbsDownCountClipped', 0) or 0)
                )
                intents.append(intent)
            except Exception as e:
                print(f"Warning: Skipping row due to error: {e}")
                continue
    
    return intents


def main():
    """Main entry point for synthetic prompt generation"""
    
    # Configuration
    INPUT_CSV = "bizchat-work-nam_exploded-intents_20250215-20250509.csv"
    OUTPUT_DIR = Path("synthetic_prompts")
    OUTPUT_DIR.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    print("=" * 80)
    print("Synthetic Prompt Generator v2 - High Quality Generation")
    print("=" * 80)
    print(f"\nInput: {INPUT_CSV}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    # Load intents
    print("Loading intents from CSV...")
    intents = load_intents_from_csv(INPUT_CSV)
    print(f"Loaded {len(intents)} valid intent rows")
    
    # Initialize generator
    generator = HighQualitySyntheticPromptGenerator()
    
    # Generate prompts
    print("\nGenerating high-quality synthetic prompts...")
    all_prompts = []
    
    for i, intent in enumerate(intents):
        prompts = generator.generate_prompts_for_intent(intent, num_prompts=10)
        all_prompts.extend(prompts)
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(intents)} intents...")
    
    print(f"\nGenerated {len(all_prompts)} synthetic prompts")
    
    # Export to CSV
    csv_path = OUTPUT_DIR / f"synthetic_prompts_v2_{timestamp}.csv"
    
    if all_prompts:
        fieldnames = list(all_prompts[0].keys())
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_prompts)
        
        print(f"\nExported to: {csv_path}")
    
    # Export to JSON
    json_path = OUTPUT_DIR / f"synthetic_prompts_v2_{timestamp}.json"
    
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'source_file': INPUT_CSV,
            'total_intents': len(intents),
            'total_prompts': len(all_prompts),
            'prompts_per_intent': 10,
            'version': '2.0',
            'quality_improvements': [
                'Natural language phrasing',
                'No redundant subject/object',
                'Handles missing values gracefully',
                'Diverse non-duplicate prompts',
                'Professional enterprise context'
            ]
        },
        'prompts': all_prompts
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported to: {json_path}")
    
    # Print sample prompts for quality check
    print("\n" + "=" * 80)
    print("SAMPLE PROMPTS (Quality Check)")
    print("=" * 80)
    
    sample_indices = [0, 1, 2, 5, 8, 10, 20, 50, 100] if len(all_prompts) > 100 else range(min(10, len(all_prompts)))
    
    for idx in sample_indices:
        if idx < len(all_prompts):
            p = all_prompts[idx]
            print(f"\n[{p['synthetic_prompt_id']}] {p['prompt_variant_type']} ({p['complexity_level']})")
            print(f"  Source: {p['source_intent']}")
            print(f"  Prompt: {p['synthetic_prompt']}")
    
    # Print summary statistics
    print("\n" + "=" * 80)
    print("GENERATION SUMMARY")
    print("=" * 80)
    print(f"Total intents processed: {len(intents)}")
    print(f"Total synthetic prompts: {len(all_prompts)}")
    print(f"Prompts per intent: 10")
    
    # Variant distribution
    variant_counts = {}
    complexity_counts = {}
    for p in all_prompts:
        vt = p['prompt_variant_type']
        cl = p['complexity_level']
        variant_counts[vt] = variant_counts.get(vt, 0) + 1
        complexity_counts[cl] = complexity_counts.get(cl, 0) + 1
    
    print("\nVariant Distribution:")
    for vt, count in sorted(variant_counts.items()):
        print(f"  {vt}: {count}")
    
    print("\nComplexity Distribution:")
    for cl, count in sorted(complexity_counts.items()):
        print(f"  {cl}: {count}")
    
    print("\n" + "=" * 80)
    print("Generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
