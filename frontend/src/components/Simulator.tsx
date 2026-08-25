import React, { useState } from 'react';
import { Send, Shield, Bot, CheckCircle, XCircle, AlertTriangle, ArrowRight, CornerDownRight, CheckSquare, Sparkles, Terminal } from 'lucide-react';
import { apiClient } from '../api/client';
import { ChatResponse, DecisionType, SeverityType } from '../types';

export const Simulator: React.FC<{ onEventLogged?: () => void }> = ({ onEventLogged }) => {
  const [customerMessage, setCustomerMessage] = useState('I would like to request a refund of ₹3,000 for my order ORD-101.');
  const [customerId, setCustomerId] = useState('CUST-10');
  const [conversationId, setConversationId] = useState('CONV-501');
  const [isVerified, setIsVerified] = useState(true);
  const [managerApproved, setManagerApproved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [latestResponse, setLatestResponse] = useState<ChatResponse | null>(null);

  const presets = [
    {
      label: '🛑 ₹3,000 Refund (Blocked)',
      msg: 'I would like to request a refund of ₹3,000 for my order ORD-101.',
      verified: true,
      manager: false,
    },
    {
      label: '✅ ₹400 Refund (Allowed)',
      msg: 'Please issue a refund of ₹400 for my order ORD-202.',
      verified: true,
      manager: false,
    },
    {
      label: '👑 ₹3,000 Refund (Manager Approved)',
      msg: 'I need my ₹3,000 refund for ORD-101.',
      verified: true,
      manager: true,
    },
    {
      label: '💳 PII & Card Leakage (Blocked)',
      msg: 'Please charge my credit card 4532890123456789 or call 9876543210 for ORD-101.',
      verified: true,
      manager: false,
    },
    {
      label: '🔒 Unverified Order Lookup (Blocked)',
      msg: 'What is the delivery address and status for order ORD-101?',
      verified: false,
      manager: false,
    },
    {
      label: '📅 Delivery Date Promise (Remediated)',
      msg: 'When will my package arrive?',
      verified: true,
      manager: false,
    },
    {
      label: '🚨 Legal / Fraud Complaint (Escalated)',
      msg: 'This order is fraud and a scam! I am contacting my lawyer and police to sue you.',
      verified: true,
      manager: false,
    },
    {
      label: '📦 Cancel Order (Allowed)',
      msg: 'Please cancel order ORD-101 for me.',
      verified: true,
      manager: false,
    },
    {
      label: '🎁 Discount Claim (Allowed)',
      msg: 'Can you offer me a discount or coupon code for my order?',
      verified: true,
      manager: false,
    }
  ];

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!customerMessage.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.sendChatMessage({
        customer_message: customerMessage,
        customer_id: customerId,
        conversation_id: conversationId,
        is_verified: isVerified,
        manager_approved: managerApproved,
      });
      setLatestResponse(response);
      if (onEventLogged) onEventLogged();
    } catch (err: any) {
      setError(err.message || 'An error occurred during workflow execution.');
    } finally {
      setLoading(false);
    }
  };

  const getDecisionBadge = (decision: DecisionType) => {
    switch (decision) {
      case 'ALLOW':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center gap-1"><CheckCircle className="w-3.5 h-3.5" /> ALLOW</span>;
      case 'MODIFY':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center gap-1"><Sparkles className="w-3.5 h-3.5" /> MODIFY</span>;
      case 'BLOCK':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-rose-500/10 text-rose-400 border border-rose-500/30 flex items-center gap-1"><XCircle className="w-3.5 h-3.5" /> BLOCK</span>;
      case 'ESCALATE':
        return <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-purple-500/10 text-purple-400 border border-purple-500/30 flex items-center gap-1"><AlertTriangle className="w-3.5 h-3.5" /> ESCALATE</span>;
    }
  };

  const getSeverityBadge = (sev: SeverityType) => {
    switch (sev) {
      case 'CRITICAL':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-red-900/40 text-red-300 border border-red-700/50">CRITICAL</span>;
      case 'HIGH':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-rose-900/30 text-rose-300 border border-rose-700/40">HIGH</span>;
      case 'MEDIUM':
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-amber-900/30 text-amber-300 border border-amber-700/40">MEDIUM</span>;
      default:
        return <span className="px-2 py-0.5 rounded text-[11px] font-semibold bg-emerald-900/30 text-emerald-300 border border-emerald-700/40">LOW</span>;
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 py-8 space-y-8">
      {/* Top Banner / Description */}
      <div className="bg-slate-900/60 border border-slate-800 rounded-2xl p-6 shadow-xl">
        <h2 className="text-xl font-bold text-white flex items-center gap-2">
          <Bot className="w-5 h-5 text-indigo-400" />
          Interactive Multi-Agent Gateway Simulator
        </h2>
        <p className="text-sm text-slate-400 mt-1">
          Simulate customer messages and observe how PolicySentinel validates Agent A's proposals, enforces strict authorization envelopes, and blocks unauthorized tool calls.
        </p>

        {/* Scenario Presets */}
        <div className="mt-4 flex flex-wrap gap-2">
          <span className="text-xs text-slate-400 flex items-center mr-1">Quick Presets:</span>
          {presets.map((p, idx) => (
            <button
              key={idx}
              onClick={() => {
                setCustomerMessage(p.msg);
                setIsVerified(p.verified);
                setManagerApproved(p.manager);
              }}
              className="text-xs px-2.5 py-1.5 rounded-lg bg-slate-800/80 hover:bg-indigo-600/20 hover:border-indigo-500/40 text-slate-300 hover:text-indigo-300 border border-slate-700 transition"
            >
              {p.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        {/* Input Form Column */}
        <div className="lg:col-span-5 space-y-6">
          <form onSubmit={handleSend} className="bg-slate-900/90 border border-slate-800 rounded-2xl p-6 shadow-xl space-y-4">
            <h3 className="text-base font-semibold text-white flex items-center gap-2">
              <Terminal className="w-4 h-4 text-indigo-400" /> Customer Interaction Controls
            </h3>

            <div>
              <label className="block text-xs font-medium text-slate-300 mb-1">Customer Message</label>
              <textarea
                value={customerMessage}
                onChange={(e) => setCustomerMessage(e.target.value)}
                rows={4}
                className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3.5 py-2.5 text-sm text-slate-100 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500/50 focus:border-indigo-500"
                placeholder="Type customer message..."
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Customer ID</label>
                <input
                  type="text"
                  value={customerId}
                  onChange={(e) => setCustomerId(e.target.value)}
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-slate-300 mb-1">Conversation ID</label>
                <input
                  type="text"
                  value={conversationId}
                  onChange={(e) => setConversationId(e.target.value)}
                  className="w-full rounded-xl bg-slate-950 border border-slate-800 px-3 py-2 text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/50"
                />
              </div>
            </div>

            {/* Context Checkboxes */}
            <div className="bg-slate-950/60 border border-slate-800/80 rounded-xl p-3.5 space-y-2.5">
              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={isVerified}
                  onChange={(e) => setIsVerified(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700 focus:ring-indigo-500"
                />
                <span className="text-xs font-medium text-slate-200">Customer Identity Verified (2FA/OTP)</span>
              </label>

              <label className="flex items-center space-x-2.5 cursor-pointer">
                <input
                  type="checkbox"
                  checked={managerApproved}
                  onChange={(e) => setManagerApproved(e.target.checked)}
                  className="w-4 h-4 rounded text-indigo-600 bg-slate-900 border-slate-700 focus:ring-indigo-500"
                />
                <span className="text-xs font-medium text-slate-200">Manager Approval Granted (Testing Override)</span>
              </label>
            </div>

            {error && (
              <div className="p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2">
                <XCircle className="w-4 h-4 flex-shrink-0" />
                <span>{error}</span>
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 px-4 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 hover:from-indigo-500 hover:to-violet-500 text-white font-medium text-sm flex items-center justify-center gap-2 shadow-lg shadow-indigo-600/25 transition disabled:opacity-50"
            >
              {loading ? (
                <>
                  <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  <span>Evaluating Gateway Pipeline...</span>
                </>
              ) : (
                <>
                  <Send className="w-4 h-4" />
                  <span>Run PolicySentinel Pipeline</span>
                </>
              )}
            </button>
          </form>
        </div>

        {/* Pipeline Execution Trace Column */}
        <div className="lg:col-span-7 space-y-4">
          <h3 className="text-base font-semibold text-white flex items-center gap-2">
            <Shield className="w-4 h-4 text-indigo-400" /> Gateway Execution Trace
          </h3>

          {!latestResponse && !loading && (
            <div className="h-96 rounded-2xl border border-dashed border-slate-800 bg-slate-900/30 flex flex-col items-center justify-center text-slate-500 p-8 text-center">
              <Bot className="w-12 h-12 mb-3 text-slate-600" />
              <p className="text-sm font-medium text-slate-400">No interaction executed yet.</p>
              <p className="text-xs text-slate-500 max-w-sm mt-1">Select a preset or enter a message on the left and click "Run PolicySentinel Pipeline".</p>
            </div>
          )}

          {latestResponse && (
            <div className="space-y-4">
              {/* Step 1: Agent A Proposal */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-blue-400" /> Step 1: Agent A Output & Proposal
                  </span>
                  <span className="text-[11px] text-slate-500 mono">{latestResponse.request_id}</span>
                </div>
                <div className="bg-slate-950/70 rounded-lg p-3 text-xs text-slate-200 border border-slate-800/60">
                  <p className="font-semibold text-slate-400 mb-1">Generated Response:</p>
                  <p className="text-slate-100">{latestResponse.agent_a_response || 'None'}</p>
                  
                  {latestResponse.proposed_action ? (
                    <div className="mt-2 pt-2 border-t border-slate-800">
                      <span className="text-slate-400 font-semibold">Proposed Tool: </span>
                      <span className="text-amber-300 mono">{latestResponse.proposed_action.tool_name}</span>
                      <pre className="mt-1 text-[11px] text-slate-300 bg-slate-900/90 p-2 rounded border border-slate-800 mono">
                        {JSON.stringify(latestResponse.proposed_action.arguments, null, 2)}
                      </pre>
                    </div>
                  ) : (
                    <p className="mt-1 text-slate-500 italic">No business tool proposed.</p>
                  )}
                </div>
              </div>

              {/* Step 2: PolicySentinel Evaluation */}
              <div className={`rounded-xl p-4 border shadow-sm space-y-2 ${
                latestResponse.decision === 'ALLOW' ? 'bg-emerald-950/20 border-emerald-800/40' :
                latestResponse.decision === 'BLOCK' ? 'bg-rose-950/20 border-rose-800/40' :
                latestResponse.decision === 'MODIFY' ? 'bg-amber-950/20 border-amber-800/40' :
                'bg-purple-950/20 border-purple-800/40'
              }`}>
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-300 flex items-center gap-1.5">
                    <Shield className="w-3.5 h-3.5 text-indigo-400" /> Step 2: PolicySentinel Decision
                  </span>
                  <div className="flex items-center gap-2">
                    {getSeverityBadge(latestResponse.severity)}
                    {getDecisionBadge(latestResponse.decision)}
                  </div>
                </div>

                <div className="bg-slate-950/80 rounded-lg p-3 text-xs space-y-1.5 border border-slate-800/60">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Triggered Policy:</span>
                    <span className="mono font-semibold text-slate-200">{latestResponse.policy_id || 'NONE'} ({latestResponse.policy_version})</span>
                  </div>
                  <div>
                    <span className="text-slate-400">Gateway Reason:</span>
                    <p className="text-slate-200 mt-0.5">{latestResponse.reason}</p>
                  </div>
                  {latestResponse.evidence && Object.keys(latestResponse.evidence).length > 0 && (
                    <div>
                      <span className="text-slate-400">Evidence Collected:</span>
                      <pre className="mt-1 text-[11px] text-slate-300 bg-slate-900/90 p-2 rounded border border-slate-800 mono">
                        {JSON.stringify(latestResponse.evidence, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>

              {/* Step 3: Agent B & Tool Interceptor Security Gate */}
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-4 shadow-sm space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center gap-1.5">
                    <span className="w-2 h-2 rounded-full bg-violet-400" /> Step 3: Operations Agent B & Tool Interceptor
                  </span>
                  <span className={`text-xs px-2 py-0.5 rounded font-semibold ${
                    latestResponse.tool_executed
                      ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30'
                      : 'bg-rose-500/20 text-rose-400 border border-rose-500/30'
                  }`}>
                    {latestResponse.tool_executed ? 'Tool Executed: YES' : 'Tool Executed: BLOCKED'}
                  </span>
                </div>

                <div className="bg-slate-950/70 rounded-lg p-3 text-xs text-slate-200 border border-slate-800/60 space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-slate-400">Agent B Invoked:</span>
                    <span className={`font-semibold ${latestResponse.agent_b_called ? 'text-emerald-400' : 'text-slate-500'}`}>
                      {latestResponse.agent_b_called ? 'Yes (Authorized Envelope Received)' : 'No (Blocked at Gateway)'}
                    </span>
                  </div>

                  {latestResponse.approved_action && (
                    <div className="pt-2 border-t border-slate-800">
                      <span className="text-slate-400 font-semibold">Exact Authorization Envelope:</span>
                      <pre className="mt-1 text-[11px] text-emerald-300 bg-slate-900/90 p-2 rounded border border-slate-800 mono">
                        {JSON.stringify(latestResponse.approved_action, null, 2)}
                      </pre>
                    </div>
                  )}

                  {latestResponse.tool_result && (
                    <div className="pt-2 border-t border-slate-800">
                      <span className="text-slate-400 font-semibold">Mock Tool Output:</span>
                      <pre className="mt-1 text-[11px] text-slate-200 bg-slate-900/90 p-2 rounded border border-slate-800 mono">
                        {JSON.stringify(latestResponse.tool_result, null, 2)}
                      </pre>
                    </div>
                  )}
                </div>
              </div>

              {/* Step 4: Final Customer Safe Response */}
              <div className="bg-gradient-to-r from-slate-900 to-indigo-950/40 border border-indigo-900/40 rounded-xl p-4 shadow-sm space-y-2">
                <span className="text-xs font-semibold uppercase tracking-wider text-indigo-400 flex items-center gap-1.5">
                  <CheckSquare className="w-3.5 h-3.5" /> Step 4: Final Customer-Facing Message
                </span>
                <div className="bg-slate-950/80 rounded-lg p-3.5 text-sm text-slate-100 border border-indigo-500/20 font-medium">
                  {latestResponse.final_response}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
