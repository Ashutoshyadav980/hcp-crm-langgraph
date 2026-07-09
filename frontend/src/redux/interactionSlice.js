import { createSlice } from '@reduxjs/toolkit';

const initialFormState = {
  id: null,
  hcp_id: '',
  hcp_name: '',
  hospital: '',
  specialty: '',
  type: 'Meeting',
  date: new Date().toISOString().split('T')[0],
  time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
  topics_discussed: '',
  materials_shared: '',
  sentiment: 'Positive',
  notes: '',
  summary: '',
  follow_up_date: '',
};

const initialState = {
  activeForm: initialFormState,
  chatHistory: [
    {
      role: 'assistant',
      content: 'Hello! I am your AI CRM Assistant. Speak or type details of your interaction (e.g. "Today I met Dr. Smith...") and I will automatically extract and populate the form fields for you.'
    }
  ],
  recentInteractions: [],
  upcomingFollowups: [],
  dashboardStats: null,
  loading: false,
  chatLoading: false,
  error: null,
};

const interactionSlice = createSlice({
  name: 'interaction',
  initialState,
  reducers: {
    setLoading: (state, action) => {
      state.loading = action.payload;
    },
    setChatLoading: (state, action) => {
      state.chatLoading = action.payload;
    },
    setError: (state, action) => {
      state.error = action.payload;
      state.loading = false;
      state.chatLoading = false;
    },
    setFormFields: (state, action) => {
      state.activeForm = { ...state.activeForm, ...action.payload };
    },
    syncFormFromExtracted: (state, action) => {
      // Direct synchronization of AI extracted details
      state.activeForm = {
        ...state.activeForm,
        id: action.payload.id || state.activeForm.id,
        hcp_id: action.payload.hcp_id || state.activeForm.hcp_id,
        hcp_name: action.payload.hcp_name || state.activeForm.hcp_name,
        hospital: action.payload.hospital || state.activeForm.hospital,
        specialty: action.payload.specialty || state.activeForm.specialty,
        type: action.payload.type || state.activeForm.type,
        date: action.payload.date || state.activeForm.date,
        time: action.payload.time || state.activeForm.time,
        topics_discussed: action.payload.topics_discussed || state.activeForm.topics_discussed,
        materials_shared: action.payload.materials_shared || state.activeForm.materials_shared,
        sentiment: action.payload.sentiment || state.activeForm.sentiment,
        notes: action.payload.notes || state.activeForm.notes,
        summary: action.payload.summary || state.activeForm.summary,
        follow_up_date: action.payload.follow_up_date || state.activeForm.follow_up_date,
      };
    },
    resetForm: (state) => {
      state.activeForm = {
        ...initialFormState,
        date: new Date().toISOString().split('T')[0],
        time: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      };
    },
    addChatMessage: (state, action) => {
      state.chatHistory.push(action.payload);
    },
    setChatHistory: (state, action) => {
      state.chatHistory = action.payload;
    },
    setDashboardData: (state, action) => {
      state.dashboardStats = action.payload.summary;
      state.recentInteractions = action.payload.recent_interactions;
      state.upcomingFollowups = action.payload.upcoming_followups_list;
    },
    clearChatHistory: (state) => {
      state.chatHistory = [
        {
          role: 'assistant',
          content: 'Hello! Describe your HCP meeting and let me extract the details for you.'
        }
      ];
    }
  },
});

export const {
  setLoading,
  setChatLoading,
  setError,
  setFormFields,
  syncFormFromExtracted,
  resetForm,
  addChatMessage,
  setChatHistory,
  setDashboardData,
  clearChatHistory
} = interactionSlice.actions;

export default interactionSlice.reducer;
