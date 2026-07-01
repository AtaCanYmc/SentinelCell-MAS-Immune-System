import React, { useState } from 'react';
import { Shield, Key, User, AlertCircle, Loader2 } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await fetch('/api/auth/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, password }),
      });

      if (!res.ok) {
        throw new Error('Invalid username or password');
      }

      // Successful login. The backend will set the HttpOnly cookie.
      // We can also store the username in localStorage to display it or keep auth state.
      localStorage.setItem('sentinel_username', username);

      // We also clean the legacy token in localStorage so we rely on cookies
      localStorage.removeItem('sentinel_api_key');

      navigate('/dashboard');
      window.location.reload();
    } catch (err) {
      setError(err.message || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-black/95 p-4 font-sans">
      <div className="max-w-md w-full bg-[#0d1117] border border-white/10 rounded-xl p-8 shadow-2xl relative overflow-hidden">
        {/* Decorative background glow */}
        <div className="absolute -top-40 -right-40 w-80 h-80 bg-blue-500/10 rounded-full blur-3xl pointer-events-none" />
        <div className="absolute -bottom-40 -left-40 w-80 h-80 bg-red-500/5 rounded-full blur-3xl pointer-events-none" />

        <div className="flex flex-col items-center mb-8 relative z-10">
          <div className="p-4 bg-blue-500/10 rounded-full border border-blue-500/20 mb-4">
            <Shield className="w-12 h-12 text-blue-400" />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-tight">SentinelCell Command</h2>
          <p className="text-xs text-gray-400 mt-1">Authenticate to access MAS Guardian Center</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5 relative z-10">
          {error && (
            <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-md flex items-center gap-3 text-red-400 text-xs">
              <AlertCircle className="w-4 h-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Username</label>
            <div className="relative">
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="text"
                required
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                className="w-full bg-black/50 border border-white/10 rounded-md py-3 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-xs font-bold text-gray-400 uppercase tracking-wider">Password</label>
            <div className="relative">
              <Key className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-500" />
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="w-full bg-black/50 border border-white/10 rounded-md py-3 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-blue-500 transition-colors"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-blue-600 hover:bg-blue-500 text-white font-medium rounded-md transition-colors disabled:opacity-50 flex items-center justify-center gap-2 cursor-pointer mt-6"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>Authenticating...</span>
              </>
            ) : (
              <span>Sign In</span>
            )}
          </button>
        </form>
      </div>
    </div>
  );
}
