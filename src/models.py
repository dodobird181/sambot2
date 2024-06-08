import dataclasses


@dataclasses.dataclass
class Message:
    role: str
    content: str
