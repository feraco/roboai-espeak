# External Knowledge System - Implementation Guide

## Overview

The external knowledge system allows you to keep your agent configs clean and maintainable by storing large amounts of reference information in separate markdown files. The Fuser automatically loads and injects this content into the LLM's system prompt at runtime.

## Benefits

✅ **Clean Configs**: Keep JSON5 configs concise and readable  
✅ **Easy Maintenance**: Update knowledge without editing configs  
✅ **Version Control**: Track knowledge changes separately from code  
✅ **Reusability**: Share knowledge files across multiple agents  
✅ **No Token Bloat**: Knowledge is loaded once at startup, not repeated in chat history

## How It Works

### 1. Architecture

```
┌─────────────────┐
│  Agent Config   │  (lex_channel_chief.json5)
│  knowledge_file │  → "docs/lexful_knowledge.md"
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│     Fuser       │  Loads knowledge file at startup
│ _load_knowledge │  Injects into system context
└────────┬────────┘
         │
         ↓
┌─────────────────┐
│   LLM Prompt    │  BASIC CONTEXT + KNOWLEDGE BASE + LAWS + EXAMPLES
│  (Full Context) │  Sent to LLM with every request
└─────────────────┘
```

### 2. File Structure

```
project_root/
├── config/
│   └── lex_channel_chief.json5    # Agent config (concise)
├── docs/
│   └── lexful_knowledge.md         # External knowledge (detailed)
└── src/
    └── fuser/__init__.py            # Loads and injects knowledge
```

## Usage Guide

### Step 1: Create Knowledge File

Create a markdown file in `docs/` with your knowledge content:

**Example: `docs/lexful_knowledge.md`**

```markdown
# Lexful Channel Chief Knowledge Base

## Product Overview
Lexful is an AI-powered legal intake management platform...

## Common Objections & Responses
### "We already have a receptionist"
Response: "That's great! Lexful doesn't replace..."

## Pricing & Packages
### Starter Plan: $1,500/month
- Up to 100 qualified leads/month
...
```

### Step 2: Reference in Agent Config

Add the `knowledge_file` field to your config:

**Example: `config/lex_channel_chief.json5`**

```json5
{
  name: "lex_channel_chief",
  api_key: null,
  hertz: 5,
  
  // External knowledge file (relative to project root)
  knowledge_file: "docs/lexful_knowledge.md",
  
  system_prompt_base: "You are Lex, the Channel Chief AI for Lexful...",
  // Keep this concise - details go in knowledge file!
  
  // ... rest of config
}
```

### Step 3: Reference Knowledge in Prompts

Guide the LLM to use the knowledge base in your system prompts:

```json5
system_prompt_base: "You are Lex...

Your knowledge:
- You have access to comprehensive product information in your KNOWLEDGE BASE section
- Reference specific details from the knowledge base when answering questions
- If you don't know something, acknowledge it honestly

Key areas in your knowledge base:
- Product overview and features
- Pricing and packages
- Common objections and responses
- Sample dialogues
- Competitive positioning
- FAQs",
```

### Step 4: Run Your Agent

```bash
# The knowledge file is automatically loaded
uv run src/run.py lex_channel_chief
```

## Configuration Options

### knowledge_file Field

```json5
{
  // Relative path (from project root)
  knowledge_file: "docs/lexful_knowledge.md",
  
  // Or absolute path
  knowledge_file: "/path/to/knowledge.md",
  
  // Or null/omit to disable
  knowledge_file: null,
}
```

