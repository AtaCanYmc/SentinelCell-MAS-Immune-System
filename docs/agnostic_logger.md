# Agnostic Logger (Log Sink Pattern)

![Logging](https://img.shields.io/badge/Logging-Sink_Pattern-blue?style=for-the-badge)
![Rich](https://img.shields.io/badge/Terminal-Rich-magenta?style=for-the-badge)
![Elasticsearch](https://img.shields.io/badge/Elasticsearch-Ready-yellow?style=for-the-badge)

The **SentinelCell MAS Immune System** operates in a highly autonomous and critical environment. Observability is key. To ensure logs are not lost in isolated containers and can be easily aggregated, we implement the **Agnostic Logger** using the **Log Sink (Havuz) Pattern**.

This strategy completely decouples the logging logic from the underlying storage mechanism, allowing logs to fan out to multiple destinations simultaneously without altering the application's core codebase.

## 1. The Strategy: "Fan-out" Log Sinks

Instead of a traditional logger writing directly to `stdout` or a single file, SentinelCell uses an `AgnosticLogger` instance. When the application issues a `console.print()` command, the `AgnosticLogger` intercepts the message and broadcasts it to all registered `LogSink`s.

### Backward Compatibility
SentinelCell natively uses the [Rich](https://github.com/Textualize/rich) library to output beautiful, color-coded, and styled text in the terminal. The `AgnosticLogger` maintains 100% backward compatibility by exposing a `print()` method that accepts standard Rich markup.

## 2. Available Sinks

### 🖥️ ConsoleSink
- **Purpose**: Prints logs to the standard terminal (`stdout`).
- **Behavior**: Preserves all Rich markup tags (e.g., `[bold red]Error[/bold red]`).
- **Use Case**: Real-time debugging and visual monitoring for developers.

### 📄 FileSink
- **Purpose**: Writes logs to a persistent local file (`logs/sentinel.log`).
- **Behavior**: Uses Regex (`\[/?([a-z0-9_ ]+)\]`) to automatically strip all Rich markup tags before writing. It prepends an ISO 8601 UTC timestamp to every entry.
- **Use Case**: Persistent storage, historical debugging, and file-beat ingestion.

### 🌐 ElasticsearchSink (Stub)
- **Purpose**: Sends logs as structured JSON to a remote Elasticsearch cluster (or any ELK stack).
- **Behavior**: Activated via the `ELASTICSEARCH_ENABLED=true` environment variable. Strips Rich markup and formats the log as a JSON payload (`{"timestamp": "...", "message": "..."}`).
- **Use Case**: Centralized monitoring, alerting, and observability dashboards.

## 3. How It Works

Here is how the architecture processes a simple log:

```python
from src.core.logger import get_console

console = get_console()
console.print("[danger][!] MALFORMED JSON DETECTED[/danger]")
```

**What happens under the hood:**
1. The message reaches `AgnosticLogger.print()`.
2. It loops through the registered sinks:
   - **ConsoleSink** receives it and prints a colored red string to the terminal.
   - **FileSink** intercepts it, strips the `[danger]` tags, and appends `[2026-06-21T18:40:00Z] [!] MALFORMED JSON DETECTED` to the `.log` file.
   - **ElasticsearchSink** (if enabled) fires an HTTP POST request with the JSON payload to the logging server.

## 4. Extending the Logger

Thanks to the abstract `LogSink` base class, adding a new logging destination (like Datadog, Splunk, or a Kafka topic) is extremely simple. Just inherit from `LogSink` and implement the `write` method:

```python
class DatadogSink(LogSink):
    def write(self, message: str, **kwargs):
        plain_message = self.markup_regex.sub("", str(message))
        # Send to Datadog API
```

Then, register it in the `_agnostic_console` initialization within `src/core/logger.py`.
