# Badge Reader Plugin - Quick Setup

## ✅ What Was Created

1. **`src/inputs/plugins/badge_reader_ocr.py`** - Lightweight OCR-based badge reader (~ 50MB memory)
2. **`src/inputs/plugins/badge_reader_vlm.py`** - VLM-based badge reader (2-4GB memory, higher accuracy)
3. **`config/badge_reader_test.json5`** - Test configuration
4. **`documentation/guides/BADGE_READER_GUIDE.md`** - Complete documentation
5. **Fixed bug in `local_asr.py`** - UnboundLocalError on line 203

## 🚀 Usage

### Quick Test

Hold up a badge or paper with a name (e.g., "JOHN SMITH") and run:

```bash
uv run src/run.py badge_reader_test
```

### Add to Astra Receptionist

Edit `config/astra_vein_receptionist.json5` and add this to `agent_inputs`:

```json5
{
  type: "BadgeReaderOCR",
  config: {
    camera_index: 0,
    poll_interval: 5.0,  // Check every 5 seconds
    greeting_cooldown: 60.0,  // Don't re-greet within 60 seconds
    preprocess_quality: "medium",  // low/medium/high - use low on Jetson
    descriptor: "Badge Reader"
  }
}
```

Then update `system_prompt_base` to mention badge detection:

```
When you detect someone's name from their badge (you'll receive input like "I see John Smith is here"), 
greet them warmly by name: "Hello John Smith! Welcome to Astra Vein Treatment Center..."
```

## 🎯 How It Works

1. **Captures frame** from camera every 5 seconds
2. **Preprocesses** image (grayscale, contrast enhancement, thresholding)
3. **Extracts text** using pytesseract OCR
4. **Parses names** using regex patterns for "First Last" format
5. **Filters out** common badge words (VISITOR, ID, EMPLOYEE, etc.)
6. **Sends to LLM**: "I see John Smith is here. Their badge shows the name John Smith."
7. **LLM responds** with personalized greeting

## 💾 Memory Usage

- **OCR version** (`BadgeReaderOCR`): ~50MB ✅ **Use this for Jetson!**
- **VLM version** (`BadgeReaderVLM`): 2-4GB (more accurate, but too heavy for Jetson)

## ⚙️ Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `camera_index` | 0 | Camera device (0 = default camera) |
| `poll_interval` | 5.0 | Seconds between badge checks |
| `greeting_cooldown` | 60.0 | Seconds before re-greeting same person |
| `preprocess_quality` | "medium" | **"low"** for Jetson, "medium" for Mac/desktop, "high" for best accuracy |

## 📝 Testing Tips

**Create test badge:**
1. Print "JOHN SMITH" in large bold text on paper
2. Hold 1-2 feet from camera
3. Keep steady for 2-3 seconds
4. Watch logs for: `✅ Badge detected: John Smith`

**Check camera:**
```bash
uv run python test_badge_detection.py
```

## 🐛 Troubleshooting

**No names detected:**
- Badge text must be printed (not handwritten)
- Hold badge 1-2 feet from camera
- Keep badge still for 2-3 seconds
- Try `preprocess_quality: "high"` for better accuracy

**Wrong names detected:**
- Increase `confidence_threshold` to 0.7
- Add problematic words to `_ignore_words` in plugin

**Too slow on Jetson:**
- Use `preprocess_quality: "low"`
- Increase `poll_interval` to 10.0 seconds

## 🔧 Files Modified

- `src/inputs/plugins/badge_reader_ocr.py` - New lightweight OCR plugin ✨
- `src/inputs/plugins/badge_reader_vlm.py` - New VLM plugin (optional)
- `config/badge_reader_test.json5` - Test configuration
- `src/inputs/plugins/local_asr.py` - Fixed UnboundLocalError bug
- `src/run.py` - Added traceback to error logging
- `documentation/guides/BADGE_READER_GUIDE.md` - Full documentation

## 📖 Full Documentation

See: `documentation/guides/BADGE_READER_GUIDE.md`
