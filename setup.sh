#!/usr/bin/env bash
set -e

echo "==============================================="
echo "🛡️  SentinelCell MAS Immune System Setup Wizard"
echo "==============================================="

if [ -f .env ]; then
  echo "[!] An existing .env file was found. We will update settings."
else
  echo "[+] Creating new .env file."
  touch .env
fi

# Overwrite/update helper function for .env
set_env_var() {
  local key=$1
  local val=$2
  local escaped_val=$(echo "$val" | sed 's/[&/\]/\\&/g')
  if grep -q "^${key}=" .env 2>/dev/null; then
    sed -i.bak "s|^${key}=.*|${key}=${escaped_val}|g" .env && rm -f .env.bak
  else
    echo "${key}=${val}" >> .env
  fi
}

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
    set_env_var "OPENAI_API_KEY" "$openai_key"
    ;;
  2)
    provider_order="GROQ,OPENAI,LOCAL_OLLAMA"
    read -p "Enter your GROQ_API_KEY: " groq_key
    set_env_var "GROQ_API_KEY" "$groq_key"
    ;;
  3)
    provider_order="LOCAL_OLLAMA,OPENAI,GROQ"
    echo "[+] Local Ollama selected. We will configure Docker Compose to spin it up automatically."
    set_env_var "COMPOSE_PROFILES" "ollama"
    ;;
  *)
    provider_order="OPENAI,GROQ,LOCAL_OLLAMA"
    ;;
esac

set_env_var "PROVIDER_ORDER" "$provider_order"

echo ""
read -p "Enable ChatOps Alerting? Enter Slack/Discord Webhook URL (leave blank to skip): " webhook_url
if [ -n "$webhook_url" ]; then
    set_env_var "SLACK_WEBHOOK_URL" "$webhook_url"
fi

echo ""
echo "[+] Starting Docker Compose..."
docker compose up -d --build

echo ""
echo "[+] SentinelCell is running!"
echo "Dashboard: http://localhost:3000"
echo "Gateway: http://localhost:8000"
