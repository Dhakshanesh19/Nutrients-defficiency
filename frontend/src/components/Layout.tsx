import React from 'react';
import { Link, Outlet, useNavigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { HeartPulse, LayoutDashboard, BrainCircuit, LogOut, User as UserIcon, UtensilsCrossed, FileText } from 'lucide-react';

export const Layout: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Predict Deficiency', path: '/predict', icon: BrainCircuit },
    { name: 'Food Log', path: '/food-log', icon: UtensilsCrossed },
    { name: 'Clinical Report', path: '/report', icon: FileText },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 bg-mesh overflow-hidden">
      {/* Sidebar Section */}
      <aside className="w-64 border-r border-slate-900 bg-slate-900/60 backdrop-blur-md flex flex-col">
        <div className="p-6 border-b border-slate-900 flex items-center gap-3">
          <HeartPulse className="h-8 w-8 text-emerald-400" />
          <span className="text-xl font-bold bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
            NutriAI
          </span>
        </div>
        
        <nav className="flex-1 p-4 space-y-2">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Link
                key={item.path}
                to={item.path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 ${
                  isActive
                    ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                    : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`}
              >
                <Icon className="h-5 w-5" />
                <span className="font-medium">{item.name}</span>
              </Link>
            );
          })}
        </nav>
        
        <div className="p-4 border-t border-slate-900">
          <div className="flex items-center gap-3 px-3 py-2 rounded-lg bg-slate-950/40 border border-slate-900 mb-3">
            <UserIcon className="h-5 w-5 text-emerald-400" />
            <div className="truncate">
              <p className="text-sm font-semibold text-slate-200">{user?.full_name || 'Demo User'}</p>
              <p className="text-xs text-slate-400 truncate">{user?.email || 'user@example.com'}</p>
            </div>
          </div>
          
          <button
            onClick={handleLogout}
            className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-rose-400 hover:bg-rose-500/10 transition-all duration-200"
          >
            <LogOut className="h-5 w-5" />
            <span className="font-medium">Logout</span>
          </button>
        </div>
      </aside>

      {/* Main Panel Content Area */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        <header className="h-16 border-b border-slate-900 flex items-center justify-between px-8 bg-slate-900/30 backdrop-blur-md">
          <h2 className="text-lg font-semibold text-slate-200">
            {location.pathname === '/' ? 'Dashboard' : location.pathname === '/food-log' ? 'Food Log' : location.pathname === '/report' ? 'Clinical Report' : 'Nutrition Deficiencies Forecast'}
          </h2>
          <div className="text-xs text-slate-400 flex items-center gap-2">
            <span className="inline-block h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
            Session Active
          </div>
        </header>
        
        <div className="p-8 max-w-7xl w-full mx-auto flex-1">
          <Outlet />
        </div>
      </main>
    </div>
  );
};
export default Layout;
