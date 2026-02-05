# pyright: reportMissingImports=false
import asyncio
import os
import sys
from dataclasses import dataclass
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from dotenv import load_dotenv

load_dotenv()

# Third-party imports
import gradio as gr  # type: ignore
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Local module imports
from browser_use import Agent, Browser

# Try to import available LLMs
try:
	from browser_use.llm import ChatOpenAI
except ImportError:
	from langchain_openai import ChatOpenAI

try:
	from browser_use.llm import ChatBrowserUse
	HAS_BROWSER_USE_LLM = True
except ImportError:
	HAS_BROWSER_USE_LLM = False
	ChatBrowserUse = None


# Custom CSS for Gemini-like appearance
CUSTOM_CSS = """
.gradio-container {
    max-width: 1400px !important;
    margin: auto !important;
    font-family: 'Google Sans', 'Segoe UI', Tahoma, sans-serif !important;
}

.header-container {
    text-align: center;
    padding: 2rem 0;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 16px;
    margin-bottom: 2rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}

.header-title {
    font-size: 3rem !important;
    font-weight: 600 !important;
    color: white !important;
    margin: 0 !important;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
}

.header-subtitle {
    font-size: 1.2rem !important;
    color: rgba(255,255,255,0.9) !important;
    margin-top: 0.5rem !important;
}

.chat-container {
    border-radius: 16px !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1) !important;
    background: #f8f9fa !important;
    padding: 1.5rem !important;
}

.input-box {
    border-radius: 24px !important;
    border: 2px solid #e0e0e0 !important;
    padding: 1rem !important;
    font-size: 1rem !important;
    transition: all 0.3s ease !important;
}

.input-box:focus {
    border-color: #667eea !important;
    box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
}

.btn-primary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
    border: none !important;
    border-radius: 24px !important;
    padding: 0.75rem 2rem !important;
    font-size: 1rem !important;
    font-weight: 600 !important;
    color: white !important;
    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3) !important;
    transition: all 0.3s ease !important;
}

.btn-primary:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4) !important;
}

.output-container {
    border-radius: 12px !important;
    background: white !important;
    padding: 1.5rem !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05) !important;
    max-height: 600px !important;
    overflow-y: auto !important;
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.875rem;
}

.status-running {
    background: #e3f2fd;
    color: #1976d2;
}

.status-success {
    background: #e8f5e9;
    color: #2e7d32;
}

.status-error {
    background: #ffebee;
    color: #c62828;
}

.step-card {
    background: white;
    border-radius: 12px;
    padding: 1rem;
    margin: 0.5rem 0;
    box-shadow: 0 1px 4px rgba(0,0,0,0.1);
    border-left: 4px solid #667eea;
}

.chatbot {
    border-radius: 16px !important;
}
"""


@dataclass
class ActionResult:
	is_done: bool
	extracted_content: str | None
	error: str | None
	include_in_memory: bool


@dataclass
class AgentHistoryList:
	all_results: list[ActionResult]
	all_model_outputs: list[dict]


