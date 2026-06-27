import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { Send, Bot, User, Loader2 } from 'lucide-react';

export default function ChatTest() {
  const { t } = useTranslation();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMsg = input.trim();
    setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
    setInput('');
    setLoading(true);

    try {
      const response = await fetch('/api/chat/test', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: userMsg })
      });

      const data = await response.json();

      if (response.ok && data.status === 'success') {
        setMessages(prev => [...prev, {
          role: 'bot',
          content: data.response,
          provider: data.provider
        }]);
      } else {
        setMessages(prev => [...prev, {
          role: 'error',
          content: data.detail || 'Error communicating with LLM'
        }]);
      }
    } catch (err) {
      setMessages(prev => [...prev, { role: 'error', content: err.toString() }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-[calc(100vh-100px)] max-w-4xl mx-auto bg-gray-900 border border-gray-800 rounded-xl overflow-hidden shadow-2xl">
      <div className="bg-gray-800 p-4 border-b border-gray-700 flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Bot className="text-blue-400" />
          {t('chat.title')}
        </h2>
      </div>

      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-[#0a0a0a]">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            {t('chat.title')}
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
              <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex items-start">
            <div className="bg-gray-800 border border-gray-700 rounded-2xl rounded-bl-none p-4 flex items-center gap-2 text-gray-400">
              <Loader2 className="animate-spin" size={16} />
              Thinking...
            </div>
          </div>
        )}
      </div>

      <form onSubmit={sendMessage} className="p-4 bg-gray-800 border-t border-gray-700">
        <div className="relative flex items-center">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder={t('chat.placeholder')}
            disabled={loading}
            className="w-full bg-gray-900 border border-gray-700 rounded-full py-3 pl-4 pr-12 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || loading}
            className="absolute right-2 p-2 bg-blue-600 text-white rounded-full hover:bg-blue-500 disabled:bg-gray-700 disabled:text-gray-500 transition-colors"
          >
            <Send size={18} />
          </button>
        </div>
      </form>
    </div>
  );
}
