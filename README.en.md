# Ganaterm - Lightweight Terminal AI Assistant

Ganaterm is a lightweight AI assistant for the terminal that allows you to chat with LLMs, execute commands, and generate and write files when you're bored.

## Quick Installation

Ganaterm provides a simple installation script to quickly set up everything:

```bash
# Give execution permission to the install script
chmod +x install.sh

# Run the installation script
./install.sh

# Activate the configuration (follow the script's prompt)
source ~/.bashrc  # or ~/.zshrc
```

> **Important Note**: After installation, you need to edit the `~/.config/ganaterm/.env` file to add your API keys!
> Ganaterm will not work properly without valid API keys.

## Key Features

- **Model API Support**: Currently supports OpenAI, DeepSeek, and xAI large language models
- **Command Execution**: Can detect commands in LLM responses and execute them with (y/n) confirmation (with security checks)
- **Lightweight Startup**: Quick one-click launch
- **Typing Effect**: Supports typewriter effect when displaying model responses to enhance the interactive experience (optional)
- **Conversation History**: Supports historical dialogue memory

## Installation Guide

### Automatic Installation (Recommended)

Use the provided installation script to automatically complete all setup:

```bash
chmod +x install.sh
./install.sh
source ~/.bashrc  # or ~/.zshrc
```

After completion, edit the `~/.config/ganaterm/.env` file to add your API keys.

### Manual Installation

If you prefer to install manually, follow these steps:

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
# Edit the .env file to add your API keys
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
