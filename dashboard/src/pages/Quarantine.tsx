import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { ShieldAlert, Edit3, Play, Loader2 } from 'lucide-react';
import CodeMirror from '@uiw/react-codemirror';
import { json } from '@codemirror/lang-json';
import { useHotkeys } from 'react-hotkeys-hook';
import ReactDiffViewer, { DiffMethod } from 'react-diff-viewer-continued';
import { fetchWithAuth } from '../hooks/api';
import { DlqItem } from '../types';

const fetchDlq = async () => {
  const res = await fetchWithAuth('/api/dlq');
  if (!res.ok) throw new Error('Network response was not ok');
  return res.json();
};

const Quarantine = () => {
  const queryClient = useQueryClient();
  const { data: rawDlqItems, isLoading } = useQuery({ queryKey: ['dlq'], queryFn: fetchDlq });
  const dlqItems = Array.isArray(rawDlqItems) ? rawDlqItems : [];

  const [editingDlq, setEditingDlq] = useState<DlqItem | null>(null);
  const [activeTab, setActiveTab] = useState('edit'); // 'edit' | 'diff'
  const [replayMessage, setReplayMessage] = useState("");
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 5;

  const totalPages = Math.max(1, Math.ceil(dlqItems.length / itemsPerPage));
  const currentItems = dlqItems.slice((currentPage - 1) * itemsPerPage, currentPage * itemsPerPage);

  const replayMutation = useMutation<any, Error, DlqItem>({
    mutationFn: async (item) => {
      let rawPayload = item.payload;
      if (typeof rawPayload !== 'string') {
        try {
          rawPayload = JSON.stringify(rawPayload);
        } catch (e) {
          rawPayload = String(rawPayload);
        }
      }
      const res = await fetchWithAuth('/api/dlq/replay', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ source: item.source, target: item.target, payload: rawPayload })
      });
      if (!res.ok) {
        const err = await res.json();
        throw new Error(err.detail || 'Replay failed');
      }
      return res.json();
    },
    onMutate: async (item) => {
      await queryClient.cancelQueries({ queryKey: ['dlq'] });
      const previousDlq = queryClient.getQueryData(['dlq']);
      queryClient.setQueryData(['dlq'], (old) => (Array.isArray(old) ? old.filter(i => i !== item) : []));
      return { previousDlq };
    },
    onSuccess: () => {
      setReplayMessage("Success: Payload accepted!");
      setEditingDlq(null);
    },
    onError: (err, item, context: any) => {
      setReplayMessage(`Error: ${err.message}`);
      queryClient.setQueryData(['dlq'], context?.previousDlq);
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['dlq'] });
    }
  });

  const handleReplay = (item: DlqItem) => {
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
            currentItems.map((item, idx) => (
              <div key={idx} className="bg-black/50 border border-red-500/30 rounded-lg p-4">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-semibold text-red-400">{item.reason}</h3>
                    <p className="text-xs text-gray-500">{new Date(item.timestamp * 1000).toLocaleString()} | Source: {item.source} ➔ Target: {item.target}</p>
                  </div>
                  <div className="flex gap-2">
                    <button onClick={() => setEditingDlq({ ...item, idx, payload: typeof item.payload === 'object' ? JSON.stringify(item.payload, null, 2) : item.payload })} className="px-3 py-1 bg-blue-500/20 text-blue-400 rounded hover:bg-blue-500/30 flex items-center gap-1 text-sm transition-colors">
                      <Edit3 className="w-4 h-4" /> Edit
                    </button>
                    <button onClick={() => handleReplay(item)} disabled={replayMutation.isPending} className="px-3 py-1 bg-green-500/20 text-green-400 rounded hover:bg-green-500/30 flex items-center gap-1 text-sm transition-colors disabled:opacity-50">
                      {replayMutation.isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : <Play className="w-4 h-4" />} Replay
                    </button>
                  </div>
                </div>

                {editingDlq?.idx === idx ? (
                  <div className="border border-blue-500/30 rounded-md overflow-hidden bg-black/50">
                    <div className="flex bg-gray-900 border-b border-white/10 text-xs font-semibold text-gray-300">
                      <button
                        onClick={() => setActiveTab('edit')}
                        className={`px-4 py-2 border-r border-white/5 transition-all ${
                          activeTab === 'edit'
                            ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-bold'
                            : 'text-gray-400 hover:text-gray-200'
                        }`}
                      >
                        Code Editor
                      </button>
                      <button
                        onClick={() => setActiveTab('diff')}
                        className={`px-4 py-2 border-r border-white/5 transition-all ${
                          activeTab === 'diff'
                            ? 'bg-[#58a6ff]/10 text-[#58a6ff] font-bold'
                            : 'text-gray-400 hover:text-gray-200'
                        }`}
                      >
                        Live Diff
                      </button>
                    </div>

                    {activeTab === 'diff' ? (
                      <ReactDiffViewer
                        oldValue={typeof item.payload === 'object' ? JSON.stringify(item.payload, null, 2) : item.payload}
                        newValue={editingDlq.payload}
                        splitView={true}
                        useDarkTheme={true}
                        compareMethod={DiffMethod.WORDS}
                        styles={{
                          variables: {
                            dark: {
                              diffViewerBackground: '#0d1117',
                              addedBackground: '#042A16',
                              addedColor: '#34d399',
                              removedBackground: '#3F121C',
                              removedColor: '#f87171',
                              wordAddedBackground: '#055d20',
                              wordRemovedBackground: '#7d1424'
                            }
                          }
                        }}
                      />
                    ) : (
                      <CodeMirror
                        value={editingDlq.payload}
                        height="220px"
                        theme="dark"
                        extensions={[json()]}
                        onChange={(value) => setEditingDlq({...editingDlq, payload: value})}
                      />
                    )}
                  </div>
                ) : (
                  <pre className="bg-[#0d1117] p-3 rounded text-xs text-gray-300 overflow-x-auto border border-white/5 whitespace-pre-wrap">
                    {typeof item.payload === 'object' ? JSON.stringify(item.payload, null, 2) : item.payload}
                  </pre>
                )}

                {editingDlq?.idx === idx && (
                  <div className="mt-4 flex justify-between items-center">
                    <span className="text-xs text-gray-500">Tip: Press <kbd className="bg-gray-800 px-1 py-0.5 rounded">Cmd/Ctrl + Enter</kbd> to save & replay</span>
                    <button onClick={() => handleReplay(editingDlq)} disabled={replayMutation.isPending} className="px-4 py-1.5 bg-[#58a6ff] hover:bg-blue-600 text-white rounded text-sm font-medium transition-colors disabled:opacity-50 flex items-center gap-1.5">
                      {replayMutation.isPending && <Loader2 className="w-4 h-4 animate-spin" />}
                      Save & Replay
                    </button>
                  </div>
                )}
              </div>
            ))
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-6 bg-black/40 p-4 rounded-lg border border-white/10">
              <div className="text-sm text-gray-400">
                Page {currentPage} of {totalPages} (Total {dlqItems.length})
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
                  disabled={currentPage === 1}
                  className="px-4 py-2 rounded-md bg-white/5 hover:bg-white/10 disabled:opacity-50 text-white transition-colors"
                >
                  Prev
                </button>
                <button
                  onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
                  disabled={currentPage === totalPages}
                  className="px-4 py-2 rounded-md bg-white/5 hover:bg-white/10 disabled:opacity-50 text-white transition-colors"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default Quarantine;
