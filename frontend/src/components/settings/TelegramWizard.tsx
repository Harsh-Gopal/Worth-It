import React, { useState, useEffect } from 'react';
import { Send, CheckCircle2, AlertCircle, Loader2, Trash2, Plus, User, Key, Bot } from 'lucide-react';
import { api } from '../../lib/api';
import type { TelegramRecipient } from '../../lib/types';

export default function TelegramWizard() {
  const [botConfigured, setBotConfigured] = useState(false);
  const [botInfo, setBotInfo] = useState<{username?: string, name?: string} | null>(null);
  const [botToken, setBotToken] = useState('');
  const [isVerifyingBot, setIsVerifyingBot] = useState(false);

  const [recipients, setRecipients] = useState<TelegramRecipient[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  
  const [chatId, setChatId] = useState('');
  const [name, setName] = useState('');
  const [type, setType] = useState('private');
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [testStatus, setTestStatus] = useState<Record<string, 'idle' | 'loading' | 'success' | 'error'>>({});
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      const [statusRes, botStatusRes] = await Promise.all([
        api.get('/telegram/status'),
        api.get('/telegram/bot/status')
      ]);
      setRecipients(statusRes.recipients || []);
      setBotConfigured(botStatusRes.configured || false);
      if (botStatusRes.configured) {
        setBotInfo({
          username: botStatusRes.bot_username,
          name: botStatusRes.bot_name
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfigureBot = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!botToken.trim()) return;

    setIsVerifyingBot(true);
    setError(null);
    try {
      const res = await api.post('/telegram/bot/configure', { bot_token: botToken.trim() });
      setBotConfigured(true);
      setBotInfo({ username: res.bot_username, name: res.bot_name });
      setBotToken('');
    } catch (err: any) {
      setError(err.message || 'Failed to verify bot token');
    } finally {
      setIsVerifyingBot(false);
    }
  };

  const handleRemoveBot = async () => {
    if (!confirm("Remove bot token? Notifications will stop working.")) return;
    try {
      await api.delete('/telegram/bot');
      setBotConfigured(false);
      setBotInfo(null);
    } catch (err: any) {
      setError(err.message || 'Failed to remove bot token');
    }
  };

  const handleAddRecipient = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatId.trim() || !name.trim()) return;
    
    setIsSubmitting(true);
    setError(null);
    try {
      const res = await api.post('/telegram/connect', { 
        chat_id: chatId.trim(),
        name: name.trim(),
        type
      });
      setRecipients(res.recipients);
      setChatId('');
      setName('');
    } catch (err: any) {
      setError(err.message || 'Failed to add recipient');
    } finally {
      setIsSubmitting(false);
    }
  };
  
  const handleRemoveRecipient = async (id: string) => {
    if (!confirm("Are you sure you want to remove this recipient?")) return;
    try {
      const res = await api.delete(`/telegram/connect/${id}`);
      setRecipients(res.recipients);
    } catch (err: any) {
      setError(err.message || 'Failed to remove recipient');
    }
  };

  const handleTest = async (id: string) => {
    setTestStatus(prev => ({ ...prev, [id]: 'loading' }));
    try {
      await api.post('/telegram/test', { chat_id: id });
      setTestStatus(prev => ({ ...prev, [id]: 'success' }));
      setTimeout(() => setTestStatus(prev => ({ ...prev, [id]: 'idle' })), 3000);
    } catch (err: any) {
      setTestStatus(prev => ({ ...prev, [id]: 'error' }));
      setError(err.message || 'Failed to send test message');
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center py-8">
        <Loader2 className="w-6 h-6 text-[var(--color-neon-green)] animate-spin" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Bot Configuration */}
      <div className="bg-[var(--color-radar-panel-light)] border border-[var(--color-radar-border)] rounded-xl overflow-hidden shadow-sm">
        <div className="px-6 py-4 border-b border-[var(--color-radar-border)] bg-[var(--color-radar-bg)] flex items-center justify-between">
          <div>
            <h3 className="font-bold text-white flex items-center gap-2"><Bot className="w-5 h-5 text-[var(--color-neon-green)]" /> Telegram Bot Setup</h3>
            <p className="text-sm text-[var(--color-text-muted)] mt-1 font-mono uppercase tracking-wider">Connect BotFather API Token</p>
          </div>
          {botConfigured && (
            <div className="px-3 py-1 bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 rounded text-xs font-bold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> CONNECTED
            </div>
          )}
        </div>
        
        <div className="p-6">
          {botConfigured ? (
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 p-4 border border-[var(--color-neon-green)]/30 rounded-xl bg-[var(--color-neon-green-glow)]">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-full bg-[var(--color-neon-green)]/20 text-[var(--color-neon-green)] flex items-center justify-center">
                  <Bot className="w-6 h-6" />
                </div>
                <div>
                  <h4 className="text-white font-bold">{botInfo?.name || 'Worth-It Bot'}</h4>
                  <p className="text-sm text-[var(--color-neon-green)]">@{botInfo?.username || 'unknown_bot'}</p>
                </div>
              </div>
              <button onClick={handleRemoveBot} className="text-xs font-bold px-4 py-2 rounded-lg border border-[var(--color-deal-trigger)] text-[var(--color-deal-trigger)] hover:bg-[var(--color-deal-trigger)]/10 transition-colors">
                Disconnect Bot
              </button>
            </div>
          ) : (
            <form onSubmit={handleConfigureBot}>
              <div className="mb-4">
                <label className="block text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Bot API Token</label>
                <div className="flex gap-2">
                  <div className="relative flex-1">
                    <Key className="w-4 h-4 text-[var(--color-text-muted)] absolute left-3 top-1/2 -translate-y-1/2" />
                    <input
                      type="password"
                      placeholder="1234567890:AAH_XXXXXXXX..."
                      value={botToken}
                      onChange={(e) => setBotToken(e.target.value)}
                      className="w-full bg-[var(--color-radar-bg)] border border-[var(--color-radar-border)] text-white text-sm rounded-lg focus:ring-1 focus:ring-[var(--color-neon-green)] focus:border-[var(--color-neon-green)] block pl-10 p-2.5 transition-all outline-none font-mono"
                      required
                    />
                  </div>
                  <button
                    type="submit"
                    disabled={isVerifyingBot || !botToken.trim()}
                    className="bg-[var(--color-neon-green)] text-black font-bold rounded-lg px-6 disabled:opacity-50 transition-all flex items-center gap-2 whitespace-nowrap shadow-[0_0_10px_var(--color-neon-green-glow)]"
                  >
                    {isVerifyingBot ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Verify & Connect'}
                  </button>
                </div>
                <p className="text-xs text-[var(--color-text-muted)] mt-2">Create a bot using <a href="https://t.me/BotFather" target="_blank" rel="noreferrer" className="text-[var(--color-neon-green)] hover:underline">@BotFather</a> and paste the API token here.</p>
              </div>
            </form>
          )}
        </div>
      </div>

      {/* Existing Recipients */}
      <div className={`bg-[var(--color-radar-panel-light)] border border-[var(--color-radar-border)] rounded-xl overflow-hidden shadow-sm transition-opacity duration-300 ${!botConfigured ? 'opacity-50 pointer-events-none' : ''}`}>
        <div className="px-6 py-4 border-b border-[var(--color-radar-border)] bg-[var(--color-radar-bg)]">
          <h3 className="font-bold text-white">Active Notification Endpoints</h3>
          <p className="text-sm text-[var(--color-text-muted)] mt-1 font-mono uppercase tracking-wider">Targets currently receiving deal alerts</p>
        </div>
        
        {recipients.length === 0 ? (
          <div className="p-8 text-center text-[var(--color-text-muted)] text-sm font-mono border-t border-[var(--color-radar-border)] bg-[var(--color-radar-bg)]">
            &gt; NO_ENDPOINTS_CONFIGURED
          </div>
        ) : (
          <ul className="divide-y divide-[var(--color-radar-border)]">
            {recipients.map((recipient) => (
              <li key={recipient.id} className="p-4 sm:px-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 hover:bg-[var(--color-radar-bg)] transition-colors">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 rounded-full bg-[var(--color-neon-green-glow)] text-[var(--color-neon-green)] flex items-center justify-center shrink-0 border border-[var(--color-neon-green)] shadow-[0_0_8px_var(--color-neon-green-glow)]">
                    <User className="w-5 h-5" />
                  </div>
                  <div>
                    <h4 className="text-sm font-bold text-white">{recipient.name}</h4>
                    <p className="text-xs text-[var(--color-text-muted)] font-mono mt-0.5"><span className="text-emerald-400 uppercase">{recipient.type}</span> // {recipient.id}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleTest(recipient.id)}
                    disabled={testStatus[recipient.id] === 'loading'}
                    className="flex-1 sm:flex-none text-xs font-bold px-4 py-2 rounded-lg border border-[var(--color-radar-border)] bg-[var(--color-radar-bg)] text-white hover:border-[var(--color-neon-green)] hover:text-[var(--color-neon-green)] transition-all flex items-center justify-center gap-1.5 disabled:opacity-50 min-w-[90px]"
                  >
                    {testStatus[recipient.id] === 'loading' ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : testStatus[recipient.id] === 'success' ? (
                      <CheckCircle2 className="w-3.5 h-3.5 text-[var(--color-neon-green)]" />
                    ) : (
                      <Send className="w-3.5 h-3.5" />
                    )}
                    {testStatus[recipient.id] === 'success' ? 'Verified!' : 'Ping'}
                  </button>
                  <button
                    onClick={() => handleRemoveRecipient(recipient.id)}
                    className="text-xs font-bold px-4 py-2 rounded-lg border border-[var(--color-radar-border)] bg-[var(--color-radar-bg)] text-[var(--color-text-muted)] hover:border-[var(--color-deal-trigger)] hover:text-[var(--color-deal-trigger)] transition-all flex items-center gap-1.5"
                  >
                    <Trash2 className="w-3.5 h-3.5" /> Delete
                  </button>
                </div>
              </li>
            ))}
          </ul>
        )}
      </div>

      {/* Add New Recipient Form */}
      <div className={`bg-[var(--color-radar-panel-light)] border border-[var(--color-radar-border)] rounded-xl overflow-hidden shadow-sm transition-opacity duration-300 ${!botConfigured ? 'opacity-50 pointer-events-none' : ''}`}>
        <div className="px-6 py-4 border-b border-[var(--color-radar-border)] bg-[var(--color-radar-bg)]">
          <h3 className="font-bold text-[var(--color-neon-green)] flex items-center gap-2">
            <Plus className="w-4 h-4" /> Add New Endpoint
          </h3>
        </div>
        
        <form onSubmit={handleAddRecipient} className="p-6">
          {!botConfigured && (
            <div className="mb-4 p-4 bg-[var(--color-radar-bg)] rounded-xl border border-[var(--color-deal-trigger)]/30">
              <p className="text-xs text-[var(--color-text-muted)] font-mono leading-relaxed">
                <span className="text-[var(--color-deal-trigger)] font-bold">&gt; BOT_NOT_CONFIGURED</span><br/>
                Please configure your Telegram Bot API token above before adding endpoints.
              </p>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-4">
            <div>
              <label className="block text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Display Name</label>
              <input
                type="text"
                placeholder="e.g. My Phone, Roommate Group"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full bg-[var(--color-radar-bg)] border border-[var(--color-radar-border)] text-white text-sm rounded-lg focus:ring-1 focus:ring-[var(--color-neon-green)] focus:border-[var(--color-neon-green)] block p-2.5 transition-all outline-none"
                required
                disabled={!botConfigured}
              />
            </div>
            <div>
              <label className="block text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-2">Chat ID</label>
              <input
                type="text"
                placeholder="e.g. 123456789 or -100987654321"
                value={chatId}
                onChange={(e) => setChatId(e.target.value)}
                className="w-full bg-[var(--color-radar-bg)] border border-[var(--color-radar-border)] text-white text-sm rounded-lg focus:ring-1 focus:ring-[var(--color-neon-green)] focus:border-[var(--color-neon-green)] block p-2.5 transition-all outline-none font-mono"
                required
                disabled={!botConfigured}
              />
            </div>
          </div>
          
          <div className="mb-6">
            <label className="block text-xs font-bold text-[var(--color-text-muted)] uppercase tracking-wider mb-3">Endpoint Type</label>
            <div className="flex gap-6">
              <label className="flex items-center gap-2 text-sm font-medium text-white cursor-pointer group">
                <input 
                  type="radio" 
                  name="type" 
                  value="private" 
                  checked={type === 'private'} 
                  onChange={(e) => setType(e.target.value)}
                  className="w-4 h-4 text-[var(--color-neon-green)] bg-[var(--color-radar-bg)] border-[var(--color-radar-border)] focus:ring-[var(--color-neon-green)] focus:ring-2" 
                  disabled={!botConfigured}
                /> 
                <span className="group-hover:text-[var(--color-neon-green)] transition-colors">Private User</span>
              </label>
              <label className="flex items-center gap-2 text-sm font-medium text-white cursor-pointer group">
                <input 
                  type="radio" 
                  name="type" 
                  value="group" 
                  checked={type === 'group'} 
                  onChange={(e) => setType(e.target.value)}
                  className="w-4 h-4 text-[var(--color-neon-green)] bg-[var(--color-radar-bg)] border-[var(--color-radar-border)] focus:ring-[var(--color-neon-green)] focus:ring-2" 
                  disabled={!botConfigured}
                /> 
                <span className="group-hover:text-[var(--color-neon-green)] transition-colors">Group Chat</span>
              </label>
            </div>
          </div>

          {error && (
            <div className="mb-4 p-3 text-sm text-[var(--color-deal-trigger)] bg-[var(--color-radar-bg)] rounded-lg flex gap-2 items-start border border-[var(--color-deal-trigger)]/50 shadow-[0_0_10px_rgba(255,59,59,0.1)]">
              <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
              <p>{error}</p>
            </div>
          )}

          <button
            type="submit"
            disabled={isSubmitting || !chatId.trim() || !name.trim() || !botConfigured}
            className="w-full sm:w-auto text-black bg-[var(--color-neon-green)] hover:bg-white focus:ring-4 focus:ring-[var(--color-neon-green-glow)] font-bold rounded-lg text-sm px-8 py-3 disabled:opacity-50 transition-all flex items-center justify-center gap-2 shadow-[0_0_15px_var(--color-neon-green-glow)]"
          >
            {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin" /> : 'Register Endpoint'}
          </button>
        </form>
      </div>
    </div>
  );
}
