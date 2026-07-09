import React, { useEffect, useState } from 'react';
import { NavLink, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { 
  LayoutDashboard, 
  PlusCircle, 
  LogOut, 
  Sun, 
  Moon, 
  Activity, 
  UserCheck 
} from 'lucide-react';
import { logout } from '../redux/authSlice';
import { resetForm, clearChatHistory } from '../redux/interactionSlice';

const Sidebar = () => {
  const dispatch = useDispatch();
  const navigate = useNavigate();
  const user = useSelector((state) => state.auth.user);
  const [darkMode, setDarkMode] = useState(
    localStorage.getItem('theme') === 'dark' || 
    (!('theme' in localStorage) && window.matchMedia('(prefers-color-scheme: dark)').matches)
  );

  useEffect(() => {
    if (darkMode) {
      document.body.classList.add('dark');
      localStorage.setItem('theme', 'dark');
    } else {
      document.body.classList.remove('dark');
      localStorage.setItem('theme', 'light');
    }
  }, [darkMode]);

  const handleLogout = () => {
    dispatch(logout());
    dispatch(resetForm());
    dispatch(clearChatHistory());
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Log HCP Interaction', path: '/interaction', icon: PlusCircle },
  ];

  return (
    <aside className="w-64 h-screen border-r border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 flex flex-col justify-between p-4 sticky top-0 transition-colors duration-300">
      <div>
        {/* Brand Logo & Name */}
        <div className="flex items-center gap-3 px-2 py-4 mb-6">
          <div className="gradient-bg w-9 h-9 rounded-lg flex items-center justify-center text-white font-bold text-lg shadow-md animate-pulse-subtle">
            +
          </div>
          <div>
            <h1 className="font-bold text-slate-800 dark:text-white leading-tight">HCP Connect</h1>
            <p className="text-xs text-sky-600 dark:text-sky-400 font-medium">AI-First Medical CRM</p>
          </div>
        </div>

        {/* Navigation List */}
        <nav className="space-y-1">
          {navItems.map((item) => {
            const Icon = item.icon;
            return (
              <NavLink
                key={item.path}
                to={item.path}
                className={({ isActive }) => 
                  `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                    isActive 
                      ? 'bg-sky-50 dark:bg-sky-950/40 text-sky-600 dark:text-sky-400' 
                      : 'text-slate-600 dark:text-slate-400 hover:bg-slate-50 dark:hover:bg-slate-800/60 hover:text-slate-900 dark:hover:text-white'
                  }`
                }
              >
                <Icon className="w-5 h-5" />
                {item.name}
              </NavLink>
            );
          })}
        </nav>
      </div>

      {/* Footer Profile & Controls */}
      <div className="space-y-4 pt-4 border-t border-slate-200 dark:border-slate-800">
        {/* User Info */}
        <div className="flex items-center gap-3 px-2">
          <div className="w-10 h-10 rounded-full bg-slate-100 dark:bg-slate-800 flex items-center justify-center font-bold text-slate-700 dark:text-slate-300 border border-slate-200 dark:border-slate-700">
            {user?.full_name ? user.full_name[0].toUpperCase() : 'U'}
          </div>
          <div className="overflow-hidden">
            <h4 className="font-semibold text-sm text-slate-800 dark:text-slate-200 truncate">{user?.full_name || 'Representative'}</h4>
            <p className="text-xs text-slate-500 truncate">{user?.email || 'sales@hcp.com'}</p>
          </div>
        </div>

        {/* Dark Mode and Logout */}
        <div className="flex gap-2">
          <button
            onClick={() => setDarkMode(!darkMode)}
            className="flex-1 flex items-center justify-center p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition"
            title="Toggle theme"
          >
            {darkMode ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </button>
          
          <button
            onClick={handleLogout}
            className="flex-1 flex items-center justify-center gap-1.5 p-2 rounded-lg bg-rose-50 hover:bg-rose-100 dark:bg-rose-950/20 dark:hover:bg-rose-950/30 text-rose-600 dark:text-rose-400 font-medium text-xs border border-rose-200/50 dark:border-rose-950/50 transition"
            title="Logout"
          >
            <LogOut className="w-4 h-4" />
            <span>Logout</span>
          </button>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
