"""Utilities for PyBotchi Agent for file."""

from cv2.typing import MatLike

from pydantic import BaseModel, ConfigDict, Field


class DocxContent(BaseModel):
    """Docx Content."""

    id: int
    text: str = ""
    images: dict[str, bytes] = Field(default_factory=dict)
    ignored_images: list[MatLike] = Field(default_factory=list)
    table: bool = False

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def append(self, text: str) -> None:
        """Append text."""
        self.text = f"{self.text}{text}"

    def add_image(self, placeholder: str, text: bytes) -> None:
        """Add image placeholder."""
        self.images[placeholder] = text

    def merge_images(self, images: dict[str, bytes]) -> None:
        """Add image placeholder."""
        if images:
            self.images.update(images)

    def child(self) -> "DocxContent":
        """Spawn child."""
        return DocxContent(id=self.id, ignored_images=self.ignored_images)
