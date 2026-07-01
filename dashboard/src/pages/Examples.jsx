import React, { useState, useEffect, useRef } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Play, Square, Terminal, CheckCircle, AlertCircle, Loader2, RefreshCw, Search, Code, Cpu } from 'lucide-react';
import { useTranslation } from 'react-i18next';

const fetchExamples = async () => {
  const res = await fetch('/api/examples');
  if (!res.ok) throw new Error('Failed to fetch examples');
  return res.json();
};

const fetchConfig = async () => {
  const res = await fetch('/api/config');
  if (!res.ok) return {};
  return res.json();
};

const Examples = () => {
  const { t } = useTranslation();
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['examples'],
    queryFn: fetchExamples,
  });
  const { data: config = {} } = useQuery({ queryKey: ['config'], queryFn: fetchConfig, refetchInterval: 30000 });

  const [selectedExample, setSelectedExample] = useState(null);
  const [consoleLogs, setConsoleLogs] = useState([]);
  const [executionState, setExecutionState] = useState('IDLE'); // IDLE, RUNNING, SUCCESS, FAILED
  const [exitCode, setExitCode] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');

  const wsRef = useRef(null);
  const consoleEndRef = useRef(null);

  // Auto-scroll console to bottom
  useEffect(() => {
    if (consoleEndRef.current) {
      consoleEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [consoleLogs]);

  // Cleanup websocket on unmount
  useEffect(() => {
    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const runExample = (example) => {
    if (executionState === 'RUNNING') return;

    setSelectedExample(example);
    setConsoleLogs([`[System] Launching ${example.name} (${example.id})...`]);
    setExecutionState('RUNNING');
    setExitCode(null);

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const tokenParam = config.API_KEY_SECRET ? `?token=${config.API_KEY_SECRET}` : '';
    const wsUrl = `${protocol}//${window.location.host}/ws/examples/run/${example.id}${tokenParam}`;

    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'stdout') {
          setConsoleLogs((prev) => [...prev, msg.line]);
        } else if (msg.type === 'exit') {
          setExitCode(msg.code);
          setExecutionState(msg.code === 0 ? 'SUCCESS' : 'FAILED');
        } else if (msg.type === 'error') {
          setConsoleLogs((prev) => [...prev, `[Error] ${msg.line}`]);
          setExecutionState('FAILED');
        }
      } catch (err) {
        setConsoleLogs((prev) => [...prev, event.data]);
      }
    };

    ws.onerror = (err) => {
      setConsoleLogs((prev) => [...prev, '[Connection Error] Failed to establish communication stream.']);
      setExecutionState('FAILED');
    };

    ws.onclose = () => {
      wsRef.current = null;
    };
  };

  const stopExample = () => {
    if (wsRef.current) {
      wsRef.current.close();
      setConsoleLogs((prev) => [...prev, '[System] Process terminated by user request.']);
      setExecutionState('IDLE');
    }
  };

  const getDifficultyColor = (difficulty) => {
    switch (difficulty?.toLowerCase()) {
      case 'easy':
        return 'bg-green-500/10 text-green-400 border-green-500/20';
      case 'medium':
        return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
      case 'hard':
        return 'bg-red-500/10 text-red-400 border-red-500/20';
      default:
        return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    }
  };

  const filteredExamples = data?.examples?.filter((ex) =>
    ex.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ex.description.toLowerCase().includes(searchTerm.toLowerCase()) ||
    ex.category.toLowerCase().includes(searchTerm.toLowerCase())
  ) || [];

  return (
    <div className="animate-in fade-in duration-300">
      <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold flex items-center gap-2">
            <Cpu className="w-6 h-6 text-[#58a6ff]" />
            {t('sidebar.examples')}
          </h1>
          <p className="text-sm text-gray-400 mt-1">
            Run, monitor, and observe real-time agent healing and security protocols directly on the live dashboard.
          </p>
        </div>

        <div className="flex w-full lg:w-auto gap-3 items-center">
          <div className="relative flex-1 lg:w-64">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-gray-500" />
            <input
              type="text"
              placeholder="Search simulations..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full bg-black/50 border border-white/10 rounded-md py-2 pl-9 pr-4 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-blue-500 transition-colors"
            />
          </div>
          <button
            onClick={() => refetch()}
            className="p-2 hover:bg-white/10 rounded-md border border-white/5 transition-colors"
            title="Refresh Examples"
          >
            <RefreshCw className="w-4 h-4 text-gray-400" />
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Examples List */}
        <div className="lg:col-span-2 space-y-4 max-h-[70vh] overflow-y-auto pr-2">
          {isLoading ? (
            <div className="flex flex-col items-center justify-center py-20 glass-panel">
              <Loader2 className="w-8 h-8 text-blue-400 animate-spin mb-4" />
              <span className="text-sm text-gray-400">Loading simulations...</span>
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center py-20 glass-panel border-red-500/20">
              <AlertCircle className="w-8 h-8 text-red-400 mb-4" />
              <span className="text-sm text-red-400 font-semibold">Error loading simulations</span>
              <p className="text-xs text-gray-500 mt-1">{error.message}</p>
            </div>
          ) : filteredExamples.length === 0 ? (
            <div className="text-center py-20 glass-panel">
              <p className="text-gray-400 text-sm">No matching simulations found.</p>
            </div>
          ) : (
            filteredExamples.map((example) => (
              <div
                key={example.id}
                className={`glass-panel p-5 transition-all border ${
                  selectedExample?.id === example.id && executionState === 'RUNNING'
                    ? 'border-blue-500/50 shadow-[0_0_15px_rgba(59,130,246,0.1)]'
                    : 'border-white/5 hover:border-white/15'
                }`}
              >
                <div className="flex justify-between items-start gap-4 mb-2">
                  <div className="flex items-center gap-3">
                    <Code className="w-5 h-5 text-gray-400" />
                    <h3 className="font-semibold text-gray-200">{example.name}</h3>
                  </div>
                  <div className="flex gap-2">
                    <span className="px-2 py-0.5 text-2xs rounded-full bg-blue-500/10 text-blue-400 border border-blue-500/20 font-medium">
                      {example.category}
                    </span>
                    <span className={`px-2 py-0.5 text-2xs rounded-full border font-medium ${getDifficultyColor(example.difficulty)}`}>
                      {example.difficulty}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-400 mb-4 font-normal">{example.description}</p>
                <div className="flex justify-between items-center">
                  <span className="font-mono text-xs text-gray-500">{example.id}</span>
                  <button
                    onClick={() => runExample(example)}
                    disabled={executionState === 'RUNNING'}
                    className={`flex items-center gap-2 px-4 py-1.5 rounded text-xs font-semibold tracking-wider transition-all ${
                      executionState === 'RUNNING'
                        ? 'bg-gray-800 text-gray-500 cursor-not-allowed border border-white/5'
                        : 'bg-[#58a6ff]/10 hover:bg-[#58a6ff]/20 text-[#58a6ff] border border-[#58a6ff]/30'
                    }`}
                  >
                    <Play className="w-3.5 h-3.5" />
                    RUN SIMULATION
                  </button>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Real-time Terminal Monitor */}
        <div className="glass-panel p-6 flex flex-col h-[70vh] border border-white/10">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Terminal className="w-5 h-5 text-green-400" />
              Terminal Monitor
            </h2>
            <div className="flex items-center gap-2">
              {executionState === 'RUNNING' ? (
                <>
                  <span className="flex h-2 w-2 relative">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-blue-500"></span>
                  </span>
                  <span className="text-xs text-blue-400 font-bold">RUNNING</span>
                  <button
                    onClick={stopExample}
                    className="p-1 hover:bg-red-500/20 rounded border border-red-500/30 transition-colors ml-2"
                    title="Stop Process"
                  >
                    <Square className="w-3.5 h-3.5 text-red-500 fill-red-500" />
                  </button>
                </>
              ) : executionState === 'SUCCESS' ? (
                <div className="flex items-center gap-1.5 text-xs text-green-400 font-bold">
                  <CheckCircle className="w-4 h-4" />
                  EXITED (0)
                </div>
              ) : executionState === 'FAILED' ? (
                <div className="flex items-center gap-1.5 text-xs text-red-400 font-bold">
                  <AlertCircle className="w-4 h-4" />
                  FAILED ({exitCode !== null ? exitCode : 'ERR'})
                </div>
              ) : (
                <span className="text-xs text-gray-500 font-medium">STANDBY</span>
              )}
            </div>
          </div>

          <div className="flex-1 overflow-y-auto bg-[#090d13] border border-white/5 rounded-md p-4 font-mono text-xs text-gray-300 space-y-1 scrollbar-thin select-text">
            {consoleLogs.length === 0 ? (
              <div className="text-gray-600 italic">Select and run a simulation example to observe active processes...</div>
            ) : (
              consoleLogs.map((line, i) => {
                let colorClass = "text-gray-300";
                if (line.startsWith('[System]')) colorClass = "text-blue-400 font-semibold";
                else if (line.startsWith('[Error]')) colorClass = "text-red-400 font-semibold";
                else if (line.startsWith('[Connection Error]')) colorClass = "text-red-500 font-bold";
                else if (line.toLowerCase().includes('successfully') || line.toLowerCase().includes('healed')) colorClass = "text-green-400";
                else if (line.toLowerCase().includes('security_breach') || line.toLowerCase().includes('dropped')) colorClass = "text-red-400 font-semibold";
                else if (line.toLowerCase().includes('warning') || line.toLowerCase().includes('quarantine')) colorClass = "text-yellow-400";

                return (
                  <div key={i} className={`${colorClass} break-all whitespace-pre-wrap`}>
                    {line}
                  </div>
                );
              })
            )}
            <div ref={consoleEndRef} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Examples;
