import React, { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Send, Bot, Loader2, Trash2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';

const fetchConfig = async () => {
  const res = await fetch('/api/config');
  if (!res.ok) return {};
  return res.json();
};

export default function ChatTest() {
  const { data: config = {} } = useQuery({ queryKey: ['config'], queryFn: fetchConfig, refetchInterval: 30000 });
  const { t, i18n } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [provider, setProvider] = useState('OPENAI');
  const wsRef = useRef(null);

  useEffect(() => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    // If running in dev server (Vite - port 5173), point to 8000.
    const host = window.location.port === '5173'
      ? `${window.location.hostname}:8000`
      : window.location.host;

    const lang = i18n.language || 'en';
    const tokenParam = config.API_KEY_SECRET ? `&token=${config.API_KEY_SECRET}` : '';
    const wsUrl = `${protocol}//${host}/ws/chat?lang=${lang}&provider=${provider}${tokenParam}`;

    const connectWs = () => {
      console.log('Connecting to WebSocket:', wsUrl);
      wsRef.current = new WebSocket(wsUrl);

      wsRef.current.onmessage = (event) => {
        const data = JSON.parse(event.data);

        if (data.type === 'start') {
          setMessages(prev => [...prev, { role: 'bot', content: '', provider: data.provider }]);
        } else if (data.type === 'chunk') {
          setMessages(prev => {
            const newMsgs = [...prev];
            if (newMsgs.length > 0 && newMsgs[newMsgs.length - 1].role === 'bot') {
              newMsgs[newMsgs.length - 1].content += data.content;
            }
            return newMsgs;
          });
        } else if (data.type === 'end') {
          setLoading(false);
        } else if (data.type === 'error') {
          setMessages(prev => [...prev, { role: 'error', content: data.content }]);
          setLoading(false);
        }
      };

      wsRef.current.onerror = (error) => {
        console.error('WebSocket Error:', error);
      };

      wsRef.current.onclose = () => {
        // Simple reconnect logic on abnormal close
        // Only reconnect if state is not unmounted
      };
    };

    connectWs();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [provider, i18n.language, config]);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      wsRef.current.send(userMsg);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', content: err.toString() }]);
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setLoading(false);
  };

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  return (
    <div className="flex flex-col h-[calc(100vh-280px)] min-h-[550px] max-w-6xl mx-auto bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-2xl animate-in fade-in duration-300">
      <div className="bg-gray-800 p-4 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Bot className="text-[#58a6ff]" />
          {t('chat.title')}
        </h2>

        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400 font-semibold">{t('chat.provider') || 'Provider'}:</span>
            <select
              value={provider}
              onChange={(e) => { setProvider(e.target.value); clearChat(); }}
              className="bg-black/50 border border-white/10 rounded px-2.5 py-1 text-xs text-gray-200 focus:outline-none focus:border-blue-500 transition-colors cursor-pointer font-medium"
            >
              <option value="OPENAI">OpenAI GPT</option>
              <option value="ANTHROPIC">Anthropic Claude</option>
              <option value="GEMINI">Google Gemini</option>
              <option value="GROQ">Groq LLaMA</option>
              <option value="LOCAL_OLLAMA">Local Ollama</option>
            </select>
          </div>

          <button
            onClick={clearChat}
            className="p-1.5 hover:bg-white/5 rounded text-gray-400 hover:text-red-400 transition-colors border border-white/5"
            title="Clear Chat History"
          >
            <Trash2 size={16} />
          </button>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#0a0a0a]">
        {messages.length === 0 && (
          <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 max-w-md mx-auto">
            <Bot className="w-12 h-12 text-[#58a6ff] opacity-40 mb-4" />
            <p className="text-sm">
              Start a diagnostic chat session with the Immune system validator model. You can type commands, ask security questions, or mock anomalies.
            </p>
          </div>
        )}

        {messages.map((msg, idx) => (
          <div key={idx} className={`flex flex-col ${msg.role === 'user' ? 'items-end' : 'items-start'}`}>
            <div className={`max-w-[80%] rounded-2xl p-4 ${
              msg.role === 'user'
                ? 'bg-blue-600 text-white rounded-br-none'
                : msg.role === 'error'
                  ? 'bg-red-900/50 text-red-200 border border-red-800 rounded-bl-none'
                  : 'bg-gray-800 text-gray-100 border border-gray-700 rounded-bl-none'
            }`}>
              {msg.role === 'bot' && msg.provider && (
                <div className="text-xs text-blue-400 mb-2 font-mono flex items-center gap-1">
                  <Bot size={12} /> {msg.provider}
                </div>
              )}
              <div className="whitespace-pre-wrap leading-relaxed text-sm">{msg.content}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-start">
            <div className="bg-gray-800 border border-gray-700 rounded-2xl rounded-bl-none p-4 flex items-center gap-2 text-gray-400 text-sm">
              <Loader2 className="animate-spin text-blue-400" size={16} />
              Thinking...
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      <form onSubmit={sendMessage} className="p-4 bg-gray-800 border-t border-gray-700">
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t('chat.placeholder')}
            disabled={loading}
            className="w-full bg-gray-900 border border-gray-700 rounded-full py-3 pl-4 pr-12 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors disabled:opacity-50 text-sm text-gray-200 placeholder-gray-500"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 p-2 bg-blue-600 text-white rounded-full hover:bg-blue-505 transition-colors disabled:bg-gray-700 disabled:text-gray-500"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
