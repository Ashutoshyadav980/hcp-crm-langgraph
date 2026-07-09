import React, { useState, useEffect, useRef } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { 
  Lock, 
  Send, 
  Sparkles, 
  RefreshCw, 
  User, 
  Calendar, 
  Clock, 
  Users, 
  Smile, 
  Meh, 
  Frown,
  Mic,
  Search,
  Plus,
  Trash2,
  Paperclip,
  CheckCircle,
  Play
} from 'lucide-react';
import { 
  setFormFields, 
  syncFormFromExtracted, 
  resetForm, 
  addChatMessage, 
  setChatLoading, 
  setError,
  clearChatHistory 
} from '../redux/interactionSlice';
import axios from '../api';

const InteractionModule = () => {
  const dispatch = useDispatch();
  const chatEndRef = useRef(null);
  const chatInputRef = useRef(null);

  // Redux state selectors
  const { 
    activeForm, 
    chatHistory, 
    chatLoading, 
    error 
  } = useSelector((state) => state.interaction);

  // Local UI states
  const [userInput, setUserInput] = useState('');
  const [hcpsList, setHcpsList] = useState([]);
  const [showHcpDropdown, setShowHcpDropdown] = useState(false);
  const [hcpSearchVal, setHcpSearchVal] = useState('');
  
  // Materials and Samples adding UI state
  const [showMaterialInput, setShowMaterialInput] = useState(false);
  const [newMaterialName, setNewMaterialName] = useState('');
  
  const [showSampleInput, setShowSampleInput] = useState(false);
  const [newSampleName, setNewSampleName] = useState('');
  const [newSampleQty, setNewSampleQty] = useState(1);

  // Attendees list state (local sync to notes if needed, or managed locally)
  const [attendees, setAttendees] = useState([]);
  const [newAttendeeName, setNewAttendeeName] = useState('');
  const [showAttendeeInput, setShowAttendeeInput] = useState(false);

  // Fetch HCP list on mount
  useEffect(() => {
    const fetchHcps = async () => {
      try {
        const res = await axios.get('/api/hcps');
        setHcpsList(res.data);
      } catch (err) {
        console.error("Failed to load HCPs:", err);
      }
    };
    fetchHcps();
  }, []);

  // Update local search text when activeForm.hcp_name changes (e.g. from AI)
  useEffect(() => {
    if (activeForm.hcp_name) {
      setHcpSearchVal(activeForm.hcp_name);
    } else {
      setHcpSearchVal('');
    }
  }, [activeForm.hcp_name]);

  // Auto-scroll disabled per UX criteria to prevent unwanted page jumps

  // Sync manual form field changes directly to Redux and debounced to Backend
  const handleFieldChange = async (fieldName, value) => {
    const updatedForm = { ...activeForm, [fieldName]: value };
    dispatch(setFormFields({ [fieldName]: value }));

    // If an interaction ID is loaded, write updates to database to keep AI synced
    if (activeForm.id) {
      try {
        await axios.put(`/api/interactions/${activeForm.id}`, {
          hcp_id: updatedForm.hcp_id || 1, 
          type: updatedForm.type,
          date: updatedForm.date,
          time: updatedForm.time,
          topics_discussed: updatedForm.topics_discussed,
          materials_shared: updatedForm.materials_shared,
          sentiment: updatedForm.sentiment,
          notes: updatedForm.notes,
          summary: updatedForm.summary,
          follow_up_date: updatedForm.follow_up_date || null
        });
      } catch (err) {
        console.error("Failed to sync manual edit to database:", err);
      }
    }
  };

  // Helper to parse comma-separated materials and samples from DB string
  const parseMaterialsAndSamples = (str) => {
    const materials = [];
    const samples = [];
    if (!str) return { materials, samples };

    const items = str.split(',').map(i => i.trim()).filter(Boolean);
    items.forEach(item => {
      // e.g. "10 samples" or "5 CardioPlus samples"
      const match = item.match(/^(\d+)\s+(.+)$/);
      if (match) {
        samples.push({ quantity: parseInt(match[1], 10), name: match[2] });
      } else {
        materials.push(item);
      }
    });
    return { materials, samples };
  };

  // Helper to serialize materials and samples list back to DB string
  const serializeMaterialsAndSamples = (materials, samples) => {
    const items = [...materials];
    samples.forEach(s => {
      items.push(`${s.quantity} ${s.name}`);
    });
    return items.join(', ');
  };

  const handleAddMaterial = () => {
    if (!newMaterialName.trim()) return;
    const { materials, samples } = parseMaterialsAndSamples(activeForm.materials_shared);
    if (!materials.includes(newMaterialName.trim())) {
      const updatedMaterials = [...materials, newMaterialName.trim()];
      const serialized = serializeMaterialsAndSamples(updatedMaterials, samples);
      handleFieldChange('materials_shared', serialized);
    }
    setNewMaterialName('');
    setShowMaterialInput(false);
  };

  const handleRemoveMaterial = (name) => {
    const { materials, samples } = parseMaterialsAndSamples(activeForm.materials_shared);
    const updatedMaterials = materials.filter(m => m !== name);
    const serialized = serializeMaterialsAndSamples(updatedMaterials, samples);
    handleFieldChange('materials_shared', serialized);
  };

  const handleAddSample = () => {
    if (!newSampleName.trim() || newSampleQty <= 0) return;
    const { materials, samples } = parseMaterialsAndSamples(activeForm.materials_shared);
    const updatedSamples = [...samples, { name: newSampleName.trim(), quantity: newSampleQty }];
    const serialized = serializeMaterialsAndSamples(materials, updatedSamples);
    handleFieldChange('materials_shared', serialized);
    setNewSampleName('');
    setNewSampleQty(1);
    setShowSampleInput(false);
  };

  const handleRemoveSample = (index) => {
    const { materials, samples } = parseMaterialsAndSamples(activeForm.materials_shared);
    const updatedSamples = samples.filter((_, idx) => idx !== index);
    const serialized = serializeMaterialsAndSamples(materials, updatedSamples);
    handleFieldChange('materials_shared', serialized);
  };

  const handleSelectHcp = (hcp) => {
    setHcpSearchVal(hcp.name);
    handleFieldChange('hcp_id', hcp.id);
    handleFieldChange('hcp_name', hcp.name);
    handleFieldChange('hospital', hcp.hospital || '');
    handleFieldChange('specialty', hcp.specialty || '');
    setShowHcpDropdown(false);
  };

  const handleCreateHcp = async () => {
    if (!hcpSearchVal.trim()) return;
    try {
      const res = await axios.post('/api/hcps', {
        name: hcpSearchVal.trim(),
        hospital: 'Apollo Hospital',
        specialty: 'General Medicine',
        phone: '123-456-7890',
        email: 'doctor@hospital.com'
      });
      const newHcp = res.data;
      setHcpsList(prev => [...prev, newHcp]);
      handleSelectHcp(newHcp);
    } catch (err) {
      console.error("Failed to create HCP:", err);
    }
  };

  const handleAddAttendee = () => {
    if (!newAttendeeName.trim()) return;
    if (!attendees.includes(newAttendeeName.trim())) {
      const updatedAttendees = [...attendees, newAttendeeName.trim()];
      setAttendees(updatedAttendees);
    }
    setNewAttendeeName('');
    setShowAttendeeInput(false);
  };

  const handleRemoveAttendee = (name) => {
    setAttendees(prev => prev.filter(a => a !== name));
  };

  const handleSendMessage = async (msgText) => {
    if (!msgText.trim()) return;
    
    dispatch(addChatMessage({ role: 'user', content: msgText }));
    dispatch(setChatLoading(true));
    setUserInput('');
    // Keep input focused without moving or scrolling the viewport
    setTimeout(() => {
      chatInputRef.current?.focus();
    }, 0);

    try {
      const historyPayload = chatHistory.map(h => ({
        role: h.role,
        content: h.content
      }));

      const response = await axios.post('/api/chat', {
        message: msgText,
        active_interaction_id: activeForm.id || null,
        chat_history: historyPayload
      });

      const { response: aiResponse, extracted_data } = response.data;
      dispatch(addChatMessage({ role: 'assistant', content: aiResponse }));

      if (extracted_data) {
        dispatch(syncFormFromExtracted(extracted_data));
      }
      
      dispatch(setChatLoading(false));
    } catch (err) {
      dispatch(setError(err.response?.data?.detail || 'Failed to connect with AI agent.'));
      dispatch(addChatMessage({ 
        role: 'assistant', 
        content: '⚠️ Sorry, I encountered an error communicating with the LangGraph backend.' 
      }));
      dispatch(setChatLoading(false));
    }
  };

  const handleReset = () => {
    dispatch(resetForm());
    dispatch(clearChatHistory());
    setAttendees([]);
  };

  // Clickable recommendation cards/links (matches reference UI list)
  const suggestions = [
    { label: "Schedule follow-up meeting in 2 weeks", action: "Schedule follow-up meeting in 2 weeks" },
    { label: "Send OncoRoot Phase III PDF", action: "Send OncoRoot Phase III PDF to doctor" },
    { label: "Add Dr. Sharma to advisory board invite list", action: "Add Dr. Sharma to advisory board invite list" }
  ];

  const handleApplySuggestion = (suggestionText) => {
    const currentVal = activeForm.summary || '';
    const updatedVal = currentVal 
      ? `${currentVal}\n- ${suggestionText}` 
      : `- ${suggestionText}`;
    handleFieldChange('summary', updatedVal);
  };

  // Parse structured materials and samples for presentation
  const { materials, samples } = parseMaterialsAndSamples(activeForm.materials_shared);

  // Filter HCPs list for dropdown
  const filteredHcps = hcpsList.filter(h => 
    h.name.toLowerCase().includes(hcpSearchVal.toLowerCase())
  );

  return (
    <div className="min-h-[calc(100vh-100px)] bg-[#f8fafc] p-6 flex flex-col font-sans antialiased text-[#334155]">
      
      {/* Page Title */}
      <div className="max-w-7xl mx-auto w-full mb-6">
        <h1 className="text-2xl font-semibold text-[#0f172a] tracking-tight">Log HCP Interaction</h1>
      </div>

      <div className="max-w-7xl mx-auto w-full grid grid-cols-1 lg:grid-cols-12 gap-6 items-start flex-grow">
        
        {/* LEFT PANEL: Interaction Details Form */}
        <div className="lg:col-span-8 bg-white border border-[#e2e8f0] rounded-xl shadow-[0_1px_2px_0_rgba(0,0,0,0.05)] p-6 flex flex-col space-y-6">
          
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <h2 className="text-base font-semibold text-[#0f172a]">Interaction Details</h2>
            
            {activeForm.id && (
              <div className="flex items-center gap-1.5 bg-sky-50 text-sky-600 border border-sky-100 px-3 py-1 rounded-lg text-xs font-semibold">
                <Lock className="w-3.5 h-3.5" />
                <span>Form Locked (AI Managed) - ID: {activeForm.id}</span>
              </div>
            )}
          </div>

          <div className="space-y-4">
            
            {/* HCP Name & Interaction Type */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* HCP Name (Searchable Dropdown) */}
              <div className="relative">
                <label className="block text-[11px] font-bold text-[#64748b] uppercase tracking-wider mb-1">HCP Name</label>
                <div className="relative">
                  <input
                    type="text"
                    value={hcpSearchVal}
                    onFocus={() => setShowHcpDropdown(true)}
                    onChange={(e) => {
                      setHcpSearchVal(e.target.value);
                      setShowHcpDropdown(true);
                      handleFieldChange('hcp_name', e.target.value);
                    }}
                    onBlur={() => {
                      // Slight delay to allow clicking dropdown list items before blur hiding
                      setTimeout(() => setShowHcpDropdown(false), 200);
                    }}
                    placeholder="Search or select HCP..."
                    className="w-full px-3.5 py-2.5 bg-white border border-[#cbd5e1] rounded-lg text-sm text-[#0f172a] focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 font-medium"
                  />
                  <Search className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>

                {/* Dropdown Items overlay */}
                {showHcpDropdown && (
                  <div className="absolute z-10 w-full bg-white border border-[#cbd5e1] rounded-lg shadow-lg mt-1 max-h-60 overflow-y-auto">
                    {filteredHcps.map(h => (
                      <button
                        key={h.id}
                        type="button"
                        onMouseDown={() => handleSelectHcp(h)}
                        className="w-full px-4 py-2.5 text-left text-sm hover:bg-slate-50 text-slate-800 border-b border-slate-100 last:border-0 block font-medium"
                      >
                        {h.name} <span className="text-xs text-slate-400">({h.specialty} at {h.hospital})</span>
                      </button>
                    ))}
                    {filteredHcps.length === 0 && hcpSearchVal.trim() !== '' && (
                      <button
                        type="button"
                        onMouseDown={handleCreateHcp}
                        className="w-full px-4 py-3 text-left text-xs text-sky-600 hover:bg-sky-50 font-bold block"
                      >
                        + Create new HCP: "{hcpSearchVal}"
                      </button>
                    )}
                  </div>
                )}
              </div>

              {/* Interaction Type */}
              <div>
                <label className="block text-[11px] font-bold text-[#64748b] uppercase tracking-wider mb-1">Interaction Type</label>
                <select
                  value={activeForm.type}
                  onChange={(e) => handleFieldChange('type', e.target.value)}
                  className="w-full px-3.5 py-2.5 bg-white border border-[#cbd5e1] rounded-lg text-sm text-[#0f172a] focus:outline-none focus:border-sky-500 font-medium"
                >
                  <option value="Meeting">Meeting</option>
                  <option value="Call">Call</option>
                  <option value="Email">Email</option>
                  <option value="Conference">Conference</option>
                  <option value="Virtual Meeting">Virtual Meeting</option>
                </select>
              </div>

            </div>

            {/* Date & Time */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              
              {/* Date */}
              <div>
                <label className="block text-[11px] font-bold text-[#64748b] uppercase tracking-wider mb-1">Date</label>
                <div className="relative">
                  <input
                    type="date"
                    value={activeForm.date}
                    onChange={(e) => handleFieldChange('date', e.target.value)}
                    className="w-full pl-3.5 pr-10 py-2.5 bg-white border border-[#cbd5e1] rounded-lg text-sm text-[#0f172a] focus:outline-none focus:border-sky-500 font-medium"
                  />
                  <Calendar className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>

              {/* Time */}
              <div>
                <label className="block text-[11px] font-bold text-[#64748b] uppercase tracking-wider mb-1">Time</label>
                <div className="relative">
                  <input
                    type="text"
                    value={activeForm.time}
                    onChange={(e) => handleFieldChange('time', e.target.value)}
                    placeholder="e.g. 19:36"
                    className="w-full pl-3.5 pr-10 py-2.5 bg-white border border-[#cbd5e1] rounded-lg text-sm text-[#0f172a] focus:outline-none focus:border-sky-500 font-medium"
                  />
                  <Clock className="absolute right-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                </div>
              </div>

            </div>

            {/* Attendees (Multi-Select) */}
            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-[11px] font-bold text-[#64748b] uppercase tracking-wider">Attendees</label>
                <button
                  type="button"
                  onClick={() => setShowAttendeeInput(!showAttendeeInput)}
                  className="text-xs text-sky-600 hover:text-sky-500 font-semibold"
                >
                  {showAttendeeInput ? "Close" : "+ Add Attendee"}
                </button>
              </div>

              {/* Tag Containers */}
              <div className="min-h-12 w-full p-2.5 bg-white border border-[#cbd5e1] rounded-lg flex flex-wrap gap-2 items-center">
                {attendees.map(name => (
                  <span 
                    key={name} 
                    className="inline-flex items-center gap-1.5 px-3 py-1 bg-slate-100 text-slate-700 text-xs font-semibold rounded-full border border-slate-200"
                  >
                    <span>{name}</span>
                    <button 
                      type="button" 
                      onClick={() => handleRemoveAttendee(name)}
                      className="text-slate-400 hover:text-slate-600 text-xs font-bold leading-none"
                    >
                      ×
                    </button>
                  </span>
                ))}
                {attendees.length === 0 && (
                  <span className="text-slate-400 text-xs px-1 select-none font-medium">Enter names or search...</span>
                )}
              </div>

              {/* Inline input */}
              {showAttendeeInput && (
                <div className="flex gap-2 mt-2">
                  <input
                    type="text"
                    value={newAttendeeName}
                    onChange={(e) => setNewAttendeeName(e.target.value)}
                    placeholder="Attendee Name"
                    className="px-3 py-1.5 bg-white border border-[#cbd5e1] rounded-lg text-xs w-48 focus:outline-none focus:border-sky-500"
                  />
                  <button
                    type="button"
                    onClick={handleAddAttendee}
                    className="px-3.5 py-1.5 bg-sky-600 hover:bg-sky-500 text-white rounded-lg text-xs font-semibold"
                  >
                    Add
                  </button>
                </div>
              )}
            </div>

            {/* Topics Discussed */}
            <div className="relative">
              <label className="block text-[11px] font-bold text-[#64748b] uppercase tracking-wider mb-1">Topics Discussed</label>
              <div className="relative">
                <textarea
                  rows={3}
                  value={activeForm.topics_discussed}
                  onChange={(e) => handleFieldChange('topics_discussed', e.target.value)}
                  placeholder="Enter key discussion points..."
                  className="w-full px-3.5 py-2.5 bg-white border border-[#cbd5e1] rounded-lg text-sm text-[#0f172a] focus:outline-none focus:border-sky-500 focus:ring-1 focus:ring-sky-500 resize-none pr-10 font-medium"
                />
                <Mic className="absolute right-3.5 bottom-3.5 w-4 h-4 text-slate-400 pointer-events-none" />
              </div>
            </div>

            {/* Voice Note Button */}
            <div>
              <button
                type="button"
                className="inline-flex items-center gap-2 px-3.5 py-2 bg-[#f1f5f9] border border-[#cbd5e1] hover:bg-[#e2e8f0] text-[#475569] rounded-lg text-xs font-semibold transition opacity-90"
              >
                <div className="flex items-center gap-0.5">
                  <span className="w-1 h-3.5 bg-slate-500 rounded-full animate-pulse"></span>
                  <span className="w-1 h-4.5 bg-slate-600 rounded-full animate-pulse" style={{ animationDelay: '100ms' }}></span>
                  <span className="w-1 h-2.5 bg-slate-500 rounded-full animate-pulse" style={{ animationDelay: '200ms' }}></span>
                </div>
                <span>Summarize from Voice Note (Requires Consent)</span>
              </button>
            </div>

            {/* Materials Shared & Samples Container Card */}
            <div className="border border-[#cbd5e1] rounded-xl p-4 bg-white space-y-4">
              <h3 className="text-xs font-bold text-[#475569] uppercase tracking-wider">Materials Shared / Samples Distributed</h3>

              {/* Materials Shared Row */}
              <div className="border-b border-[#f1f5f9] pb-3.5 flex items-center justify-between gap-4">
                <div className="flex-grow">
                  <div className="text-[10px] font-bold text-slate-400 uppercase mb-1.5">Materials Shared</div>
                  <div className="flex flex-wrap gap-1.5">
                    {materials.map(m => (
                      <span key={m} className="inline-flex items-center gap-1.5 px-3 py-1 bg-sky-50 text-sky-700 text-xs font-semibold rounded-full border border-sky-100">
                        <span>{m}</span>
                        <button type="button" onClick={() => handleRemoveMaterial(m)} className="text-sky-400 hover:text-sky-600 font-bold">×</button>
                      </span>
                    ))}
                    {materials.length === 0 && (
                      <span className="text-xs text-slate-400 font-medium">No materials added.</span>
                    )}
                  </div>
                </div>
                
                <div className="shrink-0 flex flex-col items-end">
                  <button
                    type="button"
                    onClick={() => setShowMaterialInput(!showMaterialInput)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#f8fafc] border border-[#cbd5e1] hover:bg-[#f1f5f9] text-[#475569] rounded-lg text-xs font-bold transition shadow-[0_1px_1px_0_rgba(0,0,0,0.02)]"
                  >
                    <Search className="w-3.5 h-3.5 text-slate-500" />
                    <span>Search/Add</span>
                  </button>

                  {showMaterialInput && (
                    <div className="flex gap-1.5 mt-2">
                      <input
                        type="text"
                        value={newMaterialName}
                        onChange={(e) => setNewMaterialName(e.target.value)}
                        placeholder="Material Name"
                        className="px-2 py-1 bg-white border border-[#cbd5e1] rounded text-xs w-36 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={handleAddMaterial}
                        className="px-2 py-1 bg-sky-600 hover:bg-sky-500 text-white rounded text-xs font-bold"
                      >
                        Add
                      </button>
                    </div>
                  )}
                </div>
              </div>

              {/* Samples Distributed Row */}
              <div className="flex items-center justify-between gap-4">
                <div className="flex-grow">
                  <div className="text-[10px] font-bold text-slate-400 uppercase mb-1.5">Samples Distributed</div>
                  <div className="flex flex-wrap gap-1.5">
                    {samples.map((s, idx) => (
                      <span key={idx} className="inline-flex items-center gap-1.5 px-3 py-1 bg-teal-50 text-teal-700 text-xs font-semibold rounded-full border border-teal-100">
                        <span>{s.quantity} x {s.name}</span>
                        <button type="button" onClick={() => handleRemoveSample(idx)} className="text-teal-400 hover:text-teal-600 font-bold">×</button>
                      </span>
                    ))}
                    {samples.length === 0 && (
                      <span className="text-xs text-slate-400 font-medium">No samples added.</span>
                    )}
                  </div>
                </div>

                <div className="shrink-0 flex flex-col items-end">
                  <button
                    type="button"
                    onClick={() => setShowSampleInput(!showSampleInput)}
                    className="inline-flex items-center gap-1.5 px-3.5 py-1.5 bg-[#f8fafc] border border-[#cbd5e1] hover:bg-[#f1f5f9] text-[#475569] rounded-lg text-xs font-bold transition shadow-[0_1px_1px_0_rgba(0,0,0,0.02)]"
                  >
                    <Plus className="w-3.5 h-3.5 text-slate-500" />
                    <span>Add Sample</span>
                  </button>

                  {showSampleInput && (
                    <div className="flex gap-1 mt-2 items-center">
                      <input
                        type="text"
                        value={newSampleName}
                        onChange={(e) => setNewSampleName(e.target.value)}
                        placeholder="Sample Product"
                        className="px-2 py-1 bg-white border border-[#cbd5e1] rounded text-xs w-28 focus:outline-none"
                      />
                      <input
                        type="number"
                        min={1}
                        value={newSampleQty}
                        onChange={(e) => setNewSampleQty(parseInt(e.target.value, 10))}
                        className="px-1 py-1 bg-white border border-[#cbd5e1] rounded text-xs w-12 focus:outline-none"
                      />
                      <button
                        type="button"
                        onClick={handleAddSample}
                        className="px-2.5 py-1 bg-teal-600 hover:bg-teal-500 text-white rounded text-xs font-bold"
                      >
                        Add
                      </button>
                    </div>
                  )}
                </div>
              </div>

            </div>

            {/* Observed/Inferred HCP Sentiment */}
            <div>
              <label className="block text-[11px] font-bold text-[#64748b] uppercase tracking-wider mb-2">Observed/Inferred HCP Sentiment</label>
              
              <div className="flex gap-10 items-center pl-1">
                
                {/* Positive Sentiment */}
                <label className="flex flex-col items-center gap-1 cursor-pointer select-none group">
                  <Smile className={`w-7.5 h-7.5 transition ${activeForm.sentiment === 'Positive' ? 'text-sky-500' : 'text-[#cbd5e1] group-hover:text-slate-400'}`} />
                  <div className="flex items-center gap-1.5 mt-1">
                    <input
                      type="radio"
                      name="sentiment"
                      value="Positive"
                      checked={activeForm.sentiment === 'Positive'}
                      onChange={() => handleFieldChange('sentiment', 'Positive')}
                      className="w-3.5 h-3.5 text-sky-600 focus:ring-sky-500 cursor-pointer"
                    />
                    <span className="text-xs text-[#334155] font-semibold">Positive</span>
                  </div>
                </label>

                {/* Neutral Sentiment */}
                <label className="flex flex-col items-center gap-1 cursor-pointer select-none group">
                  <Meh className={`w-7.5 h-7.5 transition ${activeForm.sentiment === 'Neutral' ? 'text-amber-500' : 'text-[#cbd5e1] group-hover:text-slate-400'}`} />
                  <div className="flex items-center gap-1.5 mt-1">
                    <input
                      type="radio"
                      name="sentiment"
                      value="Neutral"
                      checked={activeForm.sentiment === 'Neutral'}
                      onChange={() => handleFieldChange('sentiment', 'Neutral')}
                      className="w-3.5 h-3.5 text-sky-600 focus:ring-sky-500 cursor-pointer"
                    />
                    <span className="text-xs text-[#334155] font-semibold">Neutral</span>
                  </div>
                </label>

                {/* Negative Sentiment */}
                <label className="flex flex-col items-center gap-1 cursor-pointer select-none group">
                  <Frown className={`w-7.5 h-7.5 transition ${activeForm.sentiment === 'Negative' ? 'text-rose-500' : 'text-[#cbd5e1] group-hover:text-slate-400'}`} />
                  <div className="flex items-center gap-1.5 mt-1">
                    <input
                      type="radio"
                      name="sentiment"
                      value="Negative"
                      checked={activeForm.sentiment === 'Negative'}
                      onChange={() => handleFieldChange('sentiment', 'Negative')}
                      className="w-3.5 h-3.5 text-sky-600 focus:ring-sky-500 cursor-pointer"
                    />
                    <span className="text-xs text-[#334155] font-semibold">Negative</span>
                  </div>
                </label>

              </div>
            </div>

            {/* Outcomes (binds to activeForm.notes) */}
            <div>
              <label className="block text-[11px] font-bold text-[#64748b] uppercase tracking-wider mb-1">Outcomes</label>
              <textarea
                rows={2}
                value={activeForm.notes}
                onChange={(e) => handleFieldChange('notes', e.target.value)}
                placeholder="Key outcomes or agreements..."
                className="w-full px-3.5 py-2.5 bg-white border border-[#cbd5e1] rounded-lg text-sm text-[#0f172a] focus:outline-none focus:border-sky-500 resize-none font-medium"
              />
            </div>

            {/* Follow-up Actions (binds to activeForm.summary) */}
            <div>
              <label className="block text-[11px] font-bold text-[#64748b] uppercase tracking-wider mb-1">Follow-up Actions</label>
              <textarea
                rows={2}
                value={activeForm.summary}
                onChange={(e) => handleFieldChange('summary', e.target.value)}
                placeholder="Enter next steps or tasks..."
                className="w-full px-3.5 py-2.5 bg-white border border-[#cbd5e1] rounded-lg text-sm text-[#0f172a] focus:outline-none focus:border-sky-500 resize-none font-medium"
              />
            </div>

            {/* AI Suggested Follow-ups Links list */}
            <div className="pt-2">
              <span className="block text-xs font-bold text-[#475569] mb-1.5">AI Suggested Follow-ups:</span>
              <ul className="space-y-1.5">
                {suggestions.map((s, idx) => (
                  <li key={idx}>
                    <button
                      type="button"
                      onClick={() => handleApplySuggestion(s.action)}
                      className="inline-flex items-center text-xs text-sky-600 hover:text-sky-500 font-bold text-left transition"
                    >
                      + <span className="ml-1 underline">{s.label}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>

          </div>

          {/* CRM Session Controls */}
          <div className="pt-4 border-t border-slate-100 flex justify-between gap-4">
            <button
              type="button"
              onClick={handleReset}
              className="flex items-center gap-1.5 px-4 py-2.5 border border-[#cbd5e1] hover:bg-slate-50 rounded-lg text-xs font-bold text-slate-600 transition"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Clear / Reset CRM Session</span>
            </button>
          </div>

        </div>

        {/* RIGHT PANEL: AI Assistant Chat */}
        <div className="lg:col-span-4 bg-white border border-[#e2e8f0] rounded-xl shadow-[0_1px_2px_0_rgba(0,0,0,0.05)] h-[calc(100vh-170px)] sticky top-6 flex flex-col overflow-hidden">
          
          {/* Chat Header */}
          <div className="px-5 py-4.5 border-b border-slate-100 flex items-center justify-between shrink-0">
            <div className="flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-sky-500" />
              <div>
                <h3 className="font-bold text-[#0f172a] text-sm leading-tight">AI Assistant</h3>
                <p className="text-[10px] text-slate-400 font-bold uppercase tracking-wider">Log interaction via chat</p>
              </div>
            </div>
            <button 
              onClick={handleReset} 
              className="text-slate-400 hover:text-[#0f172a] transition"
              title="Reset conversation"
            >
              <RefreshCw className="w-4 h-4" />
            </button>
          </div>

          {/* Chat Bubble Thread List */}
          <div className="flex-grow p-5 overflow-y-auto space-y-4 bg-[#f8fafc]/60">
            {chatHistory.map((msg, index) => {
              const isUser = msg.role === 'user';
              return (
                <div 
                  key={index}
                  className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}
                >
                  <div 
                    className={`max-w-[90%] rounded-xl px-4 py-3 text-xs leading-relaxed border ${
                      isUser 
                        ? 'bg-sky-600 text-white border-sky-600 rounded-br-none font-semibold shadow-sm' 
                        : 'bg-white text-slate-800 border-[#e2e8f0] rounded-bl-none shadow-[0_1px_1px_0_rgba(0,0,0,0.02)] font-medium'
                    }`}
                  >
                    <p className="whitespace-pre-line">{msg.content}</p>
                  </div>
                </div>
              );
            })}

            {/* AI is thinking/loading */}
            {chatLoading && (
              <div className="flex justify-start">
                <div className="bg-white text-slate-500 rounded-xl border border-[#e2e8f0] rounded-bl-none px-4 py-3.5 text-xs flex items-center gap-2 shadow-sm font-semibold">
                  <span className="flex gap-1 shrink-0">
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '0ms' }}></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '150ms' }}></span>
                    <span className="w-1.5 h-1.5 rounded-full bg-slate-400 animate-bounce" style={{ animationDelay: '300ms' }}></span>
                  </span>
                  <span className="text-[10px] italic">Extracting interaction details...</span>
                </div>
              </div>
            )}
            
            <div ref={chatEndRef} />
          </div>

          {/* Chat Input form */}
          <div className="p-4 border-t border-slate-100 shrink-0 bg-white">
            <form 
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage(userInput);
              }}
              className="flex gap-2"
            >
              <input
                ref={chatInputRef}
                type="text"
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
                placeholder="Describe interaction..."
                disabled={chatLoading}
                className="flex-grow px-3.5 py-2.5 bg-white border border-[#cbd5e1] rounded-lg text-xs text-[#0f172a] font-semibold placeholder-slate-400 focus:outline-none focus:border-sky-500"
              />
              <button
                type="submit"
                disabled={chatLoading || !userInput.trim()}
                className="px-4 py-2.5 bg-slate-800 hover:bg-slate-700 disabled:opacity-50 text-white rounded-lg flex items-center gap-1.5 transition text-xs font-bold"
              >
                <Send className="w-3.5 h-3.5 rotate-45 text-white" />
                <span>Log</span>
              </button>
            </form>
          </div>

        </div>

      </div>
    </div>
  );
};

export default InteractionModule;
