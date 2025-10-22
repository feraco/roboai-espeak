import logging
import time

from actions.base import ActionConfig, ActionConnector
from actions.face.interface import FaceInput
from providers.avatar_provider import AvatarProvider


class FaceAvatarConnector(ActionConnector[FaceInput]):
    def __init__(self, config: ActionConfig):
        """
        Initialize the FaceAvatarConnector with the given configuration.

        Parameters:
        ----------
        config : ActionConfig
            Configuration parameters for the connector.
        """
        super().__init__(config)

        self.avatar_provider = AvatarProvider()

        logging.info("Emotion system intiated")

    async def connect(self, output_interface: FaceInput) -> None:
        """
        Connect to the avatar system and send the appropriate face command.

        Parameters:
        ----------
        output_interface : FaceInput
            The face input containing the action to be performed.
        """
        if output_interface.action == "happy":
            self.avatar_provider.send_avatar_command("Happy")
        elif output_interface.action == "sad":
            self.avatar_provider.send_avatar_command("Sad")
        elif output_interface.action == "curious":
            self.avatar_provider.send_avatar_command("Curious")
        elif output_interface.action == "confused":
            self.avatar_provider.send_avatar_command("Confused")
        elif output_interface.action == "think":
            self.avatar_provider.send_avatar_command("Think")
        elif output_interface.action == "excited":
            self.avatar_provider.send_avatar_command("Excited")
        else:
            logging.info(f"Unknown emotion: {output_interface.action}")

        logging.info(f"SendThisToUTClient: {output_interface.action}")

    def tick(self) -> None:
        time.sleep(60)
