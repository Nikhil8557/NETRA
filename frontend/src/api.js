// frontend/src/api.js
import axios from 'axios';
import { useNetraStore } from './store';

const api = axios.create({
  baseURL: 'http://127.0.0.1:8000/api/v1',
  timeout: 10000,
});

api.interceptors.request.use(
  (config) => {
    const store = useNetraStore.getState();
    if (store.userToken) {
      config.headers['Authorization'] = `Bearer ${store.userToken}`;
    }
    const caseMatch = config.url.match(/\/case\/([A-Z0-9-]+)/);
    const resourceId = caseMatch ? caseMatch[1] : null;
    if (resourceId && store.activeOverrides[resourceId]) {
      const override = store.activeOverrides[resourceId];
      config.headers['X-Emergency-Override-Reason'] = override.reason;
      config.headers['X-Active-Investigation-FIR'] = override.activeFir;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const originalRequest = error.config;
    if (error.response && error.response.status === 403) {
      const store = useNetraStore.getState();
      const caseMatch = originalRequest.url.match(/\/case\/([A-Z0-9-]+)/);
      const resourceId = caseMatch ? caseMatch[1] : null;
      const targetJurisdiction = error.response.data?.detail
        ? (error.response.data.detail.match(/jurisdiction \(([^)]+)\)/) || [])[1] || 'OUTSIDE'
        : 'OUTSIDE';

      if (resourceId) {
        store.openBreakGlass('CASE', resourceId, targetJurisdiction);
        return new Promise(() => {}); 
      }
    }
    return Promise.reject(error);
  }
);

export default api;
