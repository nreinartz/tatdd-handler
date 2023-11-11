import requests
from dataclasses import dataclass
from models.shared import QueryRequest


class ChatSession:
    def __init__(self, botName, channel, messenger):
        self.messenger = messenger
        self.botName = botName
        self.channel = channel
        self.webhookEndpoint = "http://localhost:8090/SBFManager/bots/{}/webhook".format(
            botName)

    def send_message(self, text):
        data = {
            "event": "chat_message",
            "messenger": self.messenger,
            "channel": self.channel,
            "message": text
        }

        response = requests.post(self.webhookEndpoint, json=data)

        return response.status_code == 200


@dataclass
class QuerySession:
    uuid: str
    parameters: QueryRequest
    chat_session: ChatSession
