import React from 'react';
import { useLocation } from 'react-router-dom';
import { Bell, ShieldCheck, Menu } from 'lucide-react';

const Navbar = ({ onMenuClick }) => {
  const location = useLocation();
  
  // Dynamic title mapping based on route path
  const getPageTitle = () => {
    switch (location.pathname) {
      case '/':
        return 'Dashboard Summary';
      case '/interaction':
        return 'Log HCP Interaction';
      default:
        return 'HCP Connect';
    }
  };

  const formattedDate = new Date().toLocaleDateString('en-US', {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  });

  return (
    <header className="h-16 px-4 md:px-6 border-b border-slate-200 dark:border-slate-800 bg-white/70 dark:bg-slate-900/70 backdrop-blur-md flex items-center justify-between transition-colors duration-300 z-10 sticky top-0">
      <div className="flex items-center gap-3">
        {/* Hamburger Menu toggle on Mobile screens */}
        <button 
          type="button"
          onClick={onMenuClick}
          className="p-2 -ml-2 rounded-lg hover:bg-slate-100 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 md:hidden"
          title="Toggle Navigation Menu"
        >
          <Menu className="w-5 h-5" />
        </button>
        <div>
          <h2 className="font-bold text-sm md:text-lg text-slate-800 dark:text-white leading-tight">{getPageTitle()}</h2>
          <p className="text-[10px] md:text-xs text-slate-400 dark:text-slate-500">{formattedDate}</p>
        </div>
      </div>

      <div className="flex items-center gap-2 md:gap-4">
        {/* Connection status tag */}
        <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 dark:bg-emerald-950/20 text-emerald-600 dark:text-emerald-400 border border-emerald-200/50 dark:border-emerald-950/30 text-[10px] md:text-xs font-semibold">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping"></span>
          <ShieldCheck className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">AI Engine Connected</span>
        </div>

        {/* Mock Action Notification bell */}
        <button className="p-2 rounded-lg border border-slate-200 dark:border-slate-800 hover:bg-slate-50 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 transition relative">
          <Bell className="w-4 h-4" />
          <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-sky-500"></span>
        </button>
      </div>
    </header>
  );
};

export default Navbar;
