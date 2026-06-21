from src.core.logger import (
    AgnosticLogger,
    ConsoleSink,
    FileSink,
    ElasticsearchSink,
    get_console,
)


def test_console_sink(capsys):
    sink = ConsoleSink()
    sink.write("[bold red]Error[/bold red]")
    # Using rich.console print directly writes to stdout
    captured = capsys.readouterr()
    assert "Error" in captured.out


def test_file_sink(tmp_path):
    log_file = tmp_path / "sentinel.log"
    sink = FileSink(filepath=str(log_file))

    sink.write("[bold red]This is an error[/bold red] with [info]info[/info]")

    assert log_file.exists()
    content = log_file.read_text()
    assert "This is an error with info" in content
    assert "[bold red]" not in content
    assert "[info]" not in content


def test_elasticsearch_sink():
    sink_disabled = ElasticsearchSink(enabled=False)
    # Should not crash and basically do nothing
    sink_disabled.write("Test message")


def test_agnostic_logger_fanout(tmp_path):
    log_file = tmp_path / "sentinel.log"
    file_sink = FileSink(filepath=str(log_file))
    console_sink = ConsoleSink()

    logger = AgnosticLogger(sinks=[console_sink, file_sink])
    logger.print("[hack]Hackerman[/hack]")

    content = log_file.read_text()
    assert "Hackerman" in content
    assert "[hack]" not in content


def test_get_console():
    console = get_console()
    assert isinstance(console, AgnosticLogger)
    assert len(console.sinks) == 3
