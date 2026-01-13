"""
Runner Script for Synthetic Prompt Generation
==============================================

This script provides a command-line interface for running the synthetic
prompt generation pipeline with various options for testing and production.

Usage:
    # Full generation (requires API key)
    python run_generation.py --mode full
    
    # Test with limited intents
    python run_generation.py --mode test --max-intents 5
    
    # Dry run (no API calls)
    python run_generation.py --mode dry-run
    
    # Generate evaluation schema only
    python run_generation.py --mode schema-only
"""

import os
import sys
import json
import argparse
import asyncio
from datetime import datetime
from pathlib import Path

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from synthetic_prompt_generator import (
    SyntheticPromptDataset,
    IntentComponents,
    IntentMetadata,
    SemanticAnalyzer,
    GenerationConstraints,
    ANTHROPIC_AVAILABLE
)

# Only import PromptGenerationEngine when needed (requires anthropic)
def get_generation_engine(api_key=None):
    """Get generation engine, importing only when needed"""
    from synthetic_prompt_generator import PromptGenerationEngine
    return PromptGenerationEngine(api_key=api_key)


def load_config(config_path: str = "config.json") -> dict:
    """Load configuration from JSON file"""
    with open(config_path, 'r') as f:
        return json.load(f)


def print_banner():
    """Print the application banner"""
    print()
    print("=" * 80)
    print("  SYNTHETIC PROMPT GENERATOR FOR LLM COMPETITIVE ANALYSIS")
    print("  Version 1.0.0")
    print("=" * 80)
    print()


def print_intent_analysis(dataset: SyntheticPromptDataset):
    """Print analysis of loaded intents"""
    print("\n--- Intent Analysis ---\n")
    
    # Analyze actions distribution
    action_counts = {}
    for components, _ in dataset.intents:
        action = components.action
        action_counts[action] = action_counts.get(action, 0) + 1
    
    print(f"Total Intents: {len(dataset.intents)}")
    print(f"Unique Actions: {len(action_counts)}")
    print("\nTop 15 Actions:")
    sorted_actions = sorted(action_counts.items(), key=lambda x: x[1], reverse=True)[:15]
    for action, count in sorted_actions:
        print(f"  {action}: {count}")
    
    # Analyze semantic categories
    print("\n--- Semantic Categories ---\n")
    category_counts = {}
    for components, _ in dataset.intents:
        category = SemanticAnalyzer.get_action_category(components.action)
        category_counts[category] = category_counts.get(category, 0) + 1
    
    for category, count in sorted(category_counts.items(), key=lambda x: x[1], reverse=True):
        print(f"  {category}: {count}")
    
    # Sample intents
    print("\n--- Sample Intents ---\n")
    for i, (components, metadata) in enumerate(dataset.intents[:5]):
        print(f"  {i+1}. {components.action} + {components.object_} "
              f"(Subject: {components.subject or 'N/A'}, Output: {components.output or 'N/A'})")
        print(f"     Semantic: {components.semantic_signature}")
        print(f"     Sat Rate: {metadata.sat_rate or 'N/A'}, Users: {metadata.user_count}")
        print()


def generate_sample_prompts_offline(dataset: SyntheticPromptDataset, num_samples: int = 3):
    """Generate sample prompts without API calls for demonstration"""
    print("\n--- Sample Prompt Templates (Offline Generation) ---\n")
    
    for i, (components, metadata) in enumerate(dataset.intents[:num_samples]):
        print(f"\nIntent {i+1}: {components.action} + {components.object_}")
        print("-" * 50)
        
        # Generate template-based prompts
        templates = generate_template_prompts(components)
        for j, (variant_type, prompt) in enumerate(templates[:5], 1):
            print(f"  {j}. [{variant_type}] {prompt}")


def generate_template_prompts(components: IntentComponents) -> list:
    """Generate template-based prompts for an intent (no LLM required)"""
    action = components.action.lower()
    obj = components.object_.lower() if components.object_ and components.object_ != '?' else "the item"
    subject = components.subject.lower() if components.subject and components.subject != '?' else None
    output = components.output.lower() if components.output else None
    
    templates = []
    
    # Direct request variants
    if subject:
        templates.append(("direct_request", f"Can you {action} {obj} from {subject}?"))
        templates.append(("direct_request", f"Please {action} the {obj} related to {subject}."))
    else:
        templates.append(("direct_request", f"Can you {action} {obj}?"))
        templates.append(("direct_request", f"I need to {action} {obj}."))
    
    # Contextual variants
    templates.append(("contextual", f"I'm working on a project and need to {action} {obj}. Can you help?"))
    templates.append(("contextual", f"For my upcoming meeting, I need to {action} {obj}."))
    
    # Conditional variants
    templates.append(("conditional", f"If possible, {action} {obj} and format it as a list."))
    templates.append(("conditional", f"{action.capitalize()} {obj} only if it's from the last week."))
    
    # Analytical variants
    templates.append(("analytical", f"Can you {action} {obj} and provide insights on the key themes?"))
    
    # Multi-step variants
    templates.append(("multi_step", f"First {action} {obj}, then summarize the key points."))
    
    # Output-specific variants
    if output:
        templates.append(("output_specific", f"{action.capitalize()} {obj} and present it as {output}."))
    
    return templates


