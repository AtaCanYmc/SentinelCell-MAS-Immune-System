import orjson
from fastapi import WebSocket, WebSocketDisconnect
from src.core.logger import get_console

console = get_console()


class ChatService:
    @staticmethod
    async def handle_websocket_chat(
        websocket: WebSocket, sentinel, provider: str, lang: str
    ):
        """
        Extracted chat handling logic. Keeps websocket handling separate from routing.
        """
        try:
            await websocket.accept()
        except RuntimeError:  # already accepted or closed
            pass

        from src.core.llm_factory import LLMFactory
        from src.core.chat_tools import get_chat_tools
        from langchain_core.messages import (
            SystemMessage,
            HumanMessage,
            ToolMessage,
            AIMessage,
        )
        from src.core.prompt_manager import PromptManager

        try:
            llm = LLMFactory.get_llm(provider)

            # Initialize and bind tools
            tools = get_chat_tools(sentinel)
            tools_map = {t.name: t for t in tools}
            llm_with_tools = llm.bind_tools(tools)

            # Initialize conversation history outside the loop
            system_prompt = PromptManager.render("assistant.jinja2", {"lang": lang})
            messages = [SystemMessage(content=system_prompt)]

            while True:
                try:
                    data = await websocket.receive_text()
                except WebSocketDisconnect:
                    break

                # Send initial metadata
                await websocket.send_text(
                    orjson.dumps({"type": "start", "provider": provider}).decode(
                        "utf-8"
                    )
                )

                # Append new user message to history
                messages.append(HumanMessage(content=data))

                # Upfront Intent Classification Step using the base LLM (no tools)
                intent_prompt = PromptManager.render(
                    "intent_classifier.jinja2", {"user_message": data}
                )
                try:
                    intent_resp = await llm.ainvoke(
                        [HumanMessage(content=intent_prompt)]
                    )
                    intent = intent_resp.content.strip().upper()
                    is_system_intent = "SYSTEM" in intent
                except Exception as e:
                    # Fallback to system mode just in case
                    print(
                        f"[bold yellow]Intent Classification Error:[/bold yellow] {e}"
                    )
                    is_system_intent = True

                try:
                    # Agentic loop to resolve tool calls
                    while True:
                        active_llm = llm_with_tools if is_system_intent else llm
                        response = await active_llm.ainvoke(messages)

                        if (
                            hasattr(response, "tool_calls")
                            and response.tool_calls
                            and is_system_intent
                        ):
                            messages.append(response)

                            for tool_call in response.tool_calls:
                                tool_name = tool_call["name"]
                                tool_args = tool_call["args"]
                                tool_id = tool_call["id"]

                                # Stream back intermediate status message to show progress
                                status_msg = (
                                    f"\n[System: Calling tool {tool_name}...]\n"
                                )
                                await websocket.send_text(
                                    orjson.dumps(
                                        {"type": "chunk", "content": status_msg}
                                    ).decode("utf-8")
                                )

                                # Execute tool
                                tool_obj = tools_map.get(tool_name)
                                if tool_obj:
                                    try:
                                        tool_result = await tool_obj.ainvoke(tool_args)
                                    except Exception as e:
                                        tool_result = f"Error executing tool: {e}"
                                else:
                                    tool_result = f"Tool '{tool_name}' not found."

                                messages.append(
                                    ToolMessage(
                                        content=str(tool_result), tool_call_id=tool_id
                                    )
                                )

                            # Loop again to feed tool results back to LLM
                            continue
                        else:
                            # Once all tools are resolved, stream final text response and capture it for history
                            final_response_content = ""
                            async for chunk in llm.astream(messages):
                                content = (
                                    chunk.content
                                    if hasattr(chunk, "content")
                                    else str(chunk)
                                )
                                if content:
                                    final_response_content += content
                                    await websocket.send_text(
                                        orjson.dumps(
                                            {"type": "chunk", "content": content}
                                        ).decode("utf-8")
                                    )
                            messages.append(AIMessage(content=final_response_content))
                            break

                    await websocket.send_text(
                        orjson.dumps({"type": "end"}).decode("utf-8")
                    )
                except Exception as stream_err:
                    await websocket.send_text(
                        orjson.dumps(
                            {"type": "error", "content": str(stream_err)}
                        ).decode("utf-8")
                    )
        except WebSocketDisconnect:
            pass
        except Exception as e:
            try:
                await websocket.send_text(
                    orjson.dumps({"type": "error", "content": str(e)}).decode("utf-8")
                )
            except Exception as e:
                console.print(
                    f"[bold red]Error sending error message to websocket:[/bold red] {e}"
                )
                pass
