import React, { useState } from 'react';
import { Upload, Image as ImageIcon, MessageSquare, Shield, Download, ArrowRight, Eye, FileSearch } from 'lucide-react';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';

// Use the current origin in production (same domain), or localhost in dev
const API_BASE = import.meta.env.PROD ? window.location.origin : 'http://localhost:8000';

const handleAxiosError = async (e) => {
  console.error(e);
  if (e.response?.data instanceof Blob) {
    const text = await e.response.data.text();
    try {
      const json = JSON.parse(text);
      alert('Error: ' + (json.detail || 'Processing failed'));
    } catch (err) {
      alert('Error: ' + text);
    }
  } else {
    alert('Error: ' + (e.response?.data?.detail || 'Processing failed'));
  }
};

function App() {
  const [activeTab, setActiveTab] = useState('image-hide');
  const [loading, setLoading] = useState(false);
  const [resultImage, setResultImage] = useState(null);
  const [extractedText, setExtractedText] = useState('');

  const tabs = [
    { id: 'image-hide', label: 'Image Hiding', icon: ImageIcon },
    { id: 'image-reveal', label: 'Image Revealing', icon: Eye },
    { id: 'text-hide', label: 'Text Hiding', icon: MessageSquare },
    { id: 'text-extract', label: 'Text Extracting', icon: Shield },
  ];

  return (
    <div className="container">
      <header className="hero animate-in">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '15px', marginBottom: '15px', flexWrap: 'wrap' }}>
          <img src="/logo-saffron.png" alt="DeepSteganography AI Logo" style={{ width: '80px', height: '80px', borderRadius: '50%', border: '3px solid var(--border)', boxShadow: 'var(--shadow)' }} />
          <h1>DeepSteganography AI</h1>
        </div>
        <p style={{ color: 'var(--text-muted)', fontWeight: '500' }}>
          Advanced Steganography Powered by Deep Learning & Cryptography
        </p>
      </header>

      <div className="nav-tabs glass animate-in" style={{ margin: '0 auto 40px' }}>
        {tabs.map((tab) => (
          <div
            key={tab.id}
            className={`nav-tab ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => {
              setActiveTab(tab.id);
              setResultImage(null);
              setExtractedText('');
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <tab.icon size={18} />
              {tab.label}
            </div>
          </div>
        ))}
      </div>

      <main className="animate-in" style={{ animationDelay: '0.2s' }}>
        <AnimatePresence mode="wait">
          <motion.div
            key={activeTab}
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            exit={{ opacity: 0, x: -20 }}
            transition={{ duration: 0.3 }}
          >
            {activeTab === 'image-hide' && <ImageHiding setLoading={setLoading} setResultImage={setResultImage} />}
            {activeTab === 'image-reveal' && <ImageRevealing setLoading={setLoading} setResultImage={setResultImage} />}
            {activeTab === 'text-hide' && <TextHiding setLoading={setLoading} setResultImage={setResultImage} />}
            {activeTab === 'text-extract' && <TextExtracting setLoading={setLoading} setExtractedText={setExtractedText} />}
          </motion.div>
        </AnimatePresence>

        {loading && (
          <div className="glass card" style={{ padding: '40px', textAlign: 'center', marginTop: '40px' }}>
            <div className="spinner"></div>
            <p style={{ marginTop: '16px', color: 'var(--primary)', fontWeight: '700' }}>Processing... (~5-20s)</p>
          </div>
        )}

        {resultImage && (
          <div className="glass card animate-in" style={{ marginTop: '40px', textAlign: 'center' }}>
            <h3>Result Generated Successfully</h3>
            <img src={resultImage} className="preview-img" style={{ maxHeight: '400px', margin: '20px 0' }} alt="Result" />
            <br />
            <a href={resultImage} download="stegen_result.png" className="btn-primary" style={{ display: 'inline-flex' }}>
              <Download size={18} /> Download Result
            </a>
          </div>
        )}

        {extractedText && (
          <div className="glass card animate-in" style={{ marginTop: '40px' }}>
            <h3>Secret Message Extracted:</h3>
            <div style={{ padding: '20px', background: 'rgba(255,255,255,0.05)', borderRadius: '12px', marginTop: '16px', fontSize: '1.2rem', color: '#10b981' }}>
              {extractedText}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

function ImageHiding({ setLoading, setResultImage }) {
  const [cover, setCover] = useState(null);
  const [secret, setSecret] = useState(null);
  const [password, setPassword] = useState('');

  const handleSubmit = async () => {
    if (!cover || !secret) return alert('Please select both images');
    setLoading(true);
    setResultImage(null);
    const formData = new FormData();
    formData.append('cover', cover);
    formData.append('secret', secret);
    if (password) formData.append('password', password);
    try {
      const resp = await axios.post(`${API_BASE}/hide-image`, formData, { responseType: 'blob' });
      setResultImage(URL.createObjectURL(resp.data));
    } catch (e) {
      handleAxiosError(e);
    }
    setLoading(false);
  };

  return (
    <form className="grid" onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
      <div className="glass card">
        <label className="input-label">Cover Image (Image to hide into)</label>
        <FilePicker onFile={setCover} label="Upload Cover" preview={cover} />
      </div>
      <div className="glass card">
        <label className="input-label">Secret Image (Image to hide)</label>
        <FilePicker onFile={setSecret} label="Upload Secret" preview={secret} />
        <div className="input-group" style={{ marginTop: '20px' }}>
          <label className="input-label">Secret Password (Optional)</label>
          <input type="password" name="password" className="text-input" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Keep it secret" />
        </div>
      </div>
      <div style={{ gridColumn: '1 / -1', textAlign: 'center' }}>
        <button type="submit" className="btn-primary" style={{ width: '100%', maxWidth: '400px', margin: '0 auto' }}>
          Hide Image in Image <ArrowRight size={18} />
        </button>
      </div>
    </form>
  );
}

function ImageRevealing({ setLoading, setResultImage }) {
  const [stego, setStego] = useState(null);
  const [password, setPassword] = useState('');

  const handleSubmit = async () => {
    if (!stego) return alert('Please select a stego image');
    setLoading(true);
    setResultImage(null);
    const formData = new FormData();
    formData.append('stego', stego);
    if (password) formData.append('password', password);
    try {
      const resp = await axios.post(`${API_BASE}/reveal-image`, formData, { responseType: 'blob' });
      setResultImage(URL.createObjectURL(resp.data));
    } catch (e) {
      handleAxiosError(e);
    }
    setLoading(false);
  };

  return (
    <form className="glass card" style={{ maxWidth: '600px', margin: '0 auto' }} onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
      <label className="input-label">Stego Image (Image containing secret)</label>
      <FilePicker onFile={setStego} label="Upload Stego Image" preview={stego} />
      <div className="input-group" style={{ marginTop: '24px' }}>
        <label className="input-label">Password (Optional)</label>
        <input type="password" name="password" className="text-input" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter password if used" />
      </div>
      <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '24px' }}>
        Reveal Secret Image <Eye size={18} />
      </button>
    </form>
  );
}

function TextHiding({ setLoading, setResultImage }) {
  const [cover, setCover] = useState(null);
  const [text, setText] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async () => {
    if (!cover || !text || !password) return alert('Missing fields');
    setLoading(true);
    setResultImage(null);
    const formData = new FormData();
    formData.append('image', cover);
    formData.append('message', text);
    formData.append('password', password);
    try {
      const resp = await axios.post(`${API_BASE}/hide-text`, formData, { responseType: 'blob' });
      setResultImage(URL.createObjectURL(resp.data));
    } catch (e) {
      handleAxiosError(e);
    }
    setLoading(false);
  };

  return (
    <form className="grid" onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
      <div className="glass card">
        <label className="input-label">Cover Image</label>
        <FilePicker onFile={setCover} label="Upload Base Image" preview={cover} />
      </div>
      <div className="glass card" style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
        <div className="input-group">
          <label className="input-label">Secret Message</label>
          <textarea className="text-input" rows="4" value={text} onChange={(e) => setText(e.target.value)} placeholder="Type your message..."></textarea>
        </div>
        <div className="input-group">
          <label className="input-label">Encryption Password</label>
          <input type="password" name="password" className="text-input" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Keep it secret" />
        </div>
      </div>
      <div style={{ gridColumn: '1 / -1', textAlign: 'center' }}>
        <button type="submit" className="btn-primary" style={{ width: '100%', maxWidth: '400px', margin: '0 auto' }}>
          Hide Text in Image <ArrowRight size={18} />
        </button>
      </div>
    </form>
  );
}

function TextExtracting({ setLoading, setExtractedText }) {
  const [stego, setStego] = useState(null);
  const [password, setPassword] = useState('');

  const handleSubmit = async () => {
    if (!stego || !password) return alert('Missing fields');
    setLoading(true);
    setExtractedText('');
    const formData = new FormData();
    formData.append('image', stego);
    formData.append('password', password);
    try {
      const resp = await axios.post(`${API_BASE}/extract-text`, formData);
      setExtractedText(resp.data.message);
    } catch (e) {
      alert('Error: ' + (e.response?.data?.detail || 'Extraction failed. Wrong password?'));
    }
    setLoading(false);
  };

  return (
    <form className="glass card" style={{ maxWidth: '600px', margin: '0 auto' }} onSubmit={(e) => { e.preventDefault(); handleSubmit(); }}>
      <label className="input-label">Stego Image</label>
      <FilePicker onFile={setStego} label="Upload Stego Image" preview={stego} />
      <div className="input-group" style={{ marginTop: '24px' }}>
        <label className="input-label">Password</label>
        <input type="password" name="password" className="text-input" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter password" />
      </div>
      <button type="submit" className="btn-primary" style={{ width: '100%', marginTop: '20px' }}>
        Extract Message <Shield size={18} />
      </button>
    </form>
  );
}

function FilePicker({ onFile, label, preview }) {
  const [pURL, setPURL] = useState(null);

  const handleFile = (e) => {
    const f = e.target.files[0];
    if (f) {
      onFile(f);
      setPURL(URL.createObjectURL(f));
    }
  };

  return (
    <div className="upload-area" onClick={() => document.getElementById(label).click()}>
      <input type="file" id={label} hidden onChange={handleFile} accept="image/*" />
      {pURL ? (
        <img src={pURL} className="preview-img" alt="preview" />
      ) : (
        <>
          <Upload size={32} color="var(--primary)" />
          <span>{label}</span>
          <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)' }}>Drag & drop or click</span>
        </>
      )}
    </div>
  );
}

export default App;
