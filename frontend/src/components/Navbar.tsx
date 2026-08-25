import React from 'react';
import { Shield, Activity, FileText, AlertTriangle, Cpu } from 'lucide-react';

interface NavbarProps {
  activeTab: 'simulator' | 'audits' | 'incidents' | 'policies';
  setActiveTab: (tab: 'simulator' | 'audits' | 'incidents' | 'policies') => void;
  incidentCount?: number;
}

export const Navbar: React.FC<NavbarProps> = ({ activeTab, setActiveTab, incidentCount = 0 }) => {
  return (
    <header className="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
        {/* Brand */}
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-indigo-600 to-violet-500 flex items-center justify-center shadow-lg shadow-indigo-500/20">
            <Shield className="w-6 h-6 text-white" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <span className="font-bold text-lg text-white tracking-tight">PolicySentinel</span>
              <span className="text-xs px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-400 border border-indigo-500/20 font-medium">
                Gateway Active
              </span>
            </div>
            <p className="text-xs text-slate-400">AI Customer-Support Policy Enforcement</p>
          </div>
        </div>

        {/* Navigation Tabs */}
        <nav className="flex items-center space-x-1">
          <button
            onClick={() => setActiveTab('simulator')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'simulator'
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Activity className="w-4 h-4" />
            <span>Simulator</span>
          </button>

          <button
            onClick={() => setActiveTab('audits')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'audits'
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <FileText className="w-4 h-4" />
            <span>Audit History</span>
          </button>

          <button
            onClick={() => setActiveTab('incidents')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all relative ${
              activeTab === 'incidents'
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <AlertTriangle className="w-4 h-4" />
            <span>Incidents</span>
            {incidentCount > 0 && (
              <span className="w-5 h-5 rounded-full bg-rose-500 text-white text-xs flex items-center justify-center font-bold">
                {incidentCount}
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('policies')}
            className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
              activeTab === 'policies'
                ? 'bg-indigo-600/20 text-indigo-400 border border-indigo-500/30'
                : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
            }`}
          >
            <Cpu className="w-4 h-4" />
            <span>Policies</span>
          </button>
        </nav>
      </div>
    </header>
  );
};