The Fuser will:
1. Try the path as absolute first
2. If not absolute, resolve relative to project root
3. Log success/failure of loading
4. Continue without knowledge if file not found (won't crash)

## Testing

### Test Knowledge Injection

```bash
uv run python test_knowledge_injection.py
```

This script verifies:
- ✅ Config loads with knowledge_file field
- ✅ Fuser loads external file
- ✅ Knowledge appears in system context
- ✅ Specific content is present

### Check System Context

Add logging to see what's sent to the LLM:

```python
# In your agent code
system_context = fuser.get_system_context()
print("SYSTEM CONTEXT LENGTH:", len(system_context))
print("KNOWLEDGE INCLUDED:", "KNOWLEDGE BASE:" in system_context)
```

## Best Practices

### 1. Structure Your Knowledge File

Use clear markdown sections that the LLM can reference:

```markdown
# Product Name Knowledge Base

## Section 1: Overview
Core information...

## Section 2: Features
Detailed features...

## Section 3: Common Questions
### Question 1
Answer...
```

### 2. Keep Prompts Focused

**❌ Bad - Everything in config:**
```json5
system_prompt_base: "You are Lex. Lexful is a platform that does X, Y, Z. 
Features include A, B, C. Pricing is $1500 for starter, $3500 for pro...
Objection 1: When they say X, respond with Y. Objection 2: When they say..."
// 5000+ characters of inline text
```

**✅ Good - Reference external knowledge:**
```json5
system_prompt_base: "You are Lex, Channel Chief AI for Lexful.

Reference your KNOWLEDGE BASE for:
- Product details and features
- Pricing information
- Objection handling
- Sample dialogues

Keep responses concise and professional."
knowledge_file: "docs/lexful_knowledge.md"
```

### 3. Version Control Knowledge Separately

```bash
git add docs/lexful_knowledge.md
git commit -m "Update Lexful pricing for Q4 2025"

# Config stays unchanged
```

### 4. Share Knowledge Across Agents

```json5
// config/lex_channel_chief.json5
knowledge_file: "docs/lexful_knowledge.md"

// config/lex_support_agent.json5
knowledge_file: "docs/lexful_knowledge.md"  // Same file!

// config/lex_demo_agent.json5
knowledge_file: "docs/lexful_knowledge.md"
```

## Advanced Usage

### Dynamic Knowledge Loading

If you need runtime knowledge updates (not implemented yet):

```python
# Future enhancement idea
class KnowledgeBaseInput(Sensor):
    """Input plugin that provides relevant knowledge snippets based on query."""
    
    async def _raw_to_text(self, raw_input) -> str:
        query = extract_query_from_conversation()
        relevant_snippets = search_knowledge_base(query)
        return f"Relevant knowledge: {relevant_snippets}"
```

### RAG Integration

For very large knowledge bases (not implemented yet):

```python
# Future enhancement idea
from langchain.vectorstores import FAISS
from langchain.embeddings import OpenAIEmbeddings

# Index knowledge at startup
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_texts([knowledge_content], embeddings)

# Retrieve relevant chunks per query
def get_relevant_knowledge(query: str, k=3):
    docs = vectorstore.similarity_search(query, k=k)
    return "\n".join([doc.page_content for doc in docs])
```

## Troubleshooting

### Knowledge File Not Found

```
WARNING:fuser:Knowledge file not found: docs/lexful_knowledge.md
```

**Solutions:**
- Check file path is correct (relative to project root)
- Verify file exists: `ls docs/lexful_knowledge.md`
- Use absolute path if relative doesn't work

### Knowledge Not Appearing in Responses

**Check:**
1. Is knowledge loaded? Look for: `INFO:fuser:Loaded external knowledge from: ...`
2. Is LLM context long enough? Check `max_tokens` in config
3. Is LLM referencing it? Add explicit instruction in system_prompt_base

### File Too Large

If knowledge file is extremely large (>50KB):

**Options:**
- Split into multiple focused files
- Implement RAG (search + retrieve relevant sections)
- Use summarization to condense
- Consider semantic chunking

## Examples

### Example 1: Lex Channel Chief (Implemented)

**Config:** `config/lex_channel_chief.json5`
- System prompt: ~2KB (concise role description)
- Knowledge file: ~18KB (full product details)
- Total context: ~21KB

**Benefits:**
- Config is readable and maintainable
- Knowledge can be updated by sales/marketing team
- Easy to version control changes

### Example 2: Customer Support Agent (Hypothetical)

```json5
{
  name: "support_agent",
  knowledge_file: "docs/product_documentation.md",
  
  system_prompt_base: "You are a helpful support agent.
  Use your KNOWLEDGE BASE for:
  - Product features and usage
  - Troubleshooting steps
  - Known issues and workarounds"
}
```

### Example 3: Multi-Agent Setup (Hypothetical)

```json5
// Shared knowledge across team
{
  name: "sales_agent",
  knowledge_file: "docs/company_knowledge.md",
  system_prompt_base: "You are a sales agent. Focus on pricing and demos."
}

{
  name: "support_agent", 
  knowledge_file: "docs/company_knowledge.md",
  system_prompt_base: "You are a support agent. Focus on troubleshooting."
}
```

## API Reference

### RuntimeConfig.knowledge_file

```python
@dataclass
class RuntimeConfig:
    # Optional external knowledge file path
    knowledge_file: Optional[str] = None
```

### Fuser._load_knowledge_file()

```python
def _load_knowledge_file(self, file_path: str) -> Optional[str]:
    """
    Load external knowledge file content.
    
    Parameters
    ----------
    file_path : str
        Path to knowledge file (relative to project root or absolute)
        
    Returns
    -------
    str or None
        File content, or None if file not found
    """
```

## Summary

The external knowledge system provides a clean separation between:
- **Configuration** (structure, settings, behavior)
- **Knowledge** (facts, procedures, examples)

This makes your agents more maintainable, updatable, and scalable.

---

**Created:** October 28, 2025  
**Author:** RoboAI Team  
**Related Files:**
- `src/fuser/__init__.py` - Fuser implementation
- `src/runtime/single_mode/config.py` - RuntimeConfig definition
- `config/lex_channel_chief.json5` - Example usage
- `docs/lexful_knowledge.md` - Example knowledge file
