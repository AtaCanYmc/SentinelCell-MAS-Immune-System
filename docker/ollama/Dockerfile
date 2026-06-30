FROM ollama/ollama:latest

# Start the Ollama server in the background, wait for it to be ready,
# pull the required model, and then kill the background server
# so the image can be committed with the model baked in.
RUN nohup bash -c "ollama serve &" && \
    for i in {1..30}; do if curl -s http://localhost:11434/api/tags > /dev/null; then break; fi; sleep 1; done && \
    ollama pull llama3.1 && \
    pkill ollama