async def run_full_generation(config: dict, max_intents: int = None):
    """Run full synthetic prompt generation"""
    
    base_path = Path(__file__).parent
    input_csv = base_path / config['paths']['input_csv']
    output_dir = base_path / config['paths']['output_dir']
    
    # Initialize
    dataset = SyntheticPromptDataset(str(input_csv), str(output_dir))
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("\nERROR: ANTHROPIC_API_KEY environment variable not set.")
        print("Set it using: $env:ANTHROPIC_API_KEY = 'your-api-key'")
        return
    
    engine = get_generation_engine(api_key=api_key)
    
    # Load intents
    num_intents = dataset.load_intents()
    print(f"\nLoaded {num_intents} intents from dataset")
    
    # Print analysis
    print_intent_analysis(dataset)
    
    # Generate prompts
    effective_max = max_intents or config['generation'].get('max_intents')
    prompts_per = config['generation']['prompts_per_intent']
    
    print(f"\nStarting generation...")
    print(f"  Prompts per intent: {prompts_per}")
    print(f"  Max intents: {effective_max or 'All'}")
    print(f"  Estimated total prompts: {(effective_max or num_intents) * prompts_per}")
    
    num_prompts = await dataset.generate_all_prompts(
        engine=engine,
        prompts_per_intent=prompts_per,
        batch_size=config['generation']['batch_size'],
        max_intents=effective_max
    )
    
    # Export
    csv_path = dataset.export_to_csv()
    json_path = dataset.export_to_json()
    schema_path = dataset.export_evaluation_schema()
    
    print(f"\n--- Generation Complete ---")
    print(f"Total prompts generated: {num_prompts}")
    print(f"\nExported files:")
    print(f"  CSV: {csv_path}")
    print(f"  JSON: {json_path}")
    print(f"  Schema: {schema_path}")


def run_dry_run(config: dict):
    """Run dry run to validate setup without API calls"""
    print("\n--- DRY RUN MODE ---")
    print("Validating configuration and data without making API calls.\n")
    
    base_path = Path(__file__).parent
    input_csv = base_path / config['paths']['input_csv']
    output_dir = base_path / config['paths']['output_dir']
    
    # Initialize dataset
    dataset = SyntheticPromptDataset(str(input_csv), str(output_dir))
    
    # Load and analyze
    num_intents = dataset.load_intents()
    print(f"✓ Loaded {num_intents} intents successfully")
    
    # Print analysis
    print_intent_analysis(dataset)
    
    # Generate sample prompts offline
    generate_sample_prompts_offline(dataset)
    
    # Validate constraints
    constraints = GenerationConstraints()
    print("\n--- Active Constraints ---")
    print(constraints.to_prompt_instructions())
    
    # Check API key
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if api_key:
        print("\n✓ ANTHROPIC_API_KEY is set")
    else:
        print("\n⚠ ANTHROPIC_API_KEY is NOT set")
        print("  Set it using: $env:ANTHROPIC_API_KEY = 'your-api-key'")
    
    # Check anthropic package
    if ANTHROPIC_AVAILABLE:
        print("✓ anthropic package is installed")
    else:
        print("⚠ anthropic package is NOT installed")
        print("  Install it using: pip install anthropic")
    
    # Estimate generation
    prompts_per = config['generation']['prompts_per_intent']
    print(f"\n--- Generation Estimate ---")
    print(f"  Intents: {num_intents}")
    print(f"  Prompts per intent: {prompts_per}")
    print(f"  Total prompts: {num_intents * prompts_per}")
    print(f"  Estimated API calls: {num_intents}")
    
    print("\n✓ Dry run complete. System ready for generation.")


def run_schema_only(config: dict):
    """Generate only the evaluation schema"""
    print("\n--- SCHEMA GENERATION MODE ---\n")
    
    base_path = Path(__file__).parent
    output_dir = base_path / config['paths']['output_dir']
    output_dir.mkdir(parents=True, exist_ok=True)
    
    input_csv = base_path / config['paths']['input_csv']
    dataset = SyntheticPromptDataset(str(input_csv), str(output_dir))
    
    schema_path = dataset.export_evaluation_schema()
    print(f"✓ Evaluation schema exported to: {schema_path}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Synthetic Prompt Generator for LLM Competitive Analysis',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_generation.py --mode dry-run          # Validate setup
  python run_generation.py --mode test --max 10    # Test with 10 intents
  python run_generation.py --mode full             # Full generation
  python run_generation.py --mode schema-only      # Generate schema only
        """
    )
    
    parser.add_argument(
        '--mode', '-m',
        choices=['full', 'test', 'dry-run', 'schema-only'],
        default='dry-run',
        help='Execution mode (default: dry-run)'
    )
    
    parser.add_argument(
        '--max-intents', '--max', '-n',
        type=int,
        default=None,
        help='Maximum number of intents to process'
    )
    
    parser.add_argument(
        '--config', '-c',
        default='config.json',
        help='Path to configuration file'
    )
    
    args = parser.parse_args()
    
    print_banner()
    
    # Load config
    config_path = Path(__file__).parent / args.config
    if not config_path.exists():
        print(f"ERROR: Configuration file not found: {config_path}")
        return 1
    
    config = load_config(str(config_path))
    print(f"Configuration loaded from: {config_path}")
    
    # Execute based on mode
    if args.mode == 'dry-run':
        run_dry_run(config)
    
    elif args.mode == 'schema-only':
        run_schema_only(config)
    
    elif args.mode == 'test':
        max_intents = args.max_intents or 5
        print(f"Running TEST mode with max {max_intents} intents")
        asyncio.run(run_full_generation(config, max_intents=max_intents))
    
    elif args.mode == 'full':
        print("Running FULL generation mode")
        asyncio.run(run_full_generation(config, max_intents=args.max_intents))
    
    print("\n" + "=" * 80)
    print("Done!")
    print("=" * 80 + "\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
