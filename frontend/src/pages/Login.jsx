import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { Mail, Lock, LogIn, AlertCircle } from 'lucide-react';
import { authStart, authSuccess, authFailure, clearError } from '../redux/authSlice';
import axios from '../api';

const Login = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const { loading, error, isAuthenticated } = useSelector((state) => state.auth);

  useEffect(() => {
    dispatch(clearError());
    if (isAuthenticated) {
      navigate('/');
    }
  }, [isAuthenticated, navigate, dispatch]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email || !password) return;

    dispatch(authStart());
    try {
      const response = await axios.post('/api/auth/login', { email, password });
      dispatch(authSuccess({
        token: response.data.access_token,
        user: response.data.user
      }));
      navigate('/');
    } catch (err) {
      dispatch(authFailure(err.response?.data?.detail || 'Authentication failed. Please verify credentials.'));
    }
  };

  return (
    <div className="min-h-screen w-full flex items-center justify-center bg-slate-900 font-sans p-4 relative overflow-hidden">
      {/* Dynamic Background Gradients */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 rounded-full bg-sky-600/20 blur-3xl animate-pulse-subtle pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 rounded-full bg-teal-600/20 blur-3xl animate-pulse-subtle pointer-events-none"></div>

      <div className="w-full max-w-md bg-slate-800/80 border border-slate-700/50 rounded-2xl p-8 backdrop-blur-xl shadow-2xl z-10">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-12 h-12 rounded-xl gradient-bg flex items-center justify-center text-white font-bold text-2xl mx-auto mb-4 shadow-lg shadow-sky-500/20">
            +
          </div>
          <h2 className="text-2xl font-bold text-white">Welcome back</h2>
          <p className="text-slate-400 text-sm mt-2">Sign in to your Healthcare CRM account</p>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="flex items-center gap-2 bg-rose-500/10 border border-rose-500/20 text-rose-300 p-3 rounded-lg text-sm mb-6">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} className="space-y-5">
          <div>
            <label className="block text-slate-300 text-xs font-semibold uppercase tracking-wider mb-2">Email Address</label>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="sales@hcp-crm.com"
                className="w-full pl-10 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-slate-300 text-xs font-semibold uppercase tracking-wider mb-2">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-500" />
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full pl-10 pr-4 py-3 bg-slate-900 border border-slate-700 rounded-lg text-slate-100 placeholder-slate-500 focus:outline-none focus:border-sky-500 transition"
                required
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 bg-sky-600 hover:bg-sky-500 text-white font-semibold rounded-lg shadow-lg hover:shadow-sky-500/20 flex items-center justify-center gap-2 transition disabled:opacity-50"
          >
            {loading ? (
              <span className="w-5 h-5 rounded-full border-2 border-white border-t-transparent animate-spin"></span>
            ) : (
              <>
                <LogIn className="w-4 h-4" />
                <span>Sign In</span>
              </>
            )}
          </button>
        </form>

        {/* Register redirection */}
        <div className="text-center mt-6 text-slate-400 text-sm">
          Don't have an account?{' '}
          <Link to="/register" className="text-sky-400 hover:text-sky-300 font-semibold underline transition">
            Register here
          </Link>
        </div>

       {/* User Information */}
<div className="mt-8 p-3.5 bg-slate-900/60 border border-slate-700/30 rounded-lg text-xs text-slate-400">
  <p className="font-semibold text-slate-300 mb-1">
    Getting Started
  </p>
  <p>
    If you're using the application for the first time, click
    <span className="text-sky-400 font-semibold"> Register</span> to create your account.
  </p>
  <p className="mt-1">
    After registration, sign in using your registered email address and password.
  </p>
</div>
      </div>
    </div>
  );
};

export default Login;
