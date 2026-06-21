import os
import re
from datetime import datetime
from abc import ABC, abstractmethod
from rich.console import Console
from rich.theme import Theme

# Hackerman theme for rich
custom_theme = Theme(
    {
        "info": "dim cyan",
        "warning": "magenta",
        "danger": "bold red",
        "success": "bold green",
        "hack": "bold bright_green",
    }
)
_rich_console = Console(theme=custom_theme)


class LogSink(ABC):
    @abstractmethod
    def write(self, message: str, **kwargs):
        pass


class ConsoleSink(LogSink):
    """Writes to terminal using Rich."""

    def write(self, message: str, **kwargs):
        _rich_console.print(message, **kwargs)


class FileSink(LogSink):
    """Writes plain text logs to a file."""

    def __init__(self, filepath="logs/sentinel.log"):
        self.filepath = filepath
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        # Regex to strip rich tags like [bold red] or [/bold red]
        self.markup_regex = re.compile(r"\[/?([a-z0-9_ ]+)\]")

    def write(self, message: str, **kwargs):
        plain_message = self.markup_regex.sub("", str(message))
        timestamp = datetime.utcnow().isoformat()
        log_entry = f"[{timestamp}] {plain_message}\n"
        with open(self.filepath, "a", encoding="utf-8") as f:
            f.write(log_entry)


class ElasticsearchSink(LogSink):
    """Sends JSON logs to an Elasticsearch index (stub)."""

    def __init__(self, enabled=False):
        self.enabled = enabled
        self.markup_regex = re.compile(r"\[/?([a-z0-9_ ]+)\]")

    def write(self, message: str, **kwargs):
        if not self.enabled:
            return
        plain_message = self.markup_regex.sub("", str(message))
        _ = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": plain_message,
        }
        # In a real scenario, use requests.post or elasticsearch-py
        # requests.post("http://localhost:9200/sentinel/_doc", json=payload)
        pass


class AgnosticLogger:
    """
    Acts as a drop-in replacement for rich.Console in existing code.
    Fans out print() calls to all registered sinks.
    """

    def __init__(self, sinks=None):
        self.sinks = sinks or []

    def print(self, message: str, **kwargs):
        for sink in self.sinks:
            try:
                sink.write(message, **kwargs)
            except Exception:
                pass


# Singleton instance pre-configured with Console and File sinks
_agnostic_console = AgnosticLogger(
    sinks=[
        ConsoleSink(),
        FileSink(),
        ElasticsearchSink(
            enabled=os.getenv("ELASTICSEARCH_ENABLED", "false").lower() == "true"
        ),
    ]
)


def get_console():
    return _agnostic_console
