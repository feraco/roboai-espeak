# Demo Conversation Generator

Generate pre-recorded demo conversations with the Astra Vein Receptionist agent for website demos.

## What It Does

This script simulates realistic patient conversations and generates audio responses in multiple languages:
- **English** conversations with Amy's voice
- **Spanish** conversations with Davefx's voice  
- **Russian** conversations with Dmitri's voice

Perfect for creating website demos without needing live agent interaction!

## Prerequisites

- Ollama running with `llama3.1:8b` model
- Piper TTS voice models installed (Amy, Davefx, Dmitri)
- UV package manager

## Usage

```bash
# Run the generator
uv run generate_demo_conversations.py
```

The script will:
1. Process all preset questions (11 total conversations)
2. Generate natural responses via LLM
3. Synthesize speech in the appropriate language
4. Save WAV files to `demo_conversations/` directory
5. Create a `manifest.json` with metadata

## Output Structure

```
demo_conversations/
├── manifest.json                          # Metadata for all conversations
├── en_01_welcome_response.wav            # English responses
├── en_02_office_hours_response.wav
├── en_03_location_response.wav
├── en_04_varicose_veins_response.wav
├── en_05_appointment_response.wav
├── en_06_doctor_response.wav
├── es_01_bienvenida_response.wav         # Spanish responses
├── es_02_horario_response.wav
├── es_03_ubicacion_response.wav
├── ru_01_privet_response.wav             # Russian responses
└── ru_02_raspisanie_response.wav
```

## Demo Conversations Included

### English (6 conversations)
1. Welcome & services overview
2. Office hours inquiry
3. Location information (Brooklyn focus)
4. Varicose vein treatment
5. Appointment scheduling
6. Doctor information

### Spanish (3 conversations)
1. Bienvenida y servicios
2. Horario de oficina
3. Ubicación

### Russian (2 conversations)
1. Приветствие и услуги
2. Часы работы

## Customizing Conversations

Edit the `DEMO_CONVERSATIONS` list in the script to add more questions:

```python
{
    "id": "07_insurance",
    "question": "Do you accept insurance?",
    "context": "Patient asking about payment"
}
```

## Using Demo Files on Website

The generated WAV files can be:
- Embedded directly in HTML with `<audio>` tags
- Played on button clicks for interactive demos
- Combined with text transcripts for accessibility
- Used in video presentations

Example HTML:
```html
<div class="demo-conversation">
  <p class="question">Q: What are your office hours?</p>
  <audio controls>
    <source src="demo_conversations/en_02_office_hours_response.wav" type="audio/wav">
  </audio>
  <p class="response">Response: [Transcript from manifest.json]</p>
</div>
```

## Manifest File

The `manifest.json` contains:
- Timestamp of generation
- Full question and response text
- Language codes
- File paths
- Conversation IDs

Perfect for programmatically building demo interfaces!

## Troubleshooting

**Ollama not responding:**
```bash
# Check if Ollama is running
curl http://localhost:11434

# Start Ollama if needed
ollama serve
```

**Voice models not found:**
- Ensure voice models are in `piper_voices/` directory
- Check that files are 60MB ONNX files (not corrupted)

**Empty responses:**
- Check LLM logs for errors
- Try increasing timeout in script
- Verify Llama 3.1 model is downloaded

## Performance

- Generates ~11 conversations in 2-3 minutes
- Each response: 5-10 seconds (LLM + TTS)
- Output files: ~50-200KB per WAV file

Enjoy your multi-language AI receptionist demos! 🎤🌍