def format_history_output(history) -> str:
	"""Format the agent history in a beautiful, Gemini-like way"""
	output = []
	
	output.append("## 🤖 Agent Execution Summary\n")
	
	# Get basic stats
	steps = history.number_of_steps() if hasattr(history, 'number_of_steps') else 0
	is_done = history.is_done() if hasattr(history, 'is_done') else False
	has_errors = history.has_errors() if hasattr(history, 'has_errors') else False
	
	# Status badge
	if has_errors:
		status = '<span class="status-badge status-error">❌ Error</span>'
	elif is_done:
		status = '<span class="status-badge status-success">✅ Completed</span>'
	else:
		status = '<span class="status-badge status-running">🔄 In Progress</span>'
	
	output.append(f"**Status:** {status}\n")
	output.append(f"**Steps Executed:** {steps}\n")
	
	if hasattr(history, 'total_duration_seconds'):
		duration = history.total_duration_seconds()
		output.append(f"**Duration:** {duration:.2f}s\n")
	
	output.append("\n---\n")
	
	# Action history
	if hasattr(history, 'action_names'):
		actions = history.action_names()
		if actions:
			output.append("### 📋 Actions Taken\n")
			for i, action in enumerate(actions, 1):
				output.append(f"{i}. `{action}`\n")
			output.append("\n")
	
	# URLs visited
	if hasattr(history, 'urls'):
		urls = history.urls()
		if urls:
			output.append("### 🌐 URLs Visited\n")
			for url in set(urls):
				if url:
					output.append(f"- {url}\n")
			output.append("\n")
	
	# Final result
	if hasattr(history, 'final_result'):
		result = history.final_result()
		if result:
			output.append("### 🎯 Final Result\n")
			output.append(f"```\n{result}\n```\n")
	
	# Errors
	if has_errors and hasattr(history, 'errors'):
		errors = [e for e in history.errors() if e]
		if errors:
			output.append("### ⚠️ Errors Encountered\n")
			for error in errors:
				output.append(f"- {error}\n")
	
	return "\n".join(output)


async def run_browser_task(
	task: str,
	api_key: str,
	model_choice: str = 'ChatBrowserUse',
	headless: bool = True,
	max_steps: int = 100,
	use_vision: bool = True,
	progress=gr.Progress(),
) -> tuple[str, str]:
	"""Enhanced browser task runner with progress tracking"""
	if not task.strip():
		return "⚠️ Please provide a task description", ""
	
	# Set API key based on model
	if model_choice.startswith('ChatBrowserUse'):
		if api_key.strip():
			os.environ['BROWSER_USE_API_KEY'] = api_key
		elif 'BROWSER_USE_API_KEY' not in os.environ:
			# ChatBrowserUse can work without explicit API key if already set
			pass
	else:
		if not api_key.strip():
			return "⚠️ Please provide an API key", ""
		os.environ['OPENAI_API_KEY'] = api_key
	
	progress(0, desc="Initializing agent...")
	
	try:
		# Create browser with enhanced settings
		browser = Browser(
			headless=headless,
			window_size={'width': 1920, 'height': 1080},
		)
		
		# Select LLM based on choice
		if model_choice.startswith('ChatBrowserUse') and HAS_BROWSER_USE_LLM:
			llm = ChatBrowserUse()
		else:
			# Extract just the model name from the choice
			model_name = model_choice.split('(')[0].strip() if '(' in model_choice else model_choice
			llm = ChatOpenAI(model=model_name)
		
		progress(0.2, desc="Starting browser task...")
		
		# Create agent with enhanced settings
		agent = Agent(
			task=task,
			llm=llm,
			browser=browser,
			use_vision=use_vision,
		)
		
		progress(0.3, desc="Executing task...")
		
		# Run the agent
		history = await agent.run(max_steps=max_steps)
		
		progress(1.0, desc="Task completed!")
		
		# Format output
		formatted_output = format_history_output(history)
		
		# Create a status message
		status = "✅ Task completed successfully!" if history.is_done() else "⚠️ Task incomplete"
		
		return formatted_output, status
		
	except Exception as e:
		error_msg = f"### ❌ Error\n\n```\n{str(e)}\n```"
		return error_msg, f"❌ Error: {str(e)}"


