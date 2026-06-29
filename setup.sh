#!/usr/bin/env bash
set -e

echo "==============================================="
echo "🛡️  SentinelCell MAS Immune System Setup Wizard"
echo "==============================================="

if [ -f .env ]; then
  echo "[!] An existing .env file was found. We will append/overwrite settings."
else
  echo "[+] Creating new .env file."
  touch .env
fi

echo ""
echo "Select your primary LLM Provider for Auto-Healing:"
echo "1) OPENAI (Requires OPENAI_API_KEY)"
echo "2) GROQ (Requires GROQ_API_KEY)"
echo "3) LOCAL_OLLAMA (No key required, runs locally)"
read -p "Choice (1-3): " llm_choice

case $llm_choice in
  1)
    provider_order="OPENAI,GROQ,LOCAL_OLLAMA"
    read -p "Enter your OPENAI_API_KEY: " openai_key
    echo "OPENAI_API_KEY=$openai_key" >> .env
    ;;
  2)
    provider_order="GROQ,OPENAI,LOCAL_OLLAMA"
    read -p "Enter your GROQ_API_KEY: " groq_key
    echo "GROQ_API_KEY=$groq_key" >> .env
    ;;
  3)
    provider_order="LOCAL_OLLAMA,OPENAI,GROQ"
    echo "[+] Local Ollama selected. We will configure Docker Compose to spin it up automatically."
    echo "COMPOSE_PROFILES=ollama" >> .env
    ;;
  *)
    provider_order="OPENAI,GROQ,LOCAL_OLLAMA"
    ;;
esac

echo "PROVIDER_ORDER=$provider_order" >> .env

echo ""
read -p "Enable ChatOps Alerting? Enter Slack/Discord Webhook URL (leave blank to skip): " webhook_url
if [ -n "$webhook_url" ]; then
    echo "SLACK_WEBHOOK_URL=$webhook_url" >> .env
fi

echo ""
echo "[+] Starting Docker Compose..."
docker compose up -d --build

echo ""
echo "[+] SentinelCell is running!"
echo "Dashboard: http://localhost:3000"
echo "Gateway: http://localhost:8000"
