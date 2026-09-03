// API Client Wrapper with JWT Token Management
const API_BASE = '/api';

class ApiClient {
  static getHeaders(isMultipart = false) {
    const token = localStorage.getItem('access_token');
    const headers = {};
    if (!isMultipart) {
      headers['Content-Type'] = 'application/json';
    }
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
    return headers;
  }

  static async request(endpoint, options = {}) {
    const isMultipart = options.body instanceof FormData;
    const config = {
      ...options,
      headers: {
        ...this.getHeaders(isMultipart),
        ...(options.headers || {}),
      },
    };

    try {
      const response = await fetch(`${API_BASE}${endpoint}`, config);
      if (response.status === 401 && !endpoint.includes('/auth/login')) {
        localStorage.removeItem('access_token');
        localStorage.removeItem('user_info');
        window.location.href = '/login.html';
        return;
      }

      const resData = await response.json();
      if (!response.ok || !resData.success) {
        throw new Error(resData.message || 'API Request failed');
      }
      return resData.data;
    } catch (err) {
      console.error(`[API Error] ${endpoint}:`, err);
      throw err;
    }
  }

  static get(endpoint) {
    return this.request(endpoint, { method: 'GET' });
  }

  static post(endpoint, body) {
    const isMultipart = body instanceof FormData;
    return this.request(endpoint, {
      method: 'POST',
      body: isMultipart ? body : JSON.stringify(body),
    });
  }

  static put(endpoint, body = {}) {
    return this.request(endpoint, {
      method: 'PUT',
      body: JSON.stringify(body),
    });
  }

  static delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }
}
