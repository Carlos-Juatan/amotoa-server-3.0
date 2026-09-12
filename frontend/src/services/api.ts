import axios from 'axios';

// Fallback to localhost:8000 in local dev environment
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = axios.create({
  baseURL: BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Interceptor to inject the active account header dynamically
api.interceptors.request.use((config) => {
  const activeAccount = localStorage.getItem('active_account') || 'car-j-home';
  config.headers['X-Active-Account'] = activeAccount;
  return config;
}, (error) => {
  return Promise.reject(error);
});

// Helper to set and update the active account state
export const getActiveAccountFromStorage = (): string => {
  return localStorage.getItem('active_account') || 'car-j-home';
};

export const setActiveAccountInStorage = (accountId: string): void => {
  localStorage.setItem('active_account', accountId);
};
