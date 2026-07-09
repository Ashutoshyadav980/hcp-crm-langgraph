import axios from 'axios';

// Set backend server API URL
axios.defaults.baseURL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default axios;
