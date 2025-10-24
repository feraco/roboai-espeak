# G1 Arm Integration Guide for Astra Vein Receptionist

## What Was Added

The Astra Vein receptionist now supports **G1 humanoid arm gestures** to create a more engaging and human-like interaction experience.

## Available Arm Movements

| Gesture | When to Use | Example Context |
|---------|-------------|-----------------|
| **high wave** | Greeting new patients, saying goodbye | "Welcome to Astra Vein!" |
| **heart** | Showing care, gratitude, appreciation | "Thank you for choosing us!" |
| **high five** | Celebrating good news or decisions | "Great! You'll love Dr. Bolotin!" |
| **shake hand** | Professional greeting or agreement | Formal introductions |
| **clap** | Celebrating patient progress | "Wonderful choice!" |
| **idle** | Neutral resting position | Most standard responses |

## Configuration Added

### 1. Ethernet Interface (Required!)
```json5
{
  name: "astra_vein_receptionist",
  unitree_ethernet: "en0",  // Ethernet interface for G1 connection
  // ...rest of config
}
```

**Important:** The G1 robot communicates over ethernet. You MUST specify the correct network interface:
- **macOS**: Usually `"en0"` or `"en1"`
- **Linux/Ubuntu (G1)**: Usually `"eno1"` or `"eth0"`

To find your ethernet interface:
```bash
# On macOS
ifconfig | grep -E "^en[0-9]"

# On Linux/G1
ip addr show | grep -E "^[0-9]+: (en|eth)"
```

### 2. Arm Action
```json5
{
  "name": "arm_g1",
  "llm_label": "arm movement",
  "type": "Action",
  "connector": "unitree_sdk",
  "config": {}
}
```

## How the LLM Uses Gestures

The agent now responds with **both speech and gestures**:

```json
Actions:
- arm movement: {'action': 'high wave'}
- speak: {'sentence': 'Welcome to Astra Vein Treatment Center!'}
```

## Design Philosophy

### ✅ Use Gestures For:
- **First greetings** - Wave to welcome patients warmly
- **Gratitude** - Heart gesture when thanking patients
- **Celebration** - Clap when patient books appointment
- **Farewell** - Wave when saying goodbye

### ❌ Don't Overuse:
- Most responses should be **speech-only**
- Gestures should **enhance**, not distract
- Use gestures **sparingly and purposefully**
- Avoid gestures for routine information delivery

## Example Interactions

### Example 1: First Greeting
```
Patient walks in (vision detects person)

Agent response:
- arm movement: {'action': 'high wave'}
- speak: {'sentence': 'Good morning! Welcome to Astra Vein Treatment Center. I'm Iris, how can I help you today?'}
```

### Example 2: Patient Books Appointment
```
Patient: "I'd like to schedule an appointment"

Agent response:
- arm movement: {'action': 'clap'}
- speak: {'sentence': 'Wonderful! You can call 347-934-9068, or our front desk can help you right now!'}
```

### Example 3: Thanking Patient
```
Patient: "Thanks for your help!"

Agent response:
- arm movement: {'action': 'heart'}
- speak: {'sentence': 'You're very welcome! We're so glad you chose Astra Vein.'}
```

### Example 4: Standard Information (No Gesture)
```
Patient: "What are your hours?"

Agent response:
- speak: {'sentence': 'We're open Monday through Friday, 9 AM to 6 PM. Closed on weekends.'}
```

## Testing on G1

### 1. Update Config on G1
```bash
cd ~/roboai/roboai-espeak
git pull
```

### 2. Run Agent
```bash
uv run src/run.py astra_vein_receptionist
```

### 3. Test Gesture Triggers
- **Say "Hello"** - Should wave and greet
- **Ask "What are your hours?"** - Should respond without gesture
- **Say "Thanks"** - Should show heart gesture
- **Say "I'll book an appointment"** - Should clap

### 4. Monitor Logs
Watch for:
```
2025-10-24 - INFO - Executing arm_g1 action: high wave
2025-10-24 - INFO - Executing speak action: Welcome to Astra Vein...
```

## Troubleshooting

### Gestures Not Working

### Check Ethernet Interface

**Find your interface:**
```bash
# On G1 (Linux)
ip addr show

# Look for the interface connected to robot (usually eno1 or eth0)
# You should see an IP like 192.168.123.x
```

**Common interfaces:**
- `eno1` - Most common on G1/Linux
- `eth0` - Older Linux systems
- `en0` - macOS (for testing)

**Update config if needed:**
```json5
unitree_ethernet: "eno1"  // Change to match your system
```

**Check connector:**
```bash
# Verify unitree_sdk is available
python3 -c "from actions.arm_g1.connector.unitree_sdk import UnitreeSDK"
```

**Check robot connection:**
- Ensure ethernet cable is connected to G1
- Verify network connection (should see 192.168.123.x IP)
- Check if robot is powered on and in proper mode

**Mock mode for testing:**
If you want to test without actual arm movement:
```json5
{
  "name": "arm_g1",
  "llm_label": "arm movement",
  "type": "Action",
  "connector": "unitree_sdk",
  "config": {
    "mock": true  // Add this for testing
  }
}
```

### Too Many Gestures

If the agent uses gestures too frequently:
- Update system prompt to emphasize "use sparingly"
- Increase LLM temperature for more varied responses
- Add examples of responses WITHOUT gestures

### Wrong Gestures

If gestures don't match context:
- Add more examples to `system_prompt_examples`
- Clarify gesture meanings in `=== ARM MOVEMENTS ===` section
- Test with different patient questions

## Best Practices

1. **Start Simple** - Begin with just wave (greeting) and heart (thanks)
2. **Observe Patient Reactions** - See which gestures feel natural
3. **Adjust Based on Feedback** - Modify examples if gestures feel off
4. **Keep It Professional** - Medical setting requires appropriate gestures
5. **Test Timing** - Ensure gesture completes before/during speech

## Advanced Customization

### Add New Gestures

If you want to add custom gestures, edit:
```python
# src/actions/arm_g1/interface.py
class ArmAction(str, Enum):
    IDLE = "idle"
    LEFT_KISS = "left kiss"
    RIGHT_KISS = "right kiss"
    CLAP = "clap"
    HIGH_FIVE = "high five"
    SHAKE_HAND = "shake hand"
    HEART = "heart"
    HIGH_WAVE = "high wave"
    # Add your custom gesture here
```

Then update the config examples to teach the LLM when to use it.

### Gesture Sequences

For more complex interactions, you could combine gestures:
```json
Actions:
- arm movement: {'action': 'high wave'}
- speak: {'sentence': 'Welcome!'}
- arm movement: {'action': 'heart'}
- speak: {'sentence': 'We're so glad you're here!'}
```

But keep it simple for now - single gesture per interaction works best.

## Summary

✅ **Added:** G1 arm gesture support to Astra Vein receptionist  
✅ **Gestures:** Wave (greeting), Heart (gratitude), Clap (celebration)  
✅ **Philosophy:** Enhance communication, don't distract  
✅ **Testing:** Pull latest config and run on G1  

The receptionist is now more engaging and human-like while maintaining professionalism! 🤖💙
