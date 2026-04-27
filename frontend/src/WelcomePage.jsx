import React, { useState, useEffect, useRef } from 'react';
import { ArrowRight, Terminal as TerminalIcon } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

const WelcomePage = ({ onEnter }) => {
  const [lines, setLines] = useState([
    { text: '$ npx init deepsteganography-ai', typed: '', completed: false, isCommand: true },
    { text: '> Initializing Neural Pipeline...', typed: '', completed: false, isCommand: false },
    { text: '> Synchronizing Entropy Gates...', typed: '', completed: false, isCommand: false },
    { text: '> System Secure & Online.', typed: '', completed: false, isCommand: false },
  ]);
  const [currentLineIndex, setCurrentLineIndex] = useState(0);
  const [showButton, setShowButton] = useState(false);
  const timerRef = useRef(null);

  useEffect(() => {
    if (currentLineIndex >= lines.length) {
      setShowButton(true);
      return;
    }

    const currentLine = lines[currentLineIndex];
    let charIndex = 0;
    
    // Initial delay for the line to start
    const startDelay = currentLineIndex === 0 ? 500 : 300;
    
    timerRef.current = setTimeout(() => {
      const interval = setInterval(() => {
        if (charIndex < currentLine.text.length) {
          setLines(prev => {
            const next = [...prev];
            next[currentLineIndex].typed = currentLine.text.slice(0, charIndex + 1);
            return next;
          });
          charIndex++;
        } else {
          clearInterval(interval);
          setLines(prev => {
            const next = [...prev];
            next[currentLineIndex].completed = true;
            return next;
          });
          setCurrentLineIndex(prev => prev + 1);
        }
      }, 35); // Constant speed for smoothness
    }, startDelay);

    return () => {
      clearTimeout(timerRef.current);
    };
  }, [currentLineIndex]);

  return (
    <div className="welcome-screen">
      <div className="terminal-card animate-in">
        <div className="terminal-wrap" style={{ border: '1px solid var(--border)' }}>
          <div className="terminal-head" style={{ background: '#1e293b' }}>
            <div className="terminal-title">
              <TerminalIcon size={16} color="#4ade80" />
              <span style={{ color: '#f1f5f9' }}>Secure Core Deployment</span>
            </div>
            <div style={{ display: 'flex', gap: '6px' }}>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f43f5e' }}></div>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#f59e0b' }}></div>
              <div style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981' }}></div>
            </div>
          </div>
          <div className="terminal-body" style={{ minHeight: '200px', background: '#020617' }}>
            {lines.map((line, idx) => (
              <div key={idx} style={{ 
                marginBottom: line.isCommand ? '15px' : '8px',
                color: line.isCommand ? '#e2e8f0' : '#94a3b8',
                display: idx <= currentLineIndex ? 'block' : 'none',
                fontFamily: 'monospace',
                fontSize: '1rem'
              }}>
                <span style={{ color: line.isCommand ? 'var(--accent-2)' : 'inherit' }}>
                  {line.typed}
                </span>
                {idx === currentLineIndex && currentLineIndex < lines.length && (
                  <span className="terminal-cursor"></span>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div style={{ height: '80px', marginTop: '40px', display: 'flex', alignItems: 'center' }}>
        <AnimatePresence>
          {showButton && (
            <motion.div 
              initial={{ opacity: 0, scale: 0.9, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ type: 'spring', damping: 15 }}
            >
              <button 
                onClick={onEnter} 
                className="btn-primary" 
                style={{ padding: '16px 40px', fontSize: '1.1rem', boxShadow: '0 10px 30px rgba(212, 80, 10, 0.3)' }}
              >
                Launch Workspace <ArrowRight size={20} />
              </button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      <p style={{ marginTop: '20px', color: 'var(--text-muted)', fontSize: '0.9rem', opacity: 0.8 }}>
        Deep Neural Steganography & Encrypted Data Handling
      </p>
    </div>
  );
};

export default WelcomePage;
