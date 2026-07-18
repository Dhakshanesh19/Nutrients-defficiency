import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { HeartPulse, Key, Mail, AlertCircle } from 'lucide-react';
import { parseApiError } from '../services/api';

export const Login: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    
    try {
      await login(email, password);
      navigate('/');
    } catch (err: any) {
      console.error(err);
      setError(parseApiError(err));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center p-4 bg-mesh">
      <div className="w-full max-w-md">
        {/* App Logo */}
        <div className="flex justify-center items-center gap-3 mb-8">
          <HeartPulse className="h-10 w-10 text-emerald-400" />
          <span className="text-3xl font-extrabold bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
            NutriAI
          </span>
        </div>

        {/* Card */}
        <div className="glass-panel p-8 rounded-2xl shadow-xl w-full">
          <h2 className="text-2xl font-bold text-slate-100 mb-2">Welcome Back</h2>
          <p className="text-sm text-slate-400 mb-6">Sign in to monitor your nutritional deficiency risks.</p>

          {error && (
            <div className="mb-4 p-3 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-300 text-sm flex items-center gap-2">
              <AlertCircle className="h-5 w-5 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <div className="relative">
                <Mail className="absolute left-3 top-3 h-5 w-5 text-slate-500" />
                <input
                  type="email"
                  required
                  placeholder="name@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all duration-200"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative">
                <Key className="absolute left-3 top-3 h-5 w-5 text-slate-500" />
                <input
                  type="password"
                  required
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full pl-10 pr-4 py-2.5 rounded-lg bg-slate-900/80 border border-slate-800 text-slate-200 placeholder-slate-500 focus:outline-none focus:border-emerald-500 focus:ring-1 focus:ring-emerald-500 transition-all duration-200"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-slate-950 font-bold transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-emerald-500/10 mt-6"
            >
              {loading ? 'Signing In...' : 'Sign In'}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-800/80 text-center text-sm text-slate-400">
            Don't have an account?{' '}
            <Link to="/register" className="text-emerald-400 hover:text-emerald-300 font-semibold transition-colors">
              Sign Up
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Login;
