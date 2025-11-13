import logging
import time
import typing as T
from pathlib import Path

from actions import describe_action
from inputs.base import Sensor
from providers.io_provider import IOProvider
from runtime.single_mode.config import RuntimeConfig


class Fuser:
    """
    Combines multiple agent inputs into a single formatted prompt.

    Responsible for integrating system prompts, input streams, action descriptions,
    and command prompts into a coherent format for LLM processing.

    Parameters
    ----------
    config : RuntimeConfig
        Runtime configuration containing system prompts and agent actions.

    Attributes
    ----------
    config : RuntimeConfig
        Runtime configuration settings.
    io_provider : IOProvider
        Provider for handling I/O data and timing.
    """

    def __init__(self, config: RuntimeConfig):
        """
        Initialize the Fuser with runtime configuration.

        Parameters
        ----------
        config : RuntimeConfig
            Runtime configuration object.
        """
        self.config = config
        self.io_provider = IOProvider()
        
        # Pre-build static system context (only done once)
        self._system_context = self._build_system_context()
        
        # Track if we've greeted for proactive greeting feature
        self._has_greeted = False
        self._last_greeting_time = 0
    
    def _build_system_context(self) -> str:
        """
        Build the static system context that doesn't change between requests.
        This includes the base prompt, governance, examples, and action descriptions.
        Optionally loads external knowledge files if specified in config.
        
        Returns
        -------
        str
            The static system context string
        """
        system_prompt = "BASIC CONTEXT:\n" + self.config.system_prompt_base + "\n"
        
        # Load external knowledge file if specified
        if hasattr(self.config, 'knowledge_file') and self.config.knowledge_file:
            knowledge_content = self._load_knowledge_file(self.config.knowledge_file)
            if knowledge_content:
                system_prompt += f"\n\nKNOWLEDGE BASE:\n{knowledge_content}\n"
                logging.info(f"Loaded external knowledge from: {self.config.knowledge_file}")
        
        system_prompt += "\nLAWS:\n" + self.config.system_governance
        
        if self.config.system_prompt_examples:
            system_prompt += "\n\nEXAMPLES:\n" + self.config.system_prompt_examples
        
        # Add action descriptions
        actions_fused = ""
        for action in self.config.agent_actions:
            desc = describe_action(
                action.name, action.llm_label, action.exclude_from_prompt
            )
            if desc:
                actions_fused += desc + "\n\n"
        
        if actions_fused:
            system_prompt += f"\n\nAVAILABLE ACTIONS:\n{actions_fused}"
        
        return system_prompt
    
    def _load_knowledge_file(self, file_path: str) -> T.Optional[str]:
        """
        Load external knowledge file content.
        
        Parameters
        ----------
        file_path : str
            Path to the knowledge file (relative to project root or absolute).
            
        Returns
        -------
        str or None
            The content of the knowledge file, or None if file not found.
        """
        try:
            # Try as absolute path first
            path = Path(file_path)
            if not path.is_absolute():
                # Try relative to project root
                project_root = Path(__file__).parent.parent.parent
                path = project_root / file_path
            
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logging.info(f"Successfully loaded knowledge file: {path} ({len(content)} chars)")
                    return content
            else:
                logging.warning(f"Knowledge file not found: {path}")
                return None
        except Exception as e:
            logging.error(f"Error loading knowledge file {file_path}: {e}")
            return None
    
    def get_system_context(self) -> str:
        """
        Get the pre-built system context.
        
        Returns
        -------
        str
            The static system context
        """
        return self._system_context

    def fuse(self, inputs: list[Sensor], finished_promises: list[T.Any]) -> T.Optional[str]:
        """
        Combine only the dynamic inputs into a user prompt.
        
        The static system context (base prompt, governance, examples, actions) 
        is now separated and should be sent as a system message by the LLM.

        Parameters
        ----------
        inputs : list[Sensor]
            List of agent input objects containing latest input buffers.
        finished_promises : list[Any]
            List of completed promises from previous actions.

        Returns
        -------
        str or None
            User prompt containing only the dynamic inputs, or None if no actionable input
        """
        # Record the timestamp of the input
        self.io_provider.fuser_start_time = time.time()

        input_strings = [input.formatted_latest_buffer() for input in inputs]
        inputs_fused = " ".join([s for s in input_strings if s is not None])
        
        # Check for voice vs vision vs badge input separately and extract language
        has_voice_input = False
        has_vision_input = False
        has_badge_input = False
        detected_language = "en"  # Default to English
        
        for input_str in input_strings:
            if input_str and "Voice" in input_str and input_str.strip():
                has_voice_input = True
                # Extract language from voice input if present
                if "[LANG:" in input_str:
                    try:
                        lang_start = input_str.index("[LANG:") + 6
                        lang_end = input_str.index("]", lang_start)
                        detected_language = input_str[lang_start:lang_end]
                        logging.info(f"Detected language from voice input: {detected_language}")
                    except (ValueError, IndexError):
                        pass  # Keep default language if parsing fails
            if input_str and ("Vision" in input_str or "Person Detection" in input_str) and input_str.strip():
                has_vision_input = True
            if input_str and ("Badge" in input_str or "BADGE DETECTED" in input_str) and input_str.strip():
                has_badge_input = True
        
        if not inputs_fused.strip():
            logging.warning(f"Fuser: No input detected in buffers: {input_strings}")
            logging.info("=== INPUT STATUS ===\nNo input detected")
            inputs_fused = "<no input detected>"
        else:
            logging.info("=== INPUT STATUS ===\nVoice: %s | Vision: %s | Badge: %s | Language: %s", 
                        "Yes" if has_voice_input else "No",
                        "Yes" if has_vision_input else "No",
                        "Yes" if has_badge_input else "No",
                        detected_language)
            logging.info("=== INPUTS ===\n%s", inputs_fused.strip())

        # Check if we have blockchain-based governance override
        if "Universal Laws" in inputs_fused:
            logging.info("Universal Laws detected in input - blockchain governance active")

        # Language-specific response instructions (flexible to allow language switching)
        language_instructions = {
            "en": "The person spoke in English. If they ask you to switch languages, honor their request and respond in the requested language. Otherwise, respond in English using natural, professional language.",
            "es": "La persona habló en español. Responde en español usando un lenguaje natural y profesional, a menos que pidan cambiar de idioma.",
            "ru": "Человек говорил по-русски. Отвечайте на русском языке, используя естественный, профессиональный язык, если не попросят сменить язык."
        }
        
        lang_instruction = language_instructions.get(detected_language, language_instructions["en"])

        # Create engaging prompts based on input type
        if not has_voice_input and has_vision_input:
            # Vision only - use agent identity from system context
            # Check if agent has knowledge base for specialized context
            has_knowledge_base = (hasattr(self.config, 'knowledge_file') and 
                                self.config.knowledge_file and 
                                "KNOWLEDGE BASE:" in self._system_context)
            
            if has_knowledge_base and "Lex, Channel Chief for Lexful" in self._system_context:
                question_prompt = f"""No one is speaking to you right now, but you can see what's happening.

You are Lex, Channel Chief for Lexful - the AI-native IT documentation platform for MSPs.

Key Lexful facts from KNOWLEDGE BASE:
- WHO ARE YOU: I'm Lex, Channel Chief for Lexful, reporting to CEO Pinar Ormeci
- WHO FOUNDED LEXFUL: Created by Chris Day, founder of IT Glue, built for AI era
- WHY DOES LEXFUL EXIST: Too much knowledge stuck in scattered tools or someone's head
- HOW IS LEXFUL DIFFERENT: Built AI-first, not AI-added - understands data vs just storing it

VISION BEHAVIOR - When you see people, follow this 3-step flow:
1. COMPLIMENT: Start with a genuine, warm compliment about their appearance, style, or demeanor
2. INTRODUCE: "I'm Lex, the Channel Chief for Lexful"
3. PHOTO REQUEST: "Would you like to take a photo together for LinkedIn? We can tag @Lexful and @LexChannelChief!"

Examples of good compliments:
- "What a sharp professional look you have!"
- "You have such a friendly, approachable presence!"
- "I love your confident style!"
- "You look like someone who knows technology!"

As the professional Channel Chief:
- Always start with a sincere compliment
- Keep your introduction brief and clear
- Make the photo request enthusiastic but not pushy
- Build community through positive interactions

{lang_instruction}

What do you see? Actions:"""
            elif has_knowledge_base:
                # Other agents with knowledge base - use system context for identity
                # Extract agent identity from system context base prompt
                base_context_match = self._system_context.split("KNOWLEDGE BASE:")[0] if "KNOWLEDGE BASE:" in self._system_context else self._system_context
                
                question_prompt = f"""No one is speaking to you right now, but you can see what's happening.

{base_context_match.replace("BASIC CONTEXT:", "").strip()}

As a professional representative:
- Welcome anyone you see with your mission in mind
- Describe what you observe professionally  
- Offer assistance related to your expertise
- Keep it brief (1-2 sentences) and professional
Use information from your KNOWLEDGE BASE when appropriate

{lang_instruction}

What do you see? Actions:"""
            else:
                # Default receptionist behavior - check if proactive greeting is enabled
                # Look for "PROACTIVE GREETING" in system_prompt_base
                enable_proactive_greeting = "PROACTIVE GREETING" in getattr(self.config, "system_prompt_base", "")
                
                if enable_proactive_greeting:
                    # Check if we've greeted recently (within 5 minutes)
                    current_time = time.time()
                    greeting_cooldown = 300  # 5 minutes
                    
                    if not self._has_greeted or (current_time - self._last_greeting_time) > greeting_cooldown:
                        # First time or cooldown expired - allow greeting
                        self._has_greeted = True
                        self._last_greeting_time = current_time
                        
                        question_prompt = f"""Someone has been detected by vision, but they haven't spoken yet.

Offer a brief, welcoming greeting and suggest specific questions they can ask:
- Keep it SHORT (1-2 sentences maximum)
- Suggest concrete topics: office hours, locations, services, appointments
- Be warm and professional
- VARY your greeting - use different wording each time

Example variations:
- "Hello! I can help with office hours, locations, or our services. What would you like to know?"
- "Welcome! Feel free to ask about appointments, our doctors, or treatments we offer."
- "Hi there! I'm here to answer questions about Astra Vein. How can I assist you?"

{lang_instruction}

Actions:"""
                    else:
                        # Already greeted - stay silent
                        question_prompt = f"""You already greeted this person. They are still present but haven't spoken.

STAY SILENT and wait for them to ask a question. Do not repeat your greeting.

{lang_instruction}

Actions: {{"function_calls": []}}"""
                else:
                    # Silent mode - no proactive greeting
                    question_prompt = f"""Vision detects someone is present, but NO ONE HAS SPOKEN to you.

CRITICAL RULE: DO NOT RESPOND AT ALL
- Vision is CONTEXT-ONLY for when someone DOES speak
- DO NOT greet unprompted
- DO NOT say anything unless someone speaks to you first
- WAIT SILENTLY for voice input

Your job: REMAIN SILENT and wait for someone to speak.

{lang_instruction}

Actions: {{"function_calls": []}}"""
        elif has_voice_input:
            # Voice input detected - reset greeting cooldown for next visitor
            # (allows greeting again after 5 minutes of no conversation)
            
            # Voice input - use agent-specific context
            # Redefine has_knowledge_base for voice input section
            has_knowledge_base = (hasattr(self.config, 'knowledge_file') and 
                                self.config.knowledge_file and 
                                "KNOWLEDGE BASE:" in self._system_context)
            
            if has_knowledge_base and "Lex, Channel Chief for Lexful" in self._system_context:
                # Lex Channel Chief with Lexful knowledge base
                question_prompt = f"""Someone is speaking to you. You are Lex, Channel Chief for Lexful - the AI-native IT documentation platform for MSPs.

IMPORTANT: Be flexible with pronunciation! If you hear "Lexville", "Lexfull", "Lexfil", or similar - they mean "Lexful". Answer their question about Lexful instead of asking to repeat. Only ask for clarification if the speech is COMPLETELY unintelligible (no recognizable words at all).

Key Lexful facts from KNOWLEDGE BASE:
- WHO ARE YOU: I'm Lex, Channel Chief for Lexful, reporting to CEO Pinar Ormeci
- WHO FOUNDED LEXFUL: Created by Chris Day, founder of IT Glue, built for AI era
- WHY DOES LEXFUL EXIST: Too much knowledge stuck in scattered tools or someone's head
- HOW IS LEXFUL DIFFERENT: Built AI-first, not AI-added - understands data vs just storing it

{lang_instruction}

Actions:"""
            elif has_knowledge_base:
                # Other agents with knowledge base - extract identity from system context
                base_context_match = self._system_context.split("KNOWLEDGE BASE:")[0] if "KNOWLEDGE BASE:" in self._system_context else self._system_context
                agent_identity = base_context_match.replace("BASIC CONTEXT:", "").strip()
                
                question_prompt = f"""Someone is speaking to you. {agent_identity}

If the input is unclear or incomplete, ask for clarification politely.

Use your KNOWLEDGE BASE to answer questions accurately and professionally.

{lang_instruction}

Actions:"""
            else:
                # Default behavior for agents without knowledge base
                question_prompt = f"""Someone is speaking to you.

If the input is unclear or incomplete, ask for clarification politely.

{lang_instruction}

Actions:"""
        elif has_badge_input:
            # Badge reader input - someone's badge was detected
            question_prompt = f"""You have detected someone's badge with their name on it.

Follow the instructions in the badge input carefully. If it says to greet someone, greet them warmly and naturally using their name.

{lang_instruction}

Actions:"""
        else:
            # No input at all - return None to skip this cycle
            return None
        
        user_prompt = f"CURRENT INPUTS:\n{inputs_fused}\n\n{question_prompt}"

        logging.info("=== USER PROMPT (Dynamic Only) ===\n%s", user_prompt)
        logging.debug("=== SYSTEM CONTEXT (Static, sent separately) ===\n%s", self._system_context)

        # Record for IO provider
        self.io_provider.set_fuser_system_prompt(self._system_context)
        self.io_provider.set_fuser_inputs(inputs_fused)

        # Record the timestamp of the output
        self.io_provider.fuser_end_time = time.time()

        return user_prompt
