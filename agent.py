#!/usr/bin/env python3
"""
Pharma QA Agents - Terminal CLI
Main agent interface script
"""

import argparse
import json
import os
import sys
from pathlib import Path
import requests
import yaml
from typing import Optional, List

# Base directory
BASE_DIR = Path(__file__).parent.parent
PROMPTS_DIR = BASE_DIR / "prompts"
CONFIG_FILE = BASE_DIR / "config.yaml"
KNOWLEDGE_DIR = BASE_DIR / "knowledge"
OUTPUTS_DIR = BASE_DIR / "outputs"

# Agent definitions
AGENTS = {
    "orchestrator": {"file": "01-orchestrator.txt", "name": "Workflow Orchestrator"},
    "quality": {"file": "02-quality-sentinel.txt", "name": "Quality & Regulatory Sentinel"},
    "lean": {"file": "03-lean-optimizer.txt", "name": "Lean Production Optimizer"},
    "project": {"file": "04-project-architect.txt", "name": "Project Architect"},
    "validation": {"file": "05-validation-specialist.txt", "name": "Validation Specialist"},
    "risk": {"file": "06-risk-assessment.txt", "name": "Risk Assessment Specialist"},
    "audit": {"file": "07-audit-readiness.txt", "name": "Audit & Inspection Readiness"},
    "document": {"file": "08-document-production.txt", "name": "Document Production Specialist"},
    "analytical": {"file": "09-analytical-method.txt", "name": "Analytical Method Writer"},
}


class Config:
    """Load and manage configuration"""
    def __init__(self):
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, 'r') as f:
                self.data = yaml.safe_load(f)
        else:
            # Default config
            self.data = {
                'ollama': {
                    'base_url': 'http://127.0.0.1:11434',
                    'model': 'qwen2.5:14b',
                    'temperature': 0.3,
                },
                'output': {
                    'default_format': 'markdown',
                    'save_history': True,
                }
            }
    
    def get_ollama_url(self):
        return self.data['ollama']['base_url']
    
    def get_model(self, agent_name=None):
        # Check for agent-specific model
        if agent_name and 'agents' in self.data:
            if agent_name in self.data['agents']:
                if 'model' in self.data['agents'][agent_name]:
                    return self.data['agents'][agent_name]['model']
        # Default model
        return self.data['ollama']['model']
    
    def get_temperature(self):
        return self.data['ollama'].get('temperature', 0.3)


class Agent:
    """Represents a single AI agent"""
    
    def __init__(self, name: str, config: Config):
        self.name = name
        self.config = config
        
        if name not in AGENTS:
            raise ValueError(f"Unknown agent: {name}. Available: {', '.join(AGENTS.keys())}")
        
        self.info = AGENTS[name]
        self.system_prompt = self._load_prompt()
        self.model = config.get_model(name)
    
    def _load_prompt(self) -> str:
        """Load system prompt from file"""
        prompt_file = PROMPTS_DIR / self.info['file']
        if not prompt_file.exists():
            raise FileNotFoundError(f"Prompt file not found: {prompt_file}")
        
        with open(prompt_file, 'r') as f:
            return f.read().strip()
    
    def query(self, user_message: str, context_docs: Optional[List[Path]] = None, 
              conversation_history: Optional[List] = None) -> str:
        """
        Send query to agent via Ollama API
        
        Args:
            user_message: The user's query
            context_docs: Optional list of PDF paths to include as context
            conversation_history: Optional previous messages
        
        Returns:
            Agent's response as string
        """
        # Build messages
        messages = []
        
        # System prompt
        messages.append({
            "role": "system",
            "content": self.system_prompt
        })
        
        # Add conversation history if provided
        if conversation_history:
            messages.extend(conversation_history)
        
        # Add document context if provided
        full_message = user_message
        if context_docs:
            context_text = self._load_documents(context_docs)
            if context_text:
                full_message = f"CONTEXT DOCUMENTS:\n{context_text}\n\nQUERY:\n{user_message}"
        
        # Add user message
        messages.append({
            "role": "user",
            "content": full_message
        })
        
        # Call Ollama API
        url = f"{self.config.get_ollama_url()}/api/chat"
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": self.config.get_temperature(),
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=300)
            response.raise_for_status()
            result = response.json()
            return result['message']['content']
        
        except requests.exceptions.ConnectionError:
            return "❌ ERROR: Cannot connect to Ollama. Is it running? Try: ollama serve"
        except requests.exceptions.Timeout:
            return "❌ ERROR: Request timed out. The model might be too large for your system."
        except Exception as e:
            return f"❌ ERROR: {str(e)}"
    
    def _load_documents(self, doc_paths: List[Path]) -> str:
        """Load and format document context (simplified - just filenames for now)"""
        # Note: Full PDF text extraction would require additional libraries
        # For now, just indicate which documents are referenced
        docs_list = [f"- {doc.name}" for doc in doc_paths if doc.exists()]
        if docs_list:
            return "Referenced documents:\n" + "\n".join(docs_list)
        return ""


