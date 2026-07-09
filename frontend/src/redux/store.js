import { configureStore } from '@reduxjs/toolkit';
import authReducer from './authSlice';
import interactionReducer from './interactionSlice';

export const store = configureStore({
  reducer: {
    auth: authReducer,
    interaction: interactionReducer,
  },
});

export default store;
