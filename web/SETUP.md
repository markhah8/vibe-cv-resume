# Setup Instructions

## 1. Install Dependencies

```bash
cd web
pip install -r requirements.txt
```

## 2. Configure AI API

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:

### Option A: Using OpenAI (GPT-4)

```env
OPENAI_API_KEY=sk-proj-your-actual-key-here
AI_PROVIDER=openai
AI_MODEL=gpt-4-turbo
```

Get API key: https://platform.openai.com/api-keys

### Option B: Using Anthropic (Claude)

```env
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here
AI_PROVIDER=anthropic
AI_MODEL=claude-3-5-sonnet-20241022
```

Get API key: https://console.anthropic.com/

## 3. Start Server

```bash
python app.py
```

Open: http://localhost:5000

## Features

### Automatic AI Optimization Flow:

1. **User fills form** → Company name, role, job description
2. **Click "Create & Auto-Optimize"**
3. **System automatically:**
   - Creates variant folder
   - Calls AI API to optimize CV
   - Generates main.tex
   - Compiles PDF with Docker
   - Shows download button
4. **User downloads PDF** → Ready to apply!

### Progress Indicator:

- ✓ Creating variant folder...
- ✓ AI optimizing CV...
- ✓ Compiling PDF...

### No manual commands needed!

Everything runs automatically in the background.

## Troubleshooting

### No AI API Key

If you don't have API key, the system will still:
- Create variant folder
- Save job description
- But won't auto-optimize (you'll need to use AI agent manually)

### Docker Not Running

Make sure Docker Desktop is running:
```bash
open -a Docker
```

### AI Timeout

GPT-4 usually takes 10-30 seconds. If timeout, check:
- API key is valid
- API has credits
- Network connection
