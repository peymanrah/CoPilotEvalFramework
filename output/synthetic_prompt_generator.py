"""
Synthetic Prompt Generator for Bizchat Intent Dataset
======================================================

A scientific, defensible approach to generating high-quality synthetic prompts
for LLM competitive analysis and benchmarking.

Author: Evaluation Framework Team
Date: January 2026

Methodology:
-----------
1. Intent Semantic Analysis: Parse Action/Intent, Object, Subject, and Output 
   to understand user intent taxonomy
2. Constraint-Based Generation: Apply linguistic and contextual constraints
   to ensure prompt quality and diversity
3. LLM-Powered Synthesis: Use Claude Opus 4.5 for intelligent prompt generation
4. Metadata Preservation: Maintain full traceability for downstream evaluation

Schema Design:
-------------
Input columns preserved as metadata:
- action_rank, rank_in_action: Intent hierarchy metrics
- Reliable, Inv_Quality, Inv_Retention, Unreliable: Quality flags
- Action, Object, Subject, Output: Intent taxonomy components
- %_Users, UserCount, %_Impressions, ImpressionCount: Usage metrics
- SatRate, FeedbackCount, ApologyRate, NoCitationRate: Quality metrics
- All percentile metrics for user engagement analysis

Output schema adds:
- synthetic_prompt_id: Unique identifier
- synthetic_prompt: The generated prompt text
- prompt_variant_type: Category of variation applied
- generation_constraints: Constraints used for generation
- expected_response_criteria: Criteria for LLM-as-judge evaluation
- complexity_level: simple/medium/complex/expert
- evaluation_dimensions: What aspects to evaluate (accuracy, completeness, etc.)
"""

import os
import json
import csv
import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
import re
from pathlib import Path