def print_header(agent_name: str):
    """Print formatted agent header"""
    info = AGENTS[agent_name]
    print("\n" + "="*70)
    print(f"🤖 {info['name']}")
    print("="*70 + "\n")


def print_response(response: str, save_to: Optional[Path] = None):
    """Print and optionally save response"""
    print(response)
    print("\n" + "-"*70 + "\n")
    
    if save_to:
        save_to.parent.mkdir(parents=True, exist_ok=True)
        with open(save_to, 'w') as f:
            f.write(response)
        print(f"💾 Saved to: {save_to}")


def interactive_mode(agent: Agent):
    """Run agent in interactive conversation mode"""
    print_header(agent.name)
    print("Interactive mode - Type 'exit' to quit, 'clear' to reset conversation\n")
    
    conversation_history = []
    
    while True:
        try:
            user_input = input("You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() == 'exit':
                print("Goodbye! 👋")
                break
            
            if user_input.lower() == 'clear':
                conversation_history = []
                print("🗑️  Conversation cleared\n")
                continue
            
            # Query agent
            response = agent.query(user_input, conversation_history=conversation_history)
            
            # Add to history
            conversation_history.append({"role": "user", "content": user_input})
            conversation_history.append({"role": "assistant", "content": response})
            
            # Print response
            print(f"\n{agent.info['name']}:\n{response}\n")
        
        except KeyboardInterrupt:
            print("\n\nGoodbye! 👋")
            break
        except Exception as e:
            print(f"❌ Error: {e}")


def list_agents():
    """List all available agents"""
    print("\n📋 Available Agents:\n")
    for key, info in AGENTS.items():
        prompt_exists = (PROMPTS_DIR / info['file']).exists()
        status = "✅" if prompt_exists else "❌"
        print(f"{status} {key:15s} - {info['name']}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="Pharma QA Agents - Terminal CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all agents
  python agent.py --list
  
  # Ask orchestrator to route query
  python agent.py orchestrator "Batch failed dissolution test"
  
  # Direct query to quality agent
  python agent.py quality "Assess temperature excursion criticality"
  
  # Interactive mode
  python agent.py lean --interactive
  
  # With document context
  python agent.py quality --context knowledge/EudraLex.pdf "What does Annex 15 say?"
  
  # Save output
  python agent.py document "Create CAPA form" --output outputs/capa.md
        """
    )
    
    parser.add_argument('agent', nargs='?', choices=list(AGENTS.keys()) + ['list'],
                       help='Agent to use (or "list" to show all agents)')
    parser.add_argument('query', nargs='?', help='Your question or prompt')
    parser.add_argument('-i', '--interactive', action='store_true',
                       help='Start interactive conversation mode')
    parser.add_argument('-c', '--context', type=str,
                       help='Comma-separated paths to PDF documents for context')
    parser.add_argument('-o', '--output', type=str,
                       help='Save response to file')
    parser.add_argument('-l', '--list', action='store_true',
                       help='List all available agents')
    parser.add_argument('--stdin', action='store_true',
                       help='Read query from stdin (for piping)')
    
    args = parser.parse_args()
    
    # Handle --list flag
    if args.list or args.agent == 'list':
        list_agents()
        return
    
    # Validate arguments
    if not args.agent:
        parser.print_help()
        return
    
    if not args.interactive and not args.query and not args.stdin:
        print("❌ Error: Provide a query, use --interactive, or --stdin")
        parser.print_help()
        return
    
    # Load configuration
    config = Config()
    
    # Create agent
    try:
        agent = Agent(args.agent, config)
    except Exception as e:
        print(f"❌ Error loading agent: {e}")
        return
    
    # Interactive mode
    if args.interactive:
        interactive_mode(agent)
        return
    
    # Get query
    if args.stdin:
        query = sys.stdin.read().strip()
    else:
        query = args.query
    
    # Parse context documents
    context_docs = None
    if args.context:
        context_docs = [Path(p.strip()) for p in args.context.split(',')]
    
    # Run query
    print_header(args.agent)
    print(f"Query: {query}\n")
    print("🤔 Thinking...\n")
    
    response = agent.query(query, context_docs=context_docs)
    
    # Handle output
    output_file = Path(args.output) if args.output else None
    print_response(response, save_to=output_file)


if __name__ == "__main__":
    main()
