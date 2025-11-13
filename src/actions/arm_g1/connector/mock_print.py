import logging
from actions.arm_g1.interface import ArmInput
from actions.base import ActionConfig, ActionConnector


class ARMMockPrintConnector(ActionConnector[ArmInput]):
    """Mock connector that prints arm actions to console for testing on Mac"""

    def __init__(self, config: ActionConfig):
        super().__init__(config)
        logging.info("🤖 ARM MOCK PRINT CONNECTOR initialized (Mac testing mode)")

    async def connect(self, output_interface: ArmInput) -> None:
        """Prints the arm action to console instead of executing on robot"""
        
        action = output_interface.action
        
        print("\n" + "="*60)
        print(f"🤖 ARM GESTURE: {action.upper()}")
        print("="*60)
        
        # Map actions to descriptions
        descriptions = {
            "idle": "No gesture (resting position)",
            "high wave": "👋 Waving hello (greeting gesture)",
            "heart": "❤️  Making heart shape (gratitude gesture)",
            "clap": "👏 Clapping hands (celebration gesture)",
            "high five": "🙌 High five gesture",
            "shake hand": "🤝 Handshake gesture",
            "left kiss": "😘 Left kiss gesture",
            "right kiss": "😘 Right kiss gesture"
        }
        
        description = descriptions.get(action, "Unknown gesture")
        print(f"   {description}")
        print("="*60 + "\n")
        
        logging.info(f"ARM GESTURE EXECUTED: {action}")
