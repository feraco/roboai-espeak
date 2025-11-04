# Badge Reader Plugin - Lightweight OCR Version

## Overview

The `BadgeReaderOCR` plugin uses OCR (pytesseract) to detect and read ID badges/name tags. It's designed to be **memory-efficient** for Jetson deployment.

## Features

- ✅ **Lightweight** - Uses only OCR, no LLM/VLM needed (~50MB memory)
- ✅ **Automatic name detection** - Extracts first and last names from badges
- ✅ **Smart filtering** - Ignores common badge text like "VISITOR", "ID", "EMPLOYEE"
- ✅ **Cooldown system** - Prevents greeting same person multiple times
- ✅ **Configurable preprocessing** - Low/medium/high quality settings

## Memory Usage

- **OCR only**: ~50MB
- **VLM version** (badge_reader_vlm.py): ~2-4GB depending on model

For Jetson: Use the OCR version!

## Installation

```bash
# Install pytesseract (already done)
uv add pytesseract

# On Ubuntu/Jetson, ensure tesseract is installed
sudo apt install tesseract-ocr

# On macOS
brew install tesseract
```

## Usage

### 1. Test Badge Reader Standalone

```bash
uv run src/run.py badge_reader_test
```

Hold up a badge or paper with a name (e.g., "John Smith") in front of the camera.

### 2. Add to Astra Receptionist

Add this input to `config/astra_vein_receptionist.json5`:

```json5
{
  type: "BadgeReaderOCR",
  config: {
    camera_index: 0,
    poll_interval: 5.0,  // Check every 5 seconds
    greeting_cooldown: 60.0,  // Don't re-greet within 60 seconds
    preprocess_quality: "medium",  // low, medium, or high
    descriptor: "Badge Reader"
  }
}
```

### 3. Update System Prompt

Make sure your system prompt knows about badge detection:

```
When you detect someone's name from their badge, greet them warmly by name 
and introduce yourself as the Astra Vein receptionist.
```

## Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `camera_index` | 0 | Camera device index |
| `poll_interval` | 5.0 | Seconds between badge checks |
| `greeting_cooldown` | 60.0 | Seconds before re-greeting same person |
| `preprocess_quality` | "medium" | Image preprocessing: low/medium/high |
| `confidence_threshold` | 0.5 | OCR confidence threshold (0-1) |
| `buffer_size` | 5 | Number of messages to keep in buffer |

## Preprocessing Quality

- **low**: Fast, basic thresholding (~100ms per frame)
- **medium**: Balanced, adaptive threshold + cleanup (~200ms per frame)
- **high**: Best accuracy, CLAHE + bilateral filter (~500ms per frame)

For Jetson: Use **medium** or **low**

## How It Works

1. **Capture**: Grabs frame from camera every `poll_interval` seconds
2. **Preprocess**: Converts to grayscale, enhances contrast, applies thresholding
3. **OCR**: Extracts text using pytesseract
4. **Parse**: Looks for "First Last" name patterns
5. **Filter**: Removes common badge words (VISITOR, ID, etc.)
6. **Output**: Sends message to LLM when new person detected

## Expected Input Format

Works best with:
- ✅ Printed name badges with clear text
- ✅ "FIRST LAST" or "First Last" format
- ✅ High contrast (dark text on light background)
- ✅ Badge held relatively still for 1-2 seconds

## Example Output

When badge is detected:
```
INPUT: Badge Reader - OCR System
// START
I see John Smith is here. Their badge shows the name John Smith.
// END
```

This triggers the LLM to respond:
```json
{
  "speak": {
    "sentence": "Hello John Smith! Welcome to Astra Vein Treatment Center.",
    "language": "en"
  }
}
```

## Troubleshooting

### No names detected
- Ensure badge has clear, printed text (not handwritten)
- Check camera focus - badge should be 1-2 feet from camera
- Try `preprocess_quality: "high"` for better accuracy
- Hold badge steady for 2-3 seconds

### Wrong names detected
- Common badge text might be misread as names
- Add problematic words to `_ignore_words` in the plugin
- Increase `confidence_threshold` to 0.7

### Too much memory on Jetson
- Use `preprocess_quality: "low"`
- Increase `poll_interval` to 10.0 or higher
- Make sure you're using BadgeReaderOCR, not BadgeReaderVLM

## Testing Tips

Create a test badge:
1. Print "JOHN SMITH" on paper in large, bold text
2. Hold it in front of camera
3. Check logs for "✅ Badge detected: John Smith"

Or use your test script:
```bash
uv run python test_badge_detection.py
```

## Performance

On Jetson Nano (4GB):
- Memory: ~50MB
- Processing time: 200-500ms per frame (depending on quality)
- No impact on LLM performance

On MacBook Pro:
- Memory: ~30MB  
- Processing time: 100-300ms per frame

## Integration Example

Full Astra config with badge reader:

```json5
{
  agent_inputs: [
    {
      type: "BadgeReaderOCR",
      config: {
        camera_index: 0,
        poll_interval: 5.0,
        greeting_cooldown: 60.0,
        preprocess_quality: "medium",
        descriptor: "Badge Reader"
      }
    },
    {
      type: "LocalASRInput",
      config: {
        engine: "faster-whisper",
        model_size: "base",
        // ... other ASR config
      }
    }
  ]
}
```

## Files

- `src/inputs/plugins/badge_reader_ocr.py` - Lightweight OCR version (recommended)
- `src/inputs/plugins/badge_reader_vlm.py` - VLM version (higher accuracy, more memory)
- `config/badge_reader_test.json5` - Test configuration
- `test_badge_detection.py` - Standalone test script
