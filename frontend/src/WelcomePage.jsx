import React from 'react';
import { ArrowRight, Terminal as TerminalIcon } from 'lucide-react';

const WelcomePage = ({ onEnter }) => {
  return (
    <div className="welcome-screen">
      <div className="terminal-card animate-in">
        <div className="terminal-wrap">
          <div className="terminal-head">
            <div className="terminal-title">
              <TerminalIcon size={16} color="#006adc" />
              <span>AI System Initialization</span>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f56' }}></div>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ffbd2e' }}></div>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#27c93f' }}></div>
            </div>
          </div>
          <div className="terminal-body">
            <div className="terminal-pre">
              <span className="terminal-code-prefix">$</span>
              <span className="terminal-code-cmd">npx init deepsteganography-ai</span>
              <span className="terminal-cursor"></span>
            </div>
            <div style={{ marginTop: '15px', color: 'var(--text-muted)', fontSize: '0.85rem', lineHeight: '1.4' }}>
              &gt; Loading Saffron Theme Engine... DONE<br />
              &gt; Synchronizing Neural Weights... DONE<br />
              &gt; Establishing Secure Gateway... READY
            </div>
          </div>
        </div>
      </div>

      <div className="welcome-btn">
        <button onClick={onEnter} className="btn-primary" style={{ padding: '16px 40px', fontSize: '1.1rem' }}>
          Enter DeepSteganography AI <ArrowRight size={20} />
        </button>
      </div>

      <p style={{ marginTop: '20px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        Secure. Deep. Private.
      </p>
    </div>
  );
};

export default WelcomePage;
