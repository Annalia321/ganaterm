# Ganaterm - Lightweight Terminal AI Assistant

Ganaterm is a lightweight AI assistant for the terminal that allows you to chat with LLMs, execute commands, and generate and write files when you're bored.

## Key Features

- **Model API Support**: Currently supports OpenAI, DeepSeek, and xAI large language models
- **Command Execution**: Can detect commands in LLM responses and execute them with (y/n) confirmation (with security checks)
- **Lightweight Startup**: Quick one-click launch
- **Typing Effect**: Supports typewriter effect when displaying model responses to enhance the interactive experience (optional)
- **Conversation History**: Supports historical dialogue memory

## Installation Guide

## Installation

1. Clone the repository
```bash
git clone https://github.com/Annalia321/ganaterm.git
cd ganaterm
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

3. Configure environment
```bash
mkdir -p ~/.config/ganaterm
cp .env.example ~/.config/ganaterm/.env
# Edit .env file to add your API keys
```

4. Set up aliases
```bash
cp aliases.sh ~/.config/ganaterm/
echo "source ~/.config/ganaterm/aliases.sh" >> ~/.bashrc  # or ~/.zshrc
```

## Usage

### Quick Commands

- `g [question]` - Use OpenAI model
- `d [question]` - Use DeepSeek model 
- `x [question]` - Use xAI (Grok) model

For example:
```bash
g How to find large files in Linux?
```

### Interactive Mode

If you don't provide a question parameter, you'll enter interactive mode:

```bash
g
```

### Command Execution

When AI suggests a command, you'll be prompted to execute it:
