import os
import sys
import asyncio
import orjson
from fastapi import WebSocket
from src.core.logger import get_console
from src.gateways.constants import SAFE_SCRIPTS

console = get_console()


class ExecutionService:
    @staticmethod
    async def run_simulation_script(websocket: WebSocket, script_name: str):
        if script_name not in SAFE_SCRIPTS:
            await websocket.send_text(
                orjson.dumps({"type": "error", "line": "Invalid script name."}).decode(
                    "utf-8"
                )
            )
            await websocket.close()
            return

        base_dir = os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        )
        script_path = os.path.join(base_dir, "examples", f"{script_name}.py")
        if not os.path.exists(script_path):
            await websocket.send_text(
                orjson.dumps(
                    {"type": "error", "line": "Script file not found."}
                ).decode("utf-8")
            )
            await websocket.close()
            return

        python_bin = sys.executable

        env = os.environ.copy()
        env["PYTHONPATH"] = "."
        env["PYTHONUNBUFFERED"] = "1"
        env["MOCK_LLM"] = "true"

        process = None
        try:
            process = await asyncio.create_subprocess_exec(
                python_bin,
                script_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                env=env,
            )

            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                line_str = line.decode("utf-8", errors="replace").rstrip()
                await websocket.send_text(
                    orjson.dumps({"type": "stdout", "line": line_str}).decode("utf-8")
                )

            await process.wait()
            exit_code = process.returncode
            await websocket.send_text(
                orjson.dumps({"type": "exit", "code": exit_code}).decode("utf-8")
            )
        except Exception as e:
            try:
                await websocket.send_text(
                    orjson.dumps(
                        {"type": "error", "line": f"Execution error: {str(e)}"}
                    ).decode("utf-8")
                )
            except Exception:
                pass
        finally:
            if process and process.returncode is None:
                try:
                    process.terminate()
                    await process.wait()
                except Exception as term_err:
                    console.print(
                        f"[bold red]Error terminating script process:[/bold red] {term_err}"
                    )
            try:
                await websocket.close()
            except Exception as close_err:
                console.print(
                    f"[bold red]Error closing WebSocket:[/bold red] {close_err}"
                )
