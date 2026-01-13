"""
Synthetic Prompt Generator - Direct Generation Version
=======================================================

This script generates synthetic prompts directly without external API calls.
The generation logic is embedded in the code based on scientific constraints.

Usage:
    python generate_synthetic_prompts.py
"""

import csv
import json
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
import random


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


class SyntheticPromptGenerator:
    """
    Generates synthetic prompts based on scientific constraints.
    
    Constraint Categories:
    1. Linguistic: Natural language, clear action verbs, unambiguous
    2. Contextual: Enterprise context, professional tone, realistic scenarios
    3. Diversity: Varied sentence structures, multiple phrasings
    4. Quality: Grammatically correct, testable by LLM-as-judge
    """
    
    # Variant type definitions with generation strategies
    VARIANT_CONFIGS = {
        'direct_request': {
            'description': 'Simple, direct request',
            'complexity': 'simple',
            'templates': [
                "{action} {object}",
                "Can you {action_lower} {object_lower}?",
                "Please {action_lower} {object_lower}",
                "I need to {action_lower} {object_lower}",
                "{action} the {object_lower}"
            ]
        },
        'contextual': {
            'description': 'Request with workplace context',
            'complexity': 'medium',
            'templates': [
                "I'm preparing for a meeting and need to {action_lower} {object_lower}",
                "For my project, can you {action_lower} {object_lower}?",
                "My manager asked me to {action_lower} {object_lower}. Can you help?",
                "I'm working on a presentation and need to {action_lower} {object_lower}",
                "Before our team sync, I need to {action_lower} {object_lower}"
            ]
        },
        'conditional': {
            'description': 'Request with conditions',
            'complexity': 'medium',
            'templates': [
                "{action} {object_lower} only if it's from the last week",
                "If available, {action_lower} {object_lower} and highlight key points",
                "{action} {object_lower}, but focus on the most recent ones",
                "Can you {action_lower} {object_lower}? Only include items from this month",
                "{action} {object_lower} if there are any pending items"
            ]
        },
        'multi_step': {
            'description': 'Multi-step request',
            'complexity': 'complex',
            'templates': [
                "First {action_lower} {object_lower}, then summarize the key findings",
                "{action} {object_lower} and then create a brief report",
                "Can you {action_lower} {object_lower}, organize them by priority, and highlight urgent items?",
                "{action} {object_lower}, then compare with last month's data",
                "Please {action_lower} {object_lower}, categorize by type, and provide recommendations"
            ]
        },
        'analytical': {
            'description': 'Request requiring analysis',
            'complexity': 'complex',
            'templates': [
                "{action} {object_lower} and analyze the trends",
                "Can you {action_lower} {object_lower} and identify patterns?",
                "{action} {object_lower} and provide insights on what stands out",
                "Analyze and {action_lower} {object_lower} - what are the key takeaways?",
                "{action} {object_lower} and help me understand the implications"
            ]
        },
        'comparative': {
            'description': 'Comparison request',
            'complexity': 'complex',
            'templates': [
                "{action} {object_lower} and compare with previous versions",
                "Can you {action_lower} {object_lower} and show how it differs from last quarter?",
                "{action} {object_lower} from multiple sources and highlight differences",
                "Compare and {action_lower} {object_lower} across different departments",
                "{action} {object_lower} and contrast with industry benchmarks"
            ]
        },
        'hypothetical': {
            'description': 'Scenario-based request',
            'complexity': 'expert',
            'templates': [
                "If I needed to {action_lower} {object_lower} for a new client, how would you approach it?",
                "Imagine I'm presenting to executives - {action_lower} {object_lower} accordingly",
                "What if I need to {action_lower} {object_lower} for a regulatory audit?",
                "Suppose I'm onboarding a new team member - {action_lower} {object_lower} they should know",
                "In a crisis scenario, quickly {action_lower} {object_lower} for leadership"
            ]
        },
        'instructional': {
            'description': 'How-to request',
            'complexity': 'medium',
            'templates': [
                "How do I {action_lower} {object_lower} effectively?",
                "What's the best way to {action_lower} {object_lower}?",
                "Guide me through how to {action_lower} {object_lower}",
                "Can you show me how to {action_lower} {object_lower} step by step?",
                "I'm new to this - help me {action_lower} {object_lower}"
            ]
        },
        'creative': {
            'description': 'Open-ended creative request',
            'complexity': 'expert',
            'templates': [
                "{action} {object_lower} in a way that would impress stakeholders",
                "Creatively {action_lower} {object_lower} for maximum impact",
                "{action} {object_lower} with fresh ideas and innovative approaches",
                "Think outside the box and {action_lower} {object_lower}",
                "{action} {object_lower} as if you were a top consultant presenting to the board"
            ]
        },
        'clarification': {
            'description': 'Request with follow-up potential',
            'complexity': 'simple',
            'templates': [
                "I think I need to {action_lower} {object_lower} - is that right?",
                "Can you {action_lower} {object_lower}? I'm not sure what I'm looking for exactly",
                "{action} {object_lower} - or should I approach this differently?",
                "Help me {action_lower} {object_lower}, and let me know if you need more context",
                "I'd like to {action_lower} {object_lower}, but feel free to suggest alternatives"
            ]
        }
    }
    
    # Subject-specific templates when subject is available
    SUBJECT_TEMPLATES = {
        'direct_request': [
            "{action} {object_lower} from {subject_lower}",
            "Can you {action_lower} {object_lower} about {subject_lower}?",
            "{action} the {object_lower} related to {subject_lower}"
        ],
        'contextual': [
            "I'm reviewing {subject_lower} and need to {action_lower} {object_lower}",
            "Regarding {subject_lower}, please {action_lower} {object_lower}",
            "For the {subject_lower} project, {action_lower} {object_lower}"
        ],
        'analytical': [
            "{action} {object_lower} from {subject_lower} and analyze the findings",
            "Looking at {subject_lower}, {action_lower} {object_lower} and provide insights",
            "Analyze {subject_lower} by {action_lower} the relevant {object_lower}"
        ]
    }
    
    # Output-specific templates when output is specified
    OUTPUT_TEMPLATES = [
        "{action} {object_lower} and present as {output_lower}",
        "{action} {object_lower} - I need it formatted as {output_lower}",
        "Generate {output_lower} by {action_lower} {object_lower}",
        "{action} {object_lower} and output the results as {output_lower}"
    ]
    
    # Evaluation criteria mapping by action type
    EVALUATION_CRITERIA = {
        'CREATE': ['content_quality', 'completeness', 'originality', 'format_adherence'],
        'FIND': ['accuracy', 'relevance', 'source_citation', 'completeness'],
        'SUMMARIZE': ['conciseness', 'key_point_coverage', 'accuracy', 'clarity'],
        'EXPLAIN': ['clarity', 'accuracy', 'comprehensiveness', 'accessibility'],
        'LIST': ['completeness', 'organization', 'relevance', 'accuracy'],
        'SUGGEST': ['relevance', 'actionability', 'diversity', 'quality'],
        'PROVIDE': ['helpfulness', 'accuracy', 'completeness', 'format'],
        'ANALYZE': ['insight_depth', 'accuracy', 'comprehensiveness', 'actionability'],
        'COMPARE': ['accuracy', 'balance', 'insight', 'clarity'],
        'DEFAULT': ['accuracy', 'completeness', 'relevance', 'clarity', 'helpfulness']
    }
    
    def __init__(self):
        self.prompt_counter = 0
    
    def generate_prompts_for_intent(self, intent: IntentRow, num_prompts: int = 10) -> List[Dict[str, Any]]:
        """Generate synthetic prompts for a single intent row"""
        prompts = []
        
        # Normalize inputs
        action = intent.action.strip().upper()
        action_lower = action.lower()
        obj = intent.object_.strip() if intent.object_ else ""
        obj_lower = obj.lower()
        subject = intent.subject.strip() if intent.subject and intent.subject != '?' else ""
        subject_lower = subject.lower() if subject else ""
        output = intent.output.strip() if intent.output else ""
        output_lower = output.lower() if output else ""
        
        # Skip invalid rows
        if not action or not obj:
            return []
        
        # Determine variant distribution for 10 prompts
        variant_distribution = [
            ('direct_request', 'simple'),
            ('direct_request', 'simple'),
            ('contextual', 'medium'),
            ('contextual', 'medium'),
            ('conditional', 'medium'),
            ('multi_step', 'complex'),
            ('analytical', 'complex'),
            ('comparative', 'complex'),
            ('hypothetical', 'expert'),
            ('creative', 'expert')
        ]
        
        for variant_type, complexity in variant_distribution:
            self.prompt_counter += 1
            
            # Generate prompt text
            prompt_text = self._generate_prompt_text(
                action, action_lower, obj, obj_lower,
                subject, subject_lower, output, output_lower,
                variant_type
            )
            
            # Get evaluation criteria
            criteria = self._get_evaluation_criteria(action, variant_type, obj, output)
            
            # Create prompt record with all metadata
            prompt_record = {
                'synthetic_prompt_id': f'SP_{self.prompt_counter:06d}',
                'synthetic_prompt': prompt_text,
                'prompt_variant_type': variant_type,
                'complexity_level': complexity,
                'expected_response_criteria': json.dumps(criteria['criteria']),
                'evaluation_dimensions': json.dumps(criteria['dimensions']),
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
    
    def _generate_prompt_text(
        self,
        action: str, action_lower: str,
        obj: str, obj_lower: str,
        subject: str, subject_lower: str,
        output: str, output_lower: str,
        variant_type: str
    ) -> str:
        """Generate the actual prompt text based on variant type and components"""
        
        # Check if we have subject for subject-aware templates
        if subject and variant_type in self.SUBJECT_TEMPLATES:
            templates = self.SUBJECT_TEMPLATES[variant_type]
        else:
            templates = self.VARIANT_CONFIGS[variant_type]['templates']
        
        # Select a template randomly for variety
        template = random.choice(templates)
        
        # Format the template
        prompt = template.format(
            action=action,
            action_lower=action_lower,
            object=obj,
            object_lower=obj_lower,
            subject=subject if subject else "",
            subject_lower=subject_lower,
            output=output if output else "",
            output_lower=output_lower
        )
        
        # If output is specified, sometimes append output format
        if output and random.random() > 0.5:
            output_suffix = random.choice([
                f" as {output_lower}",
                f" formatted as {output_lower}",
                f" (output as {output_lower})"
            ])
            if output_lower not in prompt.lower():
                prompt += output_suffix
        
        # Clean up any double spaces
        prompt = ' '.join(prompt.split())
        
        return prompt
    
    def _get_evaluation_criteria(
        self, action: str, variant_type: str, obj: str, output: str
    ) -> Dict[str, List[str]]:
        """Determine evaluation criteria based on action and variant type"""
        
        # Get base criteria for action type
        action_upper = action.upper()
        base_criteria = self.EVALUATION_CRITERIA.get(
            action_upper, 
            self.EVALUATION_CRITERIA['DEFAULT']
        )
        
        # Build specific criteria based on context
        specific_criteria = []
        
        if action_upper in ['CREATE', 'WRITE', 'GENERATE']:
            specific_criteria.append(f"Response should create appropriate {obj.lower()}")
            specific_criteria.append("Content should be original and well-structured")
            
        elif action_upper in ['FIND', 'GET', 'LOCATE', 'SEARCH']:
            specific_criteria.append(f"Response should identify relevant {obj.lower()}")
            specific_criteria.append("Information should be accurate and sourced")
            
        elif action_upper in ['SUMMARIZE', 'RECAP']:
            specific_criteria.append("Summary should capture key points concisely")
            specific_criteria.append("Important details should not be omitted")
            
        elif action_upper in ['EXPLAIN', 'DEFINE', 'DESCRIBE']:
            specific_criteria.append("Explanation should be clear and understandable")
            specific_criteria.append("Technical terms should be defined if used")
            
        elif action_upper in ['LIST', 'ENUMERATE']:
            specific_criteria.append(f"Response should provide complete list of {obj.lower()}")
            specific_criteria.append("Items should be organized logically")
            
        elif action_upper in ['SUGGEST', 'RECOMMEND', 'PROPOSE']:
            specific_criteria.append("Suggestions should be actionable and relevant")
            specific_criteria.append("Multiple options should be provided when appropriate")
            
        elif action_upper in ['ANALYZE', 'EVALUATE', 'ASSESS']:
            specific_criteria.append("Analysis should provide meaningful insights")
            specific_criteria.append("Conclusions should be supported by evidence")
            
        elif action_upper in ['COMPARE', 'CONTRAST']:
            specific_criteria.append("Comparison should be balanced and fair")
            specific_criteria.append("Key differences and similarities should be highlighted")
        
        else:
            specific_criteria.append(f"Response should appropriately {action.lower()} {obj.lower()}")
            specific_criteria.append("Response should be helpful and complete")
        
        # Add output-specific criteria if output is specified
        if output:
            specific_criteria.append(f"Output should be formatted as {output.lower()}")
        
        # Add variant-specific criteria
        if variant_type == 'multi_step':
            specific_criteria.append("All steps should be addressed in sequence")
        elif variant_type == 'analytical':
            specific_criteria.append("Analysis should include actionable insights")
        elif variant_type == 'comparative':
            specific_criteria.append("Comparison should be balanced and informative")
        
        # Determine evaluation dimensions
        dimensions = ['accuracy', 'completeness', 'relevance', 'clarity']
        if action_upper in ['CREATE', 'WRITE', 'SUGGEST']:
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
            
            if not action or not obj:
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
    print("Synthetic Prompt Generator - Direct Generation")
    print("=" * 80)
    print(f"\nInput: {INPUT_CSV}")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    # Load intents
    print("Loading intents from CSV...")
    intents = load_intents_from_csv(INPUT_CSV)
    print(f"Loaded {len(intents)} valid intent rows")
    
    # Initialize generator
    generator = SyntheticPromptGenerator()
    
    # Generate prompts
    print("\nGenerating synthetic prompts...")
    all_prompts = []
    
    for i, intent in enumerate(intents):
        prompts = generator.generate_prompts_for_intent(intent, num_prompts=10)
        all_prompts.extend(prompts)
        
        if (i + 1) % 50 == 0:
            print(f"  Processed {i + 1}/{len(intents)} intents...")
    
    print(f"\nGenerated {len(all_prompts)} synthetic prompts")
    
    # Export to CSV
    csv_path = OUTPUT_DIR / f"synthetic_prompts_{timestamp}.csv"
    
    # Get all fieldnames from first record
    if all_prompts:
        fieldnames = list(all_prompts[0].keys())
        
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_prompts)
        
        print(f"\nExported to: {csv_path}")
    
    # Export to JSON
    json_path = OUTPUT_DIR / f"synthetic_prompts_{timestamp}.json"
    
    output_data = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'source_file': INPUT_CSV,
            'total_intents': len(intents),
            'total_prompts': len(all_prompts),
            'prompts_per_intent': 10
        },
        'prompts': all_prompts
    }
    
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    print(f"Exported to: {json_path}")
    
    # Export evaluation schema
    schema_path = OUTPUT_DIR / f"evaluation_schema_{timestamp}.json"
    
    schema = {
        'version': '1.0',
        'description': 'Schema for LLM-as-judge competitive evaluation',
        'evaluation_dimensions': {
            'accuracy': 'Factual correctness of the response',
            'completeness': 'Whether all aspects of the prompt are addressed',
            'relevance': 'How well the response matches the user intent',
            'clarity': 'Clarity and readability of the response',
            'actionability': 'How actionable the information provided is',
            'helpfulness': 'Overall helpfulness to the user',
            'creativity': 'Originality and creative quality (for generative tasks)'
        },
        'scoring': {
            'range': [1, 5],
            'criteria': {
                1: 'Poor - Does not meet basic expectations',
                2: 'Below Average - Partially meets expectations with gaps',
                3: 'Average - Meets basic expectations',
                4: 'Good - Exceeds expectations in most areas',
                5: 'Excellent - Exceptional quality'
            }
        },
        'comparison_targets': [
            {'name': 'Copilot', 'provider': 'Microsoft'},
            {'name': 'ChatGPT', 'provider': 'OpenAI'},
            {'name': 'Gemini', 'provider': 'Google'},
            {'name': 'Claude', 'provider': 'Anthropic'}
        ]
    }
    
    with open(schema_path, 'w', encoding='utf-8') as f:
        json.dump(schema, f, indent=2)
    
    print(f"Exported to: {schema_path}")
    
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