def create_ui():
	"""Create a modern, Gemini-inspired UI"""
	with gr.Blocks(title='Browser Use AI Agent') as interface:
		
		# Header
		with gr.Row(elem_classes="header-container"):
			gr.HTML("""
				<div>
					<h1 class="header-title">✨ Browser Use AI Agent</h1>
					<p class="header-subtitle">Powered by Browser-Use | Automate anything on the web</p>
				</div>
			""")
		
		# Main content
		with gr.Row():
			# Left panel - Input controls
			with gr.Column(scale=1):
				gr.Markdown("### 🎯 Task Configuration")
				
				task = gr.Textbox(
					label="📝 What do you want me to do?",
					placeholder="Example: Go to Hacker News and find the top 3 posts with their scores",
					lines=4,
					elem_classes="input-box",
				)
				
				with gr.Accordion("⚙️ Advanced Settings", open=True):
					model_choice = gr.Radio(
						choices=[
							'ChatBrowserUse (Recommended - Fastest & Most Accurate)',
							'gpt-4.1-mini',
							'gpt-4.1',
							'gpt-5-mini',
							'o3-mini',
						],
						label='🤖 AI Model',
						value='ChatBrowserUse (Recommended - Fastest & Most Accurate)',
					)
					
					api_key = gr.Textbox(
						label='🔑 API Key',
						placeholder='Your API key (optional for ChatBrowserUse - get $10 free credits)',
						type='password',
						info="Get free credits at cloud.browser-use.com/new-api-key"
					)
					
					with gr.Row():
						max_steps = gr.Slider(
							minimum=10,
							maximum=200,
							value=100,
							step=10,
							label='📊 Max Steps',
							info="Maximum number of actions the agent can take"
						)
					
					with gr.Row():
						headless = gr.Checkbox(
							label='🖥️ Headless Mode',
							value=False,
							info="Run browser in background (faster but no visual)"
						)
						use_vision = gr.Checkbox(
							label='👁️ Enable Vision',
							value=True,
							info="Use AI vision to see the page (more accurate)"
						)
				
				submit_btn = gr.Button(
					'🚀 Run Agent',
					variant='primary',
					size='lg',
					elem_classes="btn-primary"
				)
				
				status_box = gr.Textbox(
					label="📡 Status",
					interactive=False,
					lines=2,
				)
				
				gr.Markdown("""
				---
				### 💡 Example Tasks
				- "Find the top product on Product Hunt today"
				- "Search for Python tutorials and summarize the first result"
				- "Go to Reddit and get the top posts from r/technology"
				- "Find the CEO of OpenAI on their website"
				- "Get the weather forecast for New York"
				""")
			
			# Right panel - Output
			with gr.Column(scale=2):
				gr.Markdown("### 📊 Agent Output")
				
				output = gr.Markdown(
					value="*Agent output will appear here...*",
					elem_classes="output-container",
					label="Output",
				)
				
				with gr.Accordion("🔍 Raw Output", open=False):
					raw_output = gr.Textbox(
						label="Debug Information",
						lines=10,
						interactive=False,
					)
		
		# Add examples
		gr.Examples(
			examples=[
				["Find the number 1 post on Hacker News", "", "ChatBrowserUse (Recommended - Fastest & Most Accurate)", False, 100, True],
				["Search for 'browser automation' on DuckDuckGo and get the first 3 results", "", "ChatBrowserUse (Recommended - Fastest & Most Accurate)", True, 50, True],
				["Go to github.com/browser-use/browser-use and tell me how many stars it has", "", "ChatBrowserUse (Recommended - Fastest & Most Accurate)", False, 30, True],
			],
			inputs=[task, api_key, model_choice, headless, max_steps, use_vision],
		)
		
		# Connect the submit button
		submit_btn.click(
			fn=lambda *args: asyncio.run(run_browser_task(*args)),
			inputs=[task, api_key, model_choice, headless, max_steps, use_vision],
			outputs=[output, status_box],
		)
		
		# Footer
		gr.HTML("""
		<div style="text-align: center; padding: 2rem; color: #666; font-size: 0.9rem;">
			<p>Built with ❤️ using <a href="https://github.com/browser-use/browser-use" target="_blank" style="color: #667eea; text-decoration: none;">Browser-Use</a></p>
			<p>Star us on <a href="https://github.com/browser-use/browser-use" target="_blank" style="color: #667eea; text-decoration: none;">GitHub</a> ⭐</p>
		</div>
		""")
	
	return interface


if __name__ == '__main__':
	demo = create_ui()
	demo.launch(
		server_name="0.0.0.0",
		server_port=7860,
		share=False,
		show_error=True,
		theme=gr.themes.Soft(),
		css=CUSTOM_CSS,
	)
