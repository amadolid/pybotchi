"""Pybotchi A2A Common."""

from copy import deepcopy
from typing import TypedDict

from a2a.utils.constants import AGENT_CARD_WELL_KNOWN_PATH, EXTENDED_AGENT_CARD_PATH


class A2ACard(TypedDict, total=False):
    """A2A Card Config."""

    path: str
    headers: dict[str, str] | None


class A2AConfig(TypedDict, total=False):
    """A2A Config."""

    base_url: str
    headers: dict[str, str] | None
    cards: dict[str, A2ACard] | None
    agent_card_path: str
    relative_card_path: str


class A2AIntegration(TypedDict, total=False):
    """A2A Integration."""

    config: A2AConfig
    allowed_tools: set[str]
    exclude_unset: bool


class A2AConnection:
    """A2A Connection configurations."""

    def __init__(
        self,
        name: str,
        base_url: str = "",
        headers: dict[str, str] | None = None,
        cards: dict[str, A2ACard] | None = None,
        agent_card_path: str = AGENT_CARD_WELL_KNOWN_PATH,
        relative_card_path: str = EXTENDED_AGENT_CARD_PATH,
        allowed_tools: set[str] | None = None,
        exclude_unset: bool = True,
        require_integration: bool = True,
    ) -> None:
        """Build A2A Connection."""
        self.name = name
        self.base_url = base_url
        self.headers = headers
        self.cards = cards
        self.agent_card_path = agent_card_path
        self.relative_card_path = relative_card_path
        self.allowed_tools = set[str]() if allowed_tools is None else allowed_tools
        self.exclude_unset = exclude_unset
        self.require_integration = require_integration

    def get_config(self, override: A2AConfig | None) -> A2AConfig:
        """Generate config."""
        if override is None:
            return {
                "base_url": self.base_url,
                "headers": self.headers,
                "cards": self.cards,
                "agent_card_path": self.agent_card_path,
                "relative_card_path": self.relative_card_path,
            }

        headers: dict[str, str] | None
        if _headers := override.get("headers"):
            if self.headers is None:
                headers = _headers
            else:
                headers = self.headers | _headers
        else:
            headers = self.headers

        if _cards := override.get("cards"):
            if self.cards is None:
                cards: dict[str, A2ACard] | None = _cards
            else:
                cards = deepcopy(self.cards)
                for key, value in _cards.items():
                    if old_card := cards.get(key):
                        old_card.update(value)
                    else:
                        cards[key] = value
        else:
            cards = self.cards

        return {
            "base_url": override.get("base_url", self.base_url),
            "headers": headers,
            "cards": cards,
            "agent_card_path": override.get("agent_card_path", self.agent_card_path),
            "relative_card_path": override.get(
                "relative_card_path", self.relative_card_path
            ),
        }
