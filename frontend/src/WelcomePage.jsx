import React, { useState, useEffect } from 'react';
import { ArrowRight, Terminal as TerminalIcon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const TypingLine = ({ text, delay = 0, speed = 40, onComplete }) => {
  const [displayedText, setDisplayedText] = useState('');

  useEffect(() => {
    const startTimeout = setTimeout(() => {
      let currentText = '';
      const interval = setInterval(() => {
        if (currentText.length < text.length) {
          currentText = text.slice(0, currentText.length + 1);
          setDisplayedText(currentText);
        } else {
          clearInterval(interval);
          if (onComplete) onComplete();
        }
      }, speed);
    }, delay);

    return () => clearTimeout(startTimeout);
  }, [text, delay, speed, onComplete]);

  return <div>{displayedText}<span className={displayedText.length < text.length ? 'terminal-cursor' : ''}></span></div>;
};

const WelcomePage = ({ onEnter }) => {
  const [step, setStep] = useState(0);
  const [showButton, setShowButton] = useState(false);

  const lines = [
    { id: 0, text: "> Initializing Neural Pipeline...", delay: 500 },
    { id: 1, text: "> Synchronizing Entropy Gates...", delay: 300 },
    { id: 2, text: "> System Secure & Online.", delay: 300 },
  ];

  return (
    <div className="welcome-screen">
      <div className="terminal-card animate-in">
        <div className="terminal-wrap">
          <div className="terminal-head">
            <div className="terminal-title">
              <TerminalIcon size={16} color="#4ade80" />
              <span>DeepSteganography Core Initialization</span>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ff5f56' }}></div>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#ffbd2e' }}></div>
              <div style={{ width: '12px', height: '12px', borderRadius: '50%', background: '#27c93f' }}></div>
            </div>
          </div>
          <div className="terminal-body" style={{ minHeight: '180px' }}>
            <div className="terminal-pre" style={{ marginBottom: '15px' }}>
              <span className="terminal-code-prefix">$ </span>
              <TypingLine 
                text="npx init deepsteganography-ai" 
                speed={50} 
                onComplete={() => setStep(1)} 
              />
            </div>
            
            <div style={{ color: '#94a3b8', fontSize: '0.9rem', lineHeight: '1.6' }}>
              {step >= 1 && (
                <TypingLine 
                  text={lines[0].text} 
                  delay={lines[0].delay} 
                  onComplete={() => setStep(2)} 
                />
              )}
              {step >= 2 && (
                <TypingLine 
                  text={lines[1].text} 
                  delay={lines[1].delay} 
                  onComplete={() => setStep(3)} 
                />
              )}
              {step >= 3 && (
                <TypingLine 
                  text={lines[2].text} 
                  delay={lines[2].delay} 
                  onComplete={() => setShowButton(true)} 
                />
              )}
            </div>
          </div>
        </div>
      </div>

      <AnimatePresence>
        {showButton && (
          <motion.div 
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            className="welcome-btn"
          >
            <button onClick={onEnter} className="btn-primary" style={{ padding: '16px 40px', fontSize: '1.1rem' }}>
              Launch Secure Workspace <ArrowRight size={20} />
            </button>
          </motion.div>
        )}
      </AnimatePresence>

      <p style={{ marginTop: '20px', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
        Professional Grade Image & Text Steganography
      </p>
    </div>
  );
};

export default WelcomePage;