# Optional import for anthropic - only needed for actual generation
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('synthetic_prompt_generation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PromptComplexity(Enum):
    """Complexity levels for synthetic prompts"""
    SIMPLE = "simple"
    MEDIUM = "medium"
    COMPLEX = "complex"
    EXPERT = "expert"


class VariantType(Enum):
    """Types of prompt variations to generate"""
    DIRECT_REQUEST = "direct_request"
    CONTEXTUAL = "contextual"
    CONDITIONAL = "conditional"
    MULTI_STEP = "multi_step"
    CLARIFICATION_SEEKING = "clarification_seeking"
    COMPARATIVE = "comparative"
    HYPOTHETICAL = "hypothetical"
    INSTRUCTIONAL = "instructional"
    ANALYTICAL = "analytical"
    CREATIVE = "creative"


class EvaluationDimension(Enum):
    """Dimensions for LLM-as-judge evaluation"""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    RELEVANCE = "relevance"
    CLARITY = "clarity"
    ACTIONABILITY = "actionability"
    HELPFULNESS = "helpfulness"
    SAFETY = "safety"
    CONSISTENCY = "consistency"


@dataclass
class IntentComponents:
    """Parsed intent components from the dataset"""
    action: str
    object_: str
    subject: str
    output: str
    
    @property
    def semantic_signature(self) -> str:
        """Create a semantic signature for the intent"""
        parts = [self.action]
        if self.subject and self.subject != '?':
            parts.append(f"from/about {self.subject}")
        if self.object_ and self.object_ != '?':
            parts.append(f"the {self.object_}")
        if self.output:
            parts.append(f"as {self.output}")
        return " ".join(parts)


@dataclass
class GenerationConstraints:
    """Constraints for synthetic prompt generation"""
    # Linguistic constraints
    must_include_action_verb: bool = True
    preserve_intent_semantics: bool = True
    natural_language_style: bool = True
    avoid_ambiguity: bool = True
    
    # Contextual constraints
    enterprise_context: bool = True  # Business/work context
    professional_tone: bool = True
    realistic_scenario: bool = True
    
    # Diversity constraints
    vary_sentence_structure: bool = True
    include_context_details: bool = True
    multiple_phrasings: bool = True
    
    # Quality constraints
    grammatically_correct: bool = True
    clear_expected_output: bool = True
    testable_by_llm_judge: bool = True
    
    def to_prompt_instructions(self) -> str:
        """Convert constraints to prompt instructions for LLM"""
        instructions = []
        
        if self.must_include_action_verb:
            instructions.append("- Include a clear action verb aligned with the intent")
        if self.preserve_intent_semantics:
            instructions.append("- Preserve the core semantic meaning of the intent")
        if self.natural_language_style:
            instructions.append("- Use natural, conversational language")
        if self.avoid_ambiguity:
            instructions.append("- Be specific and unambiguous")
        if self.enterprise_context:
            instructions.append("- Frame within an enterprise/business context")
        if self.professional_tone:
            instructions.append("- Maintain professional tone appropriate for workplace")
        if self.realistic_scenario:
            instructions.append("- Create realistic scenarios users would actually encounter")
        if self.vary_sentence_structure:
            instructions.append("- Vary sentence structures across variants")
        if self.include_context_details:
            instructions.append("- Include relevant contextual details when appropriate")
        if self.grammatically_correct:
            instructions.append("- Ensure grammatical correctness")
        if self.clear_expected_output:
            instructions.append("- Make the expected output type clear from the prompt")
        if self.testable_by_llm_judge:
            instructions.append("- Design prompt so response quality can be objectively evaluated")
            
        return "\n".join(instructions)


@dataclass
class SyntheticPrompt:
    """A single synthetic prompt with full metadata"""
    # Generated content
    synthetic_prompt_id: str
    synthetic_prompt: str
    prompt_variant_type: str
    complexity_level: str
    generation_constraints: Dict[str, bool]
    expected_response_criteria: List[str]
    evaluation_dimensions: List[str]
    
    # Original metadata (preserved from input)
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


@dataclass 
class IntentMetadata:
    """Complete metadata for an intent row"""
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


class SemanticAnalyzer:
    """
    Analyzes semantic relationships between intent components.
    
    Action/Intent Taxonomy:
    - CREATE: Generative tasks (documents, content, artifacts)
    - FIND/GET: Retrieval and search tasks
    - SUMMARIZE: Condensation and synthesis tasks
    - EXPLAIN: Clarification and educational tasks
    - LIST: Enumeration tasks
    - SUGGEST/PROVIDE: Recommendation tasks
    - MODIFY/CONVERT: Transformation tasks
    - ANALYZE: Analytical and insight tasks
    - CHECK/DETERMINE: Verification tasks
    """
    
    # Action verb categories for semantic understanding
    ACTION_CATEGORIES = {
        'generative': ['CREATE', 'WRITE', 'GENERATE', 'COMPOSE', 'DRAFT'],
        'retrieval': ['FIND', 'GET', 'SEARCH', 'LOCATE', 'RETRIEVE'],
        'synthesis': ['SUMMARIZE', 'RECAP', 'CONDENSE', 'DIGEST'],
        'explanation': ['EXPLAIN', 'DEFINE', 'CLARIFY', 'DESCRIBE'],
        'enumeration': ['LIST', 'ENUMERATE', 'CATALOG', 'ITEMIZE'],
        'recommendation': ['SUGGEST', 'RECOMMEND', 'PROPOSE', 'ADVISE'],
        'transformation': ['MODIFY', 'CONVERT', 'TRANSFORM', 'CHANGE', 'REPLACE'],
        'analysis': ['ANALYZE', 'EVALUATE', 'ASSESS', 'REVIEW'],
        'verification': ['CHECK', 'VERIFY', 'VALIDATE', 'CONFIRM', 'DETERMINE'],
        'organization': ['ORGANIZE', 'ARRANGE', 'SORT', 'STRUCTURE'],
        'communication': ['SEND', 'SHARE', 'CONTACT', 'NOTIFY'],
        'enhancement': ['ENHANCE', 'IMPROVE', 'OPTIMIZE', 'FIX'],
        'inclusion': ['ADD', 'INCLUDE', 'ATTACH', 'INSERT'],
        'extraction': ['EXTRACT', 'HIGHLIGHT', 'IDENTIFY', 'COUNT'],
        'comparison': ['COMPARE', 'CONTRAST', 'DIFFERENTIATE'],
        'preparation': ['PREPARE', 'SET UP', 'CONFIGURE', 'SCHEDULE']
    }
    
    # Object categories for context understanding
    OBJECT_CATEGORIES = {
        'documents': ['DOCUMENT', 'FILE', 'ARTICLE', 'PROPOSAL', 'REPORT'],
        'communication': ['EMAIL', 'MESSAGE', 'MESSAGES', 'CHANNEL MESSAGES'],
        'content': ['TEXT', 'CODE', 'SCRIPT', 'CONTENT', 'STATEMENT'],
        'data': ['DATA', 'TABLE', 'LIST', 'FORMULA', 'GRAPH'],
        'media': ['IMAGE', 'PICTURE', 'PHOTO', 'DIAGRAM'],
        'presentations': ['PRESENTATION', 'SLIDE', 'DECK'],
        'meetings': ['MEETING', 'MEETING TIMES', 'AGENDA', 'ACTION ITEMS'],
        'organizational': ['PEOPLE', 'TEAMS', 'COMPANIES', 'ROLES', 'CONTACTS'],
        'tasks': ['TASKS', 'PROJECTS', 'TIMELINE', 'PLAN'],
        'information': ['INFORMATION', 'UPDATES', 'NEWS', 'SUMMARY', 'KEY TAKEAWAYS'],
        'resources': ['URL', 'LINK', 'TEMPLATE', 'RESOURCES', 'EXAMPLES'],
        'ideas': ['IDEAS', 'SUGGESTIONS', 'TIPS', 'BEST PRACTICES', 'INSIGHTS']
    }
    
    @classmethod
    def get_action_category(cls, action: str) -> str:
        """Get the semantic category for an action verb"""
        action_upper = action.upper()
        for category, verbs in cls.ACTION_CATEGORIES.items():
            if action_upper in verbs:
                return category
        return 'other'
    
    @classmethod
    def get_object_category(cls, obj: str) -> str:
        """Get the semantic category for an object"""
        if not obj or obj == '?':
            return 'unspecified'
        obj_upper = obj.upper()
        for category, objects in cls.OBJECT_CATEGORIES.items():
            if obj_upper in objects:
                return category
        return 'other'
    
    @classmethod
    def analyze_intent(cls, components: IntentComponents) -> Dict[str, Any]:
        """Perform comprehensive semantic analysis on intent components"""
        return {
            'action_category': cls.get_action_category(components.action),
            'object_category': cls.get_object_category(components.object_),
            'has_subject': bool(components.subject and components.subject != '?'),
            'has_explicit_output': bool(components.output),
            'semantic_signature': components.semantic_signature,
            'complexity_indicators': cls._assess_complexity(components)
        }
    
    @classmethod
    def _assess_complexity(cls, components: IntentComponents) -> Dict[str, bool]:
        """Assess complexity indicators for the intent"""
        return {
            'multi_component': all([
                components.action,
                components.object_ and components.object_ != '?',
                components.subject and components.subject != '?'
            ]),
            'has_transformation': components.action.upper() in ['CONVERT', 'TRANSFORM', 'MODIFY'],
            'requires_context': components.subject and components.subject != '?',
            'has_specified_output': bool(components.output)
        }


class PromptGenerationEngine:
    """
    Core engine for generating synthetic prompts using Claude Opus 4.5.
    
    Implements a multi-stage generation pipeline:
    1. Intent Analysis: Understand semantic structure
    2. Constraint Application: Apply quality constraints
    3. Variant Generation: Create diverse prompt variants
    4. Quality Validation: Ensure prompt meets criteria
    """
    
    VARIANT_TEMPLATES = {
        VariantType.DIRECT_REQUEST: "Direct, straightforward request matching the intent",
        VariantType.CONTEXTUAL: "Request with rich workplace context and background",
        VariantType.CONDITIONAL: "Request with specific conditions or prerequisites",
        VariantType.MULTI_STEP: "Complex request requiring multiple steps to fulfill",
        VariantType.CLARIFICATION_SEEKING: "Request that may need clarification or follow-up",
        VariantType.COMPARATIVE: "Request involving comparison or alternatives",
        VariantType.HYPOTHETICAL: "Hypothetical scenario-based request",
        VariantType.INSTRUCTIONAL: "Request for guidance or how-to information",
        VariantType.ANALYTICAL: "Request requiring analysis or insights",
        VariantType.CREATIVE: "Request with creative or open-ended elements"
    }
    
    COMPLEXITY_CRITERIA = {
        PromptComplexity.SIMPLE: {
            "description": "Single, clear task with obvious expected output",
            "word_range": (5, 20),
            "context_level": "minimal"
        },
        PromptComplexity.MEDIUM: {
            "description": "Task with some context or mild ambiguity",
            "word_range": (15, 40),
            "context_level": "moderate"
        },
        PromptComplexity.COMPLEX: {
            "description": "Multi-faceted task with specific requirements",
            "word_range": (30, 60),
            "context_level": "detailed"
        },
        PromptComplexity.EXPERT: {
            "description": "Sophisticated task requiring domain knowledge",
            "word_range": (40, 80),
            "context_level": "comprehensive"
        }
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """Initialize the prompt generation engine"""
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "The 'anthropic' package is required for prompt generation. "
                "Install it with: pip install anthropic"
            )
        self.api_key = api_key or os.environ.get('ANTHROPIC_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Anthropic API key required. Set ANTHROPIC_API_KEY environment variable "
                "or pass api_key parameter."
            )
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.constraints = GenerationConstraints()
        self.analyzer = SemanticAnalyzer()
    
    def generate_system_prompt(self) -> str:
        """Generate the system prompt for Claude"""
        return """You are an expert at generating high-quality synthetic prompts for AI chatbot evaluation.

Your task is to create realistic, diverse prompts that users might ask AI assistants like Copilot, ChatGPT, or Gemini in a workplace setting.

Key principles:
1. AUTHENTICITY: Create prompts that real users would actually ask
2. DIVERSITY: Vary phrasing, complexity, and context across variants
3. TESTABILITY: Design prompts so responses can be objectively evaluated
4. CLARITY: Make the user's intent and expected output clear
5. PROFESSIONALISM: Maintain enterprise-appropriate language and scenarios

You will receive intent components (Action, Object, Subject, Output) and must generate prompts that capture the semantic essence while varying the expression.

Output Format: JSON array of prompt objects with fields:
- prompt: The synthetic prompt text
- variant_type: Category of variation (direct_request, contextual, conditional, etc.)
- complexity_level: simple/medium/complex/expert
- expected_response_criteria: List of criteria for evaluating responses
- evaluation_dimensions: Which aspects to evaluate (accuracy, completeness, etc.)"""

    def generate_user_prompt(
        self,
        components: IntentComponents,
        metadata: IntentMetadata,
        num_variants: int = 10
    ) -> str:
        """Generate the user prompt for Claude to create synthetic prompts"""
        analysis = self.analyzer.analyze_intent(components)
        
        # Calculate quality signals from metadata
        quality_context = self._get_quality_context(metadata)
        
        prompt = f"""Generate {num_variants} diverse synthetic prompts for the following intent:

## Intent Components
- **Action/Intent**: {components.action}
- **Object**: {components.object_ if components.object_ and components.object_ != '?' else 'Not specified'}
- **Subject**: {components.subject if components.subject and components.subject != '?' else 'Not specified'}
- **Expected Output**: {components.output if components.output else 'Not specified'}

## Semantic Analysis
- Action Category: {analysis['action_category']}
- Object Category: {analysis['object_category']}
- Semantic Signature: {analysis['semantic_signature']}

## Quality Context from Usage Data
{quality_context}

## Generation Constraints
{self.constraints.to_prompt_instructions()}

## Required Variant Distribution
Generate prompts with the following variant distribution:
1. Direct Request (2 prompts): Straightforward requests
2. Contextual (2 prompts): Rich workplace context
3. Conditional/Multi-step (2 prompts): With conditions or multiple parts
4. Analytical/Comparative (2 prompts): Requiring analysis or comparison
5. Creative/Hypothetical (2 prompts): Open-ended or scenario-based

## Complexity Distribution
- 2 prompts: SIMPLE (5-20 words, minimal context)
- 3 prompts: MEDIUM (15-40 words, moderate context)
- 3 prompts: COMPLEX (30-60 words, detailed requirements)
- 2 prompts: EXPERT (40-80 words, domain expertise needed)

## Output Requirements
Return a JSON array with exactly {num_variants} objects. Each object must have:
{{
    "prompt": "The synthetic prompt text",
    "variant_type": "direct_request|contextual|conditional|multi_step|clarification_seeking|comparative|hypothetical|instructional|analytical|creative",
    "complexity_level": "simple|medium|complex|expert",
    "expected_response_criteria": ["criterion1", "criterion2", ...],
    "evaluation_dimensions": ["accuracy", "completeness", "relevance", etc.]
}}

Generate diverse, high-quality prompts that would realistically be asked to an AI assistant in an enterprise workplace context."""

        return prompt
    
    def _get_quality_context(self, metadata: IntentMetadata) -> str:
        """Extract quality context from metadata for informed generation"""
        context_parts = []
        
        # User engagement
        context_parts.append(f"- User engagement: {metadata.pct_users} of users ({metadata.user_count} total)")
        
        # Satisfaction rate (if available)
        if metadata.sat_rate:
            context_parts.append(f"- Satisfaction rate: {metadata.sat_rate}")
        
        # Quality flags
        if metadata.reliable:
            context_parts.append("- This is a RELIABLE intent pattern")
        
        # Apology and citation rates (quality indicators)
        if metadata.apology_rate and metadata.apology_rate != '0%':
            context_parts.append(f"- Apology rate: {metadata.apology_rate} (indicates potential difficulty)")
        if metadata.no_citation_rate and metadata.no_citation_rate != '0%':
            context_parts.append(f"- No-citation rate: {metadata.no_citation_rate}")
        
        # Tenant diversity
        context_parts.append(f"- Used across {metadata.tenant_count} tenants (enterprise diversity)")
        
        return "\n".join(context_parts)
    
    async def generate_prompts_for_intent(
        self,
        components: IntentComponents,
        metadata: IntentMetadata,
        num_variants: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate synthetic prompts for a single intent using Claude Opus 4.5"""
        
        system_prompt = self.generate_system_prompt()
        user_prompt = self.generate_user_prompt(components, metadata, num_variants)
        
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Using Claude Sonnet 4 as a robust option
                max_tokens=4096,
                system=system_prompt,
                messages=[
                    {"role": "user", "content": user_prompt}
                ]
            )
            
            # Parse the response
            content = response.content[0].text
            
            # Extract JSON from response
            prompts_data = self._parse_json_response(content)
            
            return prompts_data
            
        except Exception as e:
            logger.error(f"Error generating prompts: {e}")
            raise
    
    def _parse_json_response(self, content: str) -> List[Dict[str, Any]]:
        """Parse JSON response from Claude, handling potential formatting issues"""
        # Try direct JSON parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # Try to find JSON array in response
        json_match = re.search(r'\[[\s\S]*\]', content)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try to find JSON between code blocks
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', content)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1))
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Could not parse JSON from response: {content[:500]}...")


class SyntheticPromptDataset:
    """
    Manager for the synthetic prompt dataset.
    Handles loading, generation, and export of synthetic prompts.
    """
    
    def __init__(self, input_csv_path: str, output_dir: str):
        """Initialize the dataset manager"""
        self.input_csv_path = Path(input_csv_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.intents: List[Tuple[IntentComponents, IntentMetadata]] = []
        self.synthetic_prompts: List[SyntheticPrompt] = []
        
    def load_intents(self) -> int:
        """Load intents from the input CSV file"""
        logger.info(f"Loading intents from {self.input_csv_path}")
        
        with open(self.input_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    components = IntentComponents(
                        action=row.get('Action', '').strip(),
                        object_=row.get('Object', '').strip(),
                        subject=row.get('Subject', '').strip(),
                        output=row.get('Output', '').strip()
                    )
                    
                    metadata = IntentMetadata(
                        action_rank=int(row.get('action_rank', 0)),
                        rank_in_action=int(row.get('rank_in_action', 0)),
                        reliable=row.get('Reliable', 'FALSE').upper() == 'TRUE',
                        inv_quality=row.get('Inv_Quality', 'FALSE').upper() == 'TRUE',
                        inv_retention=row.get('Inv_Retention', 'FALSE').upper() == 'TRUE',
                        unreliable=row.get('Unreliable', 'FALSE').upper() == 'TRUE',
                        action=row.get('Action', '').strip(),
                        object_=row.get('Object', '').strip(),
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
                    
                    self.intents.append((components, metadata))
                    
                except Exception as e:
                    logger.warning(f"Error parsing row: {e}")
                    continue
        
        logger.info(f"Loaded {len(self.intents)} intents")
        return len(self.intents)
    
    async def generate_all_prompts(
        self,
        engine: PromptGenerationEngine,
        prompts_per_intent: int = 10,
        batch_size: int = 5,
        max_intents: Optional[int] = None
    ) -> int:
        """Generate synthetic prompts for all loaded intents"""
        
        intents_to_process = self.intents[:max_intents] if max_intents else self.intents
        total_intents = len(intents_to_process)
        
        logger.info(f"Generating {prompts_per_intent} prompts each for {total_intents} intents")
        
        prompt_id_counter = 0
        
        for batch_start in range(0, total_intents, batch_size):
            batch_end = min(batch_start + batch_size, total_intents)
            batch = intents_to_process[batch_start:batch_end]
            
            logger.info(f"Processing batch {batch_start//batch_size + 1}: intents {batch_start+1}-{batch_end}")
            
            for components, metadata in batch:
                try:
                    # Generate prompts for this intent
                    generated_prompts = await engine.generate_prompts_for_intent(
                        components, metadata, prompts_per_intent
                    )
                    
                    # Create SyntheticPrompt objects with full metadata
                    for prompt_data in generated_prompts:
                        prompt_id_counter += 1
                        
                        synthetic_prompt = SyntheticPrompt(
                            synthetic_prompt_id=f"SP_{prompt_id_counter:06d}",
                            synthetic_prompt=prompt_data.get('prompt', ''),
                            prompt_variant_type=prompt_data.get('variant_type', 'unknown'),
                            complexity_level=prompt_data.get('complexity_level', 'medium'),
                            generation_constraints=asdict(engine.constraints),
                            expected_response_criteria=prompt_data.get('expected_response_criteria', []),
                            evaluation_dimensions=prompt_data.get('evaluation_dimensions', []),
                            # Preserve all original metadata
                            action_rank=metadata.action_rank,
                            rank_in_action=metadata.rank_in_action,
                            reliable=metadata.reliable,
                            inv_quality=metadata.inv_quality,
                            inv_retention=metadata.inv_retention,
                            unreliable=metadata.unreliable,
                            action=metadata.action,
                            object_=metadata.object_,
                            subject=metadata.subject,
                            output=metadata.output,
                            pct_users=metadata.pct_users,
                            user_count=metadata.user_count,
                            pct_impressions=metadata.pct_impressions,
                            impression_count=metadata.impression_count,
                            sat_rate=metadata.sat_rate,
                            feedback_count=metadata.feedback_count,
                            apology_rate=metadata.apology_rate,
                            no_citation_rate=metadata.no_citation_rate,
                            active_weeks_p75=metadata.active_weeks_p75,
                            active_weeks_p90=metadata.active_weeks_p90,
                            active_weeks_p95=metadata.active_weeks_p95,
                            active_weeks_p99=metadata.active_weeks_p99,
                            pct_active_weeks_p75=metadata.pct_active_weeks_p75,
                            pct_active_weeks_p90=metadata.pct_active_weeks_p90,
                            pct_active_weeks_p95=metadata.pct_active_weeks_p95,
                            pct_active_weeks_p99=metadata.pct_active_weeks_p99,
                            active_days_p75=metadata.active_days_p75,
                            active_days_p90=metadata.active_days_p90,
                            active_days_p95=metadata.active_days_p95,
                            active_days_p99=metadata.active_days_p99,
                            focus_days_p75=metadata.focus_days_p75,
                            focus_days_p90=metadata.focus_days_p90,
                            focus_days_p95=metadata.focus_days_p95,
                            focus_days_p99=metadata.focus_days_p99,
                            tenant_count=metadata.tenant_count,
                            conversation_count=metadata.conversation_count,
                            day_count=metadata.day_count,
                            week_count=metadata.week_count,
                            thumbs_up_count=metadata.thumbs_up_count,
                            thumbs_down_count=metadata.thumbs_down_count
                        )
                        
                        self.synthetic_prompts.append(synthetic_prompt)
                    
                    logger.info(f"Generated {len(generated_prompts)} prompts for intent: "
                               f"{components.action} {components.object_}")
                    
                except Exception as e:
                    logger.error(f"Error generating prompts for {components.action} "
                               f"{components.object_}: {e}")
                    continue
            
            # Small delay between batches to respect rate limits
            await asyncio.sleep(1)
        
        logger.info(f"Total synthetic prompts generated: {len(self.synthetic_prompts)}")
        return len(self.synthetic_prompts)
    
    def export_to_csv(self, filename: Optional[str] = None) -> str:
        """Export synthetic prompts to CSV with full metadata"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"synthetic_prompts_{timestamp}.csv"
        
        output_path = self.output_dir / filename
        
        # Define CSV columns
        columns = [
            # Generated fields
            'synthetic_prompt_id',
            'synthetic_prompt',
            'prompt_variant_type',
            'complexity_level',
            'generation_constraints',
            'expected_response_criteria',
            'evaluation_dimensions',
            # Original metadata
            'action_rank',
            'rank_in_action',
            'reliable',
            'inv_quality',
            'inv_retention',
            'unreliable',
            'action',
            'object',
            'subject',
            'output',
            'pct_users',
            'user_count',
            'pct_impressions',
            'impression_count',
            'sat_rate',
            'feedback_count',
            'apology_rate',
            'no_citation_rate',
            'active_weeks_p75',
            'active_weeks_p90',
            'active_weeks_p95',
            'active_weeks_p99',
            'pct_active_weeks_p75',
            'pct_active_weeks_p90',
            'pct_active_weeks_p95',
            'pct_active_weeks_p99',
            'active_days_p75',
            'active_days_p90',
            'active_days_p95',
            'active_days_p99',
            'focus_days_p75',
            'focus_days_p90',
            'focus_days_p95',
            'focus_days_p99',
            'tenant_count',
            'conversation_count',
            'day_count',
            'week_count',
            'thumbs_up_count',
            'thumbs_down_count'
        ]
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            
            for sp in self.synthetic_prompts:
                row = {
                    'synthetic_prompt_id': sp.synthetic_prompt_id,
                    'synthetic_prompt': sp.synthetic_prompt,
                    'prompt_variant_type': sp.prompt_variant_type,
                    'complexity_level': sp.complexity_level,
                    'generation_constraints': json.dumps(sp.generation_constraints),
                    'expected_response_criteria': json.dumps(sp.expected_response_criteria),
                    'evaluation_dimensions': json.dumps(sp.evaluation_dimensions),
                    'action_rank': sp.action_rank,
                    'rank_in_action': sp.rank_in_action,
                    'reliable': sp.reliable,
                    'inv_quality': sp.inv_quality,
                    'inv_retention': sp.inv_retention,
                    'unreliable': sp.unreliable,
                    'action': sp.action,
                    'object': sp.object_,
                    'subject': sp.subject,
                    'output': sp.output,
                    'pct_users': sp.pct_users,
                    'user_count': sp.user_count,
                    'pct_impressions': sp.pct_impressions,
                    'impression_count': sp.impression_count,
                    'sat_rate': sp.sat_rate,
                    'feedback_count': sp.feedback_count,
                    'apology_rate': sp.apology_rate,
                    'no_citation_rate': sp.no_citation_rate,
                    'active_weeks_p75': sp.active_weeks_p75,
                    'active_weeks_p90': sp.active_weeks_p90,
                    'active_weeks_p95': sp.active_weeks_p95,
                    'active_weeks_p99': sp.active_weeks_p99,
                    'pct_active_weeks_p75': sp.pct_active_weeks_p75,
                    'pct_active_weeks_p90': sp.pct_active_weeks_p90,
                    'pct_active_weeks_p95': sp.pct_active_weeks_p95,
                    'pct_active_weeks_p99': sp.pct_active_weeks_p99,
                    'active_days_p75': sp.active_days_p75,
                    'active_days_p90': sp.active_days_p90,
                    'active_days_p95': sp.active_days_p95,
                    'active_days_p99': sp.active_days_p99,
                    'focus_days_p75': sp.focus_days_p75,
                    'focus_days_p90': sp.focus_days_p90,
                    'focus_days_p95': sp.focus_days_p95,
                    'focus_days_p99': sp.focus_days_p99,
                    'tenant_count': sp.tenant_count,
                    'conversation_count': sp.conversation_count,
                    'day_count': sp.day_count,
                    'week_count': sp.week_count,
                    'thumbs_up_count': sp.thumbs_up_count,
                    'thumbs_down_count': sp.thumbs_down_count
                }
                writer.writerow(row)
        
        logger.info(f"Exported {len(self.synthetic_prompts)} prompts to {output_path}")
        return str(output_path)
    
    def export_to_json(self, filename: Optional[str] = None) -> str:
        """Export synthetic prompts to JSON with full metadata"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"synthetic_prompts_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'source_file': str(self.input_csv_path),
                'total_intents': len(self.intents),
                'total_synthetic_prompts': len(self.synthetic_prompts),
                'generation_constraints': asdict(GenerationConstraints())
            },
            'prompts': [asdict(sp) for sp in self.synthetic_prompts]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Exported {len(self.synthetic_prompts)} prompts to {output_path}")
        return str(output_path)
    
    def export_evaluation_schema(self, filename: Optional[str] = None) -> str:
        """Export schema for LLM-as-judge evaluation"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"evaluation_schema_{timestamp}.json"
        
        output_path = self.output_dir / filename
        
        schema = {
            'version': '1.0',
            'description': 'Schema for LLM-as-judge competitive evaluation',
            'evaluation_framework': {
                'dimensions': {
                    dim.value: {
                        'description': self._get_dimension_description(dim),
                        'scoring_range': [1, 5],
                        'scoring_criteria': self._get_scoring_criteria(dim)
                    }
                    for dim in EvaluationDimension
                },
                'aggregation_method': 'weighted_average',
                'comparison_metrics': [
                    'win_rate',
                    'average_score',
                    'dimension_breakdown',
                    'complexity_performance',
                    'variant_type_performance'
                ]
            },
            'prompt_schema': {
                'required_fields': [
                    'synthetic_prompt_id',
                    'synthetic_prompt',
                    'prompt_variant_type',
                    'complexity_level',
                    'expected_response_criteria',
                    'evaluation_dimensions'
                ],
                'metadata_fields': [
                    'action', 'object', 'subject', 'output',
                    'sat_rate', 'feedback_count', 'tenant_count'
                ]
            },
            'comparison_targets': [
                {'name': 'Copilot', 'provider': 'Microsoft'},
                {'name': 'ChatGPT', 'provider': 'OpenAI'},
                {'name': 'Gemini', 'provider': 'Google'},
                {'name': 'Claude', 'provider': 'Anthropic'}
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2)
        
        logger.info(f"Exported evaluation schema to {output_path}")
        return str(output_path)
    
    def _get_dimension_description(self, dim: EvaluationDimension) -> str:
        """Get description for evaluation dimension"""
        descriptions = {
            EvaluationDimension.ACCURACY: "Factual correctness of the response",
            EvaluationDimension.COMPLETENESS: "Whether all aspects of the prompt are addressed",
            EvaluationDimension.RELEVANCE: "How well the response matches the user's intent",
            EvaluationDimension.CLARITY: "Clarity and readability of the response",
            EvaluationDimension.ACTIONABILITY: "How actionable the information provided is",
            EvaluationDimension.HELPFULNESS: "Overall helpfulness to the user",
            EvaluationDimension.SAFETY: "Absence of harmful or inappropriate content",
            EvaluationDimension.CONSISTENCY: "Internal consistency of the response"
        }
        return descriptions.get(dim, "No description available")
    
    def _get_scoring_criteria(self, dim: EvaluationDimension) -> Dict[int, str]:
        """Get scoring criteria for evaluation dimension"""
        base_criteria = {
            1: "Poor - Does not meet basic expectations",
            2: "Below Average - Partially meets expectations with significant gaps",
            3: "Average - Meets basic expectations",
            4: "Good - Exceeds expectations in most areas",
            5: "Excellent - Exceptional quality, fully meets all expectations"
        }
        return base_criteria


async def main():
    """Main entry point for synthetic prompt generation"""
    
    # Configuration
    INPUT_CSV = r"c:\Users\perahmat\OneDrive - Microsoft\Evaluation Framework\output\bizchat-work-nam_exploded-intents_20250215-20250509.csv"
    OUTPUT_DIR = r"c:\Users\perahmat\OneDrive - Microsoft\Evaluation Framework\output\synthetic_prompts"
    
    # Optional: Limit for testing (set to None for full dataset)
    MAX_INTENTS = None  # Set to e.g., 10 for testing
    PROMPTS_PER_INTENT = 10
    
    print("=" * 80)
    print("Synthetic Prompt Generator for Bizchat Intent Dataset")
    print("=" * 80)
    print(f"\nInput: {INPUT_CSV}")
    print(f"Output: {OUTPUT_DIR}")
    print(f"Prompts per intent: {PROMPTS_PER_INTENT}")
    if MAX_INTENTS:
        print(f"Max intents to process: {MAX_INTENTS}")
    print()
    
    # Check for API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Please set it with: $env:ANTHROPIC_API_KEY = 'your-api-key'")
        return
    
    # Initialize components
    dataset = SyntheticPromptDataset(INPUT_CSV, OUTPUT_DIR)
    engine = PromptGenerationEngine(api_key=api_key)
    
    # Load intents
    num_intents = dataset.load_intents()
    print(f"Loaded {num_intents} intents from dataset")
    
    # Generate prompts
    print("\nStarting prompt generation...")
    num_prompts = await dataset.generate_all_prompts(
        engine=engine,
        prompts_per_intent=PROMPTS_PER_INTENT,
        batch_size=5,
        max_intents=MAX_INTENTS
    )
    
    print(f"\nGenerated {num_prompts} synthetic prompts")
    
    # Export results
    csv_path = dataset.export_to_csv()
    json_path = dataset.export_to_json()
    schema_path = dataset.export_evaluation_schema()
    
    print(f"\nExported results:")
    print(f"  - CSV: {csv_path}")
    print(f"  - JSON: {json_path}")
    print(f"  - Evaluation Schema: {schema_path}")
    
    print("\n" + "=" * 80)
    print("Generation complete!")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
