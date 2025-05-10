# Ganaterm - Lightweight Terminal AI Assistant

[简体中文](README.md) | English

Ganaterm is a lightweight AI assistant for terminal use, enabling you to chat with LLMs, execute commands, and generate files when feeling bored.

## Key Features

* **Model API Support:** Currently supports OpenAI, DeepSeek, and xAI language models.
* **Command Execution:** Detects commands in LLM responses and prompts for (y/n) execution (with safety checks).
* **Lightweight Launch:** Quick one-click startup.
* **Typing Effect:** Supports typewriter effect for displaying model responses, enhancing interactive experience (optional).
* **Conversation Memory:** Supports historical conversation memory.

---

## Installation Guide

### Installation

1. Clone the repository:

```bash
git clone https://github.com/Annalia321/ganaterm.git
cd ganaterm
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Configure environment:

```bash
mkdir -p ~/.config/ganaterm
cp .env.example ~/.config/ganaterm/.env
# Edit the .env file and add your API keys
```

4. Set up aliases:

```bash
cp aliases.sh ~/.config/ganaterm/
echo "source ~/.config/ganaterm/aliases.sh" >> ~/.bashrc  # or ~/.zshrc
```

---

## Usage

### Quick Commands

* `g [question]` - Uses OpenAI model
* `d [question]` - Uses DeepSeek model
* `x [question]` - Uses xAI (Grok) model

Example:

```bash
g How to find large files in Linux?
```

### Command Execution

When AI suggests a command, it will prompt for execution:

```
! Execute: `find . -type f -size +100M` ?(y/n)
```

### Code Generation

When AI generates a code block, it will prompt for saving the file:

```
! Detected Python code block. Save to main.py? (y/n/e/rnm)
- y: Save
- n: Discard
- e: Show content
- rnm: Rename
```

---

## Environment Variables

The `.env` file supports the following configurations:

* `OPENAI_API_KEY` - OpenAI API Key
* `DEEPSEEK_API_KEY` - DeepSeek API Key
* `XAI_API_KEY` - xAI API Key
* `HTTP_PROXY/HTTPS_PROXY` - Proxy settings
* `USE_TYPEWRITER` - Enable/disable typewriter effect
* `TYPING_SPEED_WPM` - Set typing speed

---

## License

---

## Contribution

Feel free to submit Pull Requests or Issues to improve Ganaterm!
