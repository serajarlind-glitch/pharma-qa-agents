#!/usr/bin/env python3
"""
Workflow Automation Script
Chains multiple agents together for complex workflows
"""

import argparse
import yaml
from pathlib import Path
from datetime import datetime
import sys

# Import from agent.py
sys.path.insert(0, str(Path(__file__).parent))
from agent import Agent, Config, AGENTS, print_header

BASE_DIR = Path(__file__).parent.parent
WORKFLOWS_DIR = BASE_DIR / "workflows"
OUTPUTS_DIR = BASE_DIR / "outputs"


class Workflow:
    """Represents a multi-agent workflow"""
    
    def __init__(self, workflow_file: Path, config: Config):
        self.config = config
        self.workflow_file = workflow_file
        
        with open(workflow_file, 'r') as f:
            self.definition = yaml.safe_load(f)
        
        self.name = self.definition.get('name', 'Unnamed Workflow')
        self.steps = self.definition.get('steps', [])
        self.variables = {}
    
    def set_variables(self, var_dict: dict):
        """Set workflow variables"""
        self.variables.update(var_dict)
    
    def _replace_variables(self, text: str) -> str:
        """Replace ${variable} placeholders with values"""
        result = text
        for key, value in self.variables.items():
            result = result.replace(f"${{{key}}}", str(value))
        return result
    
    def run(self, output_dir: Path):
        """Execute the workflow"""
        print("\n" + "="*70)
        print(f"🔄 Running Workflow: {self.name}")
        print("="*70 + "\n")
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Track outputs from previous steps
        step_outputs = {}
        
        # Execute each step
        for i, step in enumerate(self.steps, 1):
            step_name = step.get('name', f'Step {i}')
            agent_name = step.get('agent')
            prompt_template = step.get('prompt', '')
            use_previous = step.get('use_previous_output', False)
            save_as = step.get('save_as')
            
            print(f"\n📍 Step {i}/{len(self.steps)}: {step_name}")
            print(f"   Agent: {AGENTS[agent_name]['name']}")
            print("-" * 70)
            
            # Create agent
            agent = Agent(agent_name, self.config)
            
            # Build prompt
            prompt = self._replace_variables(prompt_template)
            
            # If using previous output, append it to prompt
            if use_previous and step_outputs:
                previous_key = list(step_outputs.keys())[-1]
                previous_output = step_outputs[previous_key]
                prompt = f"{previous_output}\n\n{prompt}"
            
            # Execute query
            print(f"\n💬 Prompt:\n{prompt[:200]}{'...' if len(prompt) > 200 else ''}\n")
            print("🤔 Processing...\n")
            
            response = agent.query(prompt)
            
            # Save output
            if save_as:
                output_file = output_dir / self._replace_variables(save_as)
                output_file.parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, 'w') as f:
                    f.write(f"# {step_name}\n\n")
                    f.write(f"**Agent:** {AGENTS[agent_name]['name']}\n")
                    f.write(f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                    f.write("---\n\n")
                    f.write(response)
                print(f"💾 Saved: {output_file}")
                
                # Store for next step
                step_outputs[step_name] = response
            else:
                # Just print
                print(response)
                step_outputs[step_name] = response
            
            print("\n" + "="*70)
        
        # Create workflow summary
        summary_file = output_dir / "workflow-summary.md"
        with open(summary_file, 'w') as f:
            f.write(f"# Workflow Summary: {self.name}\n\n")
            f.write(f"**Executed:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Workflow File:** {self.workflow_file.name}\n\n")
            f.write(f"## Variables\n\n")
            for key, value in self.variables.items():
                f.write(f"- `{key}`: {value}\n")
            f.write(f"\n## Steps Completed\n\n")
            for i, step in enumerate(self.steps, 1):
                f.write(f"{i}. {step.get('name')} (Agent: {step.get('agent')})\n")
        
        print(f"\n✅ Workflow Complete!")
        print(f"📁 Output directory: {output_dir}")
        print(f"📄 Summary: {summary_file}\n")


def list_workflows():
    """List available workflow templates"""
    print("\n📋 Available Workflows:\n")
    
    if not WORKFLOWS_DIR.exists():
        print("No workflows directory found.")
        return
    
    workflow_files = list(WORKFLOWS_DIR.glob("*.yaml"))
    
    if not workflow_files:
        print("No workflow templates found in workflows/")
        return
    
    for wf_file in workflow_files:
        try:
            with open(wf_file, 'r') as f:
                wf_def = yaml.safe_load(f)
            name = wf_def.get('name', wf_file.stem)
            description = wf_def.get('description', 'No description')
            num_steps = len(wf_def.get('steps', []))
            
            print(f"📌 {wf_file.stem}")
            print(f"   Name: {name}")
            print(f"   Description: {description}")
            print(f"   Steps: {num_steps}")
            print()
        except Exception as e:
            print(f"❌ {wf_file.name}: Error loading ({e})")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Pharma QA Workflow Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available workflows
  python workflow.py --list
  
  # Run CAPA workflow
  python workflow.py capa-workflow --var deviation="Batch failed" --var batch="2024-0892"
  
  # Run with custom output directory
  python workflow.py validation-workflow --output outputs/validation-2024-03/
  
  # Run specific workflow file
  python workflow.py run workflows/custom-workflow.yaml
        """
    )
    
    parser.add_argument('workflow', nargs='?',
                       help='Workflow template name (without .yaml) or path to workflow file')
    parser.add_argument('-l', '--list', action='store_true',
                       help='List available workflow templates')
    parser.add_argument('-v', '--var', action='append',
                       help='Set workflow variable (format: key=value). Can be used multiple times.')
    parser.add_argument('-o', '--output', type=str,
                       help='Output directory (default: outputs/WORKFLOW_TIMESTAMP/)')
    parser.add_argument('--input', type=str,
                       help='Input text (sets ${input} variable)')
    
    args = parser.parse_args()
    
    # Handle --list
    if args.list:
        list_workflows()
        return
    
    if not args.workflow:
        parser.print_help()
        return
    
    # Determine workflow file
    if Path(args.workflow).exists():
        workflow_file = Path(args.workflow)
    elif (WORKFLOWS_DIR / f"{args.workflow}.yaml").exists():
        workflow_file = WORKFLOWS_DIR / f"{args.workflow}.yaml"
    else:
        print(f"❌ Workflow not found: {args.workflow}")
        print("\nAvailable workflows:")
        list_workflows()
        return
    
    # Load config and workflow
    config = Config()
    workflow = Workflow(workflow_file, config)
    
    # Set variables
    variables = {}
    
    # From --var arguments
    if args.var:
        for var_pair in args.var:
            if '=' not in var_pair:
                print(f"❌ Invalid variable format: {var_pair} (use key=value)")
                return
            key, value = var_pair.split('=', 1)
            variables[key.strip()] = value.strip()
    
    # From --input
    if args.input:
        variables['input'] = args.input
    
    workflow.set_variables(variables)
    
    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        timestamp = datetime.now().strftime('%Y%m%d-%H%M%S')
        output_dir = OUTPUTS_DIR / f"{workflow_file.stem}-{timestamp}"
    
    # Run workflow
    try:
        workflow.run(output_dir)
    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
    except Exception as e:
        print(f"\n❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
