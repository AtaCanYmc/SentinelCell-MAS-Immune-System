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

    def __init__(self, filepath=None):
        if filepath is None:
            if os.path.exists("/logs") and os.access("/logs", os.W_OK):
                filepath = "/logs/sentinel.log"
            else:
                filepath = "logs/sentinel.log"
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
    """Sends JSON logs to an Elasticsearch index."""

    def __init__(
        self,
        enabled=False,
        url="http://elasticsearch-1:9200",
        index_name="sentinel-logs",
    ):
        self.enabled = enabled
        self.index_name = index_name
        self.markup_regex = re.compile(r"\[/?([a-z0-9_ ]+)\]")
        self.es = None
        if self.enabled:
            try:
                from elasticsearch import Elasticsearch

                es_user = os.getenv("ELASTICSEARCH_USER", "elastic")
                es_pass = os.getenv("ELASTICSEARCH_PASSWORD")

                if es_pass:
                    self.es = Elasticsearch(url, basic_auth=(es_user, es_pass))
                else:
                    self.es = Elasticsearch(url)
            except Exception:
                self.enabled = False

    def write(self, message: str, **kwargs):
        if not self.enabled or not self.es:
            return
        plain_message = self.markup_regex.sub("", str(message))
        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "message": plain_message,
        }
        try:
            self.es.index(index=self.index_name, document=payload)
        except Exception:
            pass


class AgnosticLogger:
    """
    Acts as a drop-in replacement for rich.Console in existing code.
    Fans out print() calls to all registered sinks.
    """

    def __init__(self, sinks=None):
        self.sinks = sinks or []

    def print(self, message: str, **kwargs):
        import asyncio
        import threading

        def _fanout():
            for sink in self.sinks:
                try:
                    sink.write(message, **kwargs)
                except Exception:
                    pass

        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        import sys

        if "pytest" in sys.modules:
            _fanout()
        elif loop and loop.is_running():
            loop.run_in_executor(None, _fanout)
        else:
            t = threading.Thread(target=_fanout, daemon=True)
            t.start()


# Singleton instance pre-configured with Console and File sinks
_agnostic_console = AgnosticLogger(
    sinks=[
        ConsoleSink(),
        FileSink(),
        ElasticsearchSink(
            enabled=os.getenv("ELASTICSEARCH_ENABLED", "false").lower() == "true",
            url=os.getenv("ELASTICSEARCH_URL", "http://elasticsearch-1:9200"),
        ),
    ]
)


def get_console():
    return _agnostic_console
