import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useSelector, useDispatch } from "react-redux";
import { Mail, Lock, User, UserPlus, AlertCircle } from "lucide-react";
import {
  authStart,
  authSuccess,
  authFailure,
  clearError,
} from "../redux/authSlice";
import api from "../api";

const Register = () => {
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const dispatch = useDispatch();
  const navigate = useNavigate();

  const { loading, error, isAuthenticated } = useSelector(
    (state) => state.auth
  );

  useEffect(() => {
    dispatch(clearError());
  }, [dispatch]);

  useEffect(() => {
    if (isAuthenticated) {
      navigate("/", { replace: true });
    }
  }, [isAuthenticated, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!fullName || !email || !password) return;

    dispatch(authStart());

    try {
      // Register
      await api.post("/api/auth/register", {
        full_name: fullName,
        email,
        password,
      });

      // Automatically login
      const loginRes = await api.post("/api/auth/login", {
        email,
        password,
      });

      dispatch(
        authSuccess({
          token: loginRes.data.access_token,
          user: loginRes.data.user,
        })
      );

      navigate("/", { replace: true });
    } catch (err) {
      dispatch(
        authFailure(
          err.response?.data?.detail || "Registration failed."
        )
      );
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-900 p-4">
      <div className="w-full max-w-md bg-slate-800 rounded-2xl p-8 shadow-xl">

        <h2 className="text-2xl font-bold text-white text-center mb-6">
          Create Account
        </h2>

        {error && (
          <div className="mb-4 flex items-center gap-2 rounded-lg border border-red-500/20 bg-red-500/10 p-3 text-red-300">
            <AlertCircle className="w-4 h-4" />
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-5">

          <div className="relative">
            <User className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
            <input
              type="text"
              placeholder="Full Name"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 py-3 pl-10 pr-4 text-white"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              required
            />
          </div>

          <div className="relative">
            <Mail className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
            <input
              type="email"
              placeholder="Email"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 py-3 pl-10 pr-4 text-white"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>

          <div className="relative">
            <Lock className="absolute left-3 top-3.5 w-4 h-4 text-slate-500" />
            <input
              type="password"
              placeholder="Password"
              className="w-full rounded-lg border border-slate-700 bg-slate-900 py-3 pl-10 pr-4 text-white"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-sky-600 py-3 font-semibold text-white hover:bg-sky-500 disabled:opacity-50"
          >
            {loading ? (
              <span className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                Register
              </>
            )}
          </button>
        </form>

        <div className="mt-6 text-center text-slate-400">
          Already have an account?{" "}
          <Link
            to="/login"
            className="font-semibold text-sky-400 hover:text-sky-300"
          >
            Login
          </Link>
        </div>
      </div>
    </div>
  );
};

export default Register;