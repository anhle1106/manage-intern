// Authentication helper
class Auth {
  static getToken() {
    return localStorage.getItem('access_token');
  }

  static getUser() {
    const data = localStorage.getItem('user_info');
    return data ? JSON.parse(data) : null;
  }

  static isAuthenticated() {
    return !!this.getToken();
  }

  static requireAuth() {
    if (!this.isAuthenticated()) {
      window.location.href = '/login.html';
    }
  }

  static async login(email, password) {
    const data = await ApiClient.post('/auth/login', { email, password });
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('user_info', JSON.stringify({
      id: data.user_id,
      role: data.role,
      full_name: data.full_name,
    }));
    window.location.href = '/dashboard.html';
  }

  static logout() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user_info');
    window.location.href = '/login.html';
  }
}
