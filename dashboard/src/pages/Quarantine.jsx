import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ShieldAlert, Edit3, Play } from 'lucide-react';
import CodeMirror from '@uiw/react-codemirror';
import { json } from '@codemirror/lang-json';
import { useHotkeys } from 'react-hotkeys-hook';

const fetchDlq = async () => {
  const res = await fetch('/api/dlq');
  if (!res.ok) throw new Error('Network response was not ok');
  return res.json();
};

const Quarantine = () => {
  const queryClient = useQueryClient();
  const { data: dlqItems = [], isLoading } = useQuery({ queryKey: ['dlq'], queryFn: fetchDlq });
  const [editingDlq, setEditingDlq] = useState(null);
  const [replayMessage, setReplayMessage] = useState("");

  const replayMutation = useMutation({
    mutationFn: async (item) => {
      const res = await fetch('/api/replay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: item.source, target: item.target, payload: item.payload })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Replay failed');
      }
      return res.json();
    },
    onSuccess: () => {
      setReplayMessage("Success: Payload accepted!");
      setEditingDlq(null);
      queryClient.invalidateQueries({ queryKey: ['dlq'] });
    },
    onError: (err) => {
      setReplayMessage(`Error: ${err.message}`);
    }
  });

  const handleReplay = (item) => {
    setReplayMessage("Replaying payload...");
    replayMutation.mutate(item);
  };

  useHotkeys('meta+enter, ctrl+enter', () => {
    if (editingDlq) {
      handleReplay(editingDlq);
    }
  }, { enableOnFormTags: true }, [editingDlq, handleReplay]);

  return (
    <div className="glass-panel p-8 max-w-5xl mx-auto animate-in slide-in-from-bottom-4 duration-300">
      <h2 className="text-2xl font-semibold mb-6 flex items-center gap-2">
        <ShieldAlert className="w-6 h-6 text-red-400" />
        Live Quarantine Room (DLQ)
      </h2>

      {replayMessage && (
        <div className={`mb-4 p-3 rounded text-sm ${replayMessage.includes('Error') ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'}`}>
          {replayMessage}
        </div>
      )}

      {isLoading ? (
        <div className="text-gray-400 animate-pulse">Loading quarantined payloads...</div>
      ) : (
        <div className="space-y-4">
          {dlqItems.length === 0 ? (
            <p className="text-gray-400">No quarantined payloads found. The system is secure.</p>
          ) : (
            dlqItems.map((item, idx) => (
              <div key={idx} className="bg-black/50 border border-red-500/30 rounded-lg p-4">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold text-red-400">{item.reason}</h3>
                    <p className="text-xs text-gray-500">{new Date(item.timestamp * 1000).toLocaleString()} | Source: {item.source} ➔ Target: {item.target}</p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => setEditingDlq({ ...item, idx })} className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded hover:bg-blue-500/30 flex items-center gap-1 text-sm transition-colors">
                      <Edit3 className="w-4 h-4" /> Edit
                    </button>
                    <button onClick={() => handleReplay(item)} disabled={replayMutation.isPending} className="px-3 py-1 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 flex items-center gap-1 text-sm transition-colors disabled:opacity-50">
                      <Play className="w-4 h-4" /> Replay
                    </button>
                  </div>
                </div>

                {editingDlq?.idx === idx ? (
                  <div className="border border-blue-500/50 rounded-md overflow-hidden">
                    <CodeMirror
                      value={editingDlq.payload}
                      height="200px"
                      theme="dark"
                      extensions={[json()]}
                      onChange={(value) => setEditingDlq({...editingDlq, payload: value})}
                    />
                  </div>
                ) : (
                  <pre className="bg-gray-900 p-3 rounded text-xs text-green-400 overflow-x-auto border border-white/5">
                    {item.payload}
                  </pre>
                )}

                {editingDlq?.idx === idx && (
                  <div className="mt-4 flex justify-between items-center">
                    <span className="text-xs text-gray-500">Tip: Press <kbd className="bg-gray-800 px-1 py-0.5 rounded">Cmd/Ctrl + Enter</kbd> to save & replay</span>
                    <button onClick={() => handleReplay(editingDlq)} disabled={replayMutation.isPending} className="px-4 py-1.5 bg-[#58a6ff] text-white rounded text-sm font-medium hover:bg-blue-600 transition-colors disabled:opacity-50">
                      Save & Replay
                    </button>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      )}
    </div>
  );
};

export default Quarantine;
