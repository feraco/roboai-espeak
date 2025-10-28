# Lex Channel Chief Agent - Quick Start

## Overview

**Lex** is an AI sales agent for Lexful, designed to engage with MSPs and channel partners at events and demos. Lex uses external knowledge files to maintain detailed product information without bloating the configuration.

## Prerequisites

- Ollama running with `llama3.1:8b` model
- Piper TTS installed with `en_US-ryan-medium` voice
- Microphone and speakers/audio output configured

## Quick Start

### 1. Start Ollama (if not running)

```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# If not, start it:
ollama serve

# In another terminal, ensure you have the model:
ollama pull llama3.1:8b
```

### 2. Run Lex Agent

```bash
cd /Users/wwhs-research/Downloads/roboai-feature-multiple-agent-configurations
uv run src/run.py lex_channel_chief
```

### 3. Test Conversation

Try asking Lex:
- "Tell me about Lexful"
- "What problems does it solve for law firms?"
- "How much does it cost?"
- "What if they already have a receptionist?"
- "Can you give me an ROI example?"

## Configuration Details

### Agent Config
- **File:** `config/lex_channel_chief.json5`
- **Voice:** Ryan (male, professional)
- **LLM:** Ollama llama3.1:8b
- **Knowledge:** External file at `docs/lexful_knowledge.md`

### Knowledge Base
- **File:** `docs/lexful_knowledge.md` (~18KB)
- **Sections:**
  - Product overview
  - Features & benefits
  - Target customers
  - Common objections & responses
  - Sample dialogues
  - Competitive positioning
  - Pricing & packages
  - FAQs
  - Brand voice guidelines

### Response Style
- **Concise:** 2-3 sentences max unless asked for details
- **Consultative:** Discovery-first approach
- **ROI-Focused:** Uses numbers and examples
- **Professional:** Confident but not pushy

## Testing Tips

### Test Different Scenarios

**Discovery Questions:**
- "What law firms do you work with?"
- "How many leads do they get per month?"
- "What's their average case value?"

**Feature Questions:**
- "How does the AI work?"
- "What integrations do you support?"
- "Can it handle Spanish speakers?"

**Objection Handling:**
- "We already have staff for this"
- "Sounds expensive"
- "Our cases are too complex for AI"
- "What about data security?"

**Closing:**
- "Can I see a demo?"
- "What's the pricing?"
- "How do I get started?"

## Customization

### Change Voice

Edit `config/lex_channel_chief.json5`:

```json5
agent_actions: [
  {
    name: "speak",
    config: {
      model_en: "en_US-ryan-medium",  // Change to different voice
      length_scale: 0.90,              // Adjust speed (lower = faster)
      emotion: "confident"             // Adjust tone
    }
  }
]
```

Available male voices in `piper_voices/`:
- `en_US-ryan-medium` (current - professional)
- `en_US-ryan-high` (higher pitch)

### Update Knowledge

Edit `docs/lexful_knowledge.md` directly. Changes take effect on next agent restart.

**Common updates:**
- Pricing changes
- New features
- Updated objection responses
- New sample dialogues
- Competitive updates

### Adjust Response Length

Edit `config/lex_channel_chief.json5`:

```json5
cortex_llm: {
  config: {
    max_tokens: 300,  // Increase for longer responses
    temperature: 0.7   // Adjust creativity (0.0-1.0)
  }
}
```

## Architecture

```
┌─────────────────────┐
│  User speaks to Lex │
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   LocalASRInput     │ (Whisper: speech → text)
│   VLMOllamaVision   │ (LLaVA: camera → description)
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│       Fuser         │ (Combines inputs + loads knowledge)
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│    OllamaLLM        │ (llama3.1:8b generates response)
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│    Piper TTS        │ (Text → speech with Ryan voice)
└──────────┬──────────┘
           │
           ↓
┌─────────────────────┐
│   Lex responds      │
└─────────────────────┘
```

## Monitoring

### Check Logs

Look for these indicators:

**✅ Good:**
```
INFO:fuser:Loaded external knowledge from: docs/lexful_knowledge.md
INFO:fuser:Successfully loaded knowledge file: ... (18123 chars)
=== INPUT STATUS ===
Voice: Yes | Vision: No | Language: en
```

**⚠️ Issues:**
```
WARNING:fuser:Knowledge file not found: docs/lexful_knowledge.md
ERROR:ollama:Connection refused to http://localhost:11434
```

### Performance Metrics

Typical response times:
- ASR (speech → text): 1-2 seconds
- LLM (generate response): 2-4 seconds
- TTS (text → speech): 1-2 seconds
- **Total:** ~5-8 seconds per interaction

## Troubleshooting

### "No module named 'actions'"

Run with `uv run` prefix:
```bash
uv run src/run.py lex_channel_chief
```

### "Connection refused to Ollama"

Start Ollama:
```bash
ollama serve
# Or: brew services start ollama
```

### "Knowledge file not found"

Check file exists:
```bash
ls docs/lexful_knowledge.md
```

### "Voice model not found"

Verify Piper voice exists:
```bash
ls piper_voices/en_US-ryan-medium*
```

Download if missing:
```bash
# Download from Piper releases
# Place .onnx and .onnx.json files in piper_voices/
```

### Agent not responding

Check:
1. Microphone input (test_microphone.py)
2. Ollama running and responsive
3. Piper TTS working (test_piper.py)

## Next Steps

### Advanced Features

1. **Add Vision Analysis**
   - Enable camera to see booth visitors
   - Comment on their body language
   - Personalize greetings

2. **Multi-Language Support**
   - Add Spanish for LATAM markets
   - Detect language automatically
   - Use appropriate TTS voice

3. **CRM Integration**
   - Log conversations to CRM
   - Track lead quality
   - Follow-up automation

4. **RAG Enhancement**
   - Index knowledge base with embeddings
   - Retrieve most relevant info per query
   - Handle extremely large knowledge bases

### Extend Knowledge Base

Add new sections to `docs/lexful_knowledge.md`:
- Case studies and success stories
- Industry benchmarks and data
- Integration guides
- Competitive comparison matrix
- Regional pricing variations

## Resources

- **Config:** `config/lex_channel_chief.json5`
- **Knowledge:** `docs/lexful_knowledge.md`
- **Guide:** `docs/EXTERNAL_KNOWLEDGE_GUIDE.md`
- **Test:** `test_knowledge_injection.py`

## Support

For questions or issues:
1. Check logs for error messages
2. Review configuration file
3. Test individual components (ASR, LLM, TTS)
4. Consult project documentation

---

**Created:** October 28, 2025  
**Agent Version:** 1.0  
**Knowledge Version:** 1.0
