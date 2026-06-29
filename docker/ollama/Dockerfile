FROM ollama/ollama:latest

# Start the Ollama server in the background, wait for it to be ready,
# pull the required model, and then kill the background server
# so the image can be committed with the model baked in.
RUN nohup bash -c "ollama serve &" && \
    sleep 5 && \
    ollama pull llama3.1 && \
    pkill ollama
