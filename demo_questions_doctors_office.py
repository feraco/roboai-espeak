"""
Demo Questions for Astra Vein Receptionist Agent

This script provides a list of sample questions you can ask the agent about the doctor's office, based on the LLM's system prompt and knowledge.
"""

QUESTIONS = [
    # General info
    "What services do you offer?",
    "Where is the office located?",
    "What are your office hours?",
    "How do I schedule an appointment?",
    "Do you accept walk-ins?",
    "Is Spanish language support available?",
    "What is the main phone number?",
    "Do you have multiple locations?",
    "Is parking available at the office?",
    "Do you offer telemedicine appointments?",

    # Doctors and staff
    "Who is the main doctor here?",
    "Can you tell me about Dr. George Bolotin?",
    "Are there other doctors or staff I can speak to?",
    "Is Dr. Bolotin board-certified?",
    "What are the qualifications of your staff?",

    # Treatments and conditions
    "Do you treat varicose veins?",
    "What treatments do you offer for spider veins?",
    "Do you provide wound care for venous ulcers?",
    "Can you help with circulation problems?",
    "Do you treat deep vein thrombosis (DVT)?",
    "What methods do you use for vein treatment?",
    "Do you offer fibroid treatments?",
    "Are your procedures outpatient?",
    "Is the treatment painful?",
    "How long does recovery take?",

    # Insurance and payment
    "Do you accept insurance?",
    "What payment methods are accepted?",
    "Do you offer payment plans?",

    # Patient experience
    "Is the office wheelchair accessible?",
    "How long is the typical wait time?",
    "What should I bring to my appointment?",
    "Can I bring a family member with me?",
    "Do you have a waiting room?",
    "Is there Wi-Fi available for patients?",

    # Other
    "Are you approved as an Ambulatory Surgery Center?",
    "What makes Astra Vein Treatment Center unique?",
    "How do you ensure patient privacy?",
    "Can I get directions to the office?",
    "Do you offer consultations for new patients?"
]

if __name__ == "__main__":
    print("Demo Questions for Astra Vein Receptionist Agent:\n")
    for i, q in enumerate(QUESTIONS, 1):
        print(f"{i}. {q}")
