import axios, { AxiosInstance } from 'axios';
import type { Client, SearchStats, SystemHealth, OverviewStats, AuditLog, SystemSettings } from '../types';

class ApiService {
  private client: AxiosInstance;
  private bearerToken: string = '';

  constructor() {
    this.client = axios.create({
      baseURL: '/api/v1',
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Attach Bearer token from Keycloak on every request
    this.client.interceptors.request.use((config) => {
      if (this.bearerToken) {
        config.headers['Authorization'] = `Bearer ${this.bearerToken}`;
      }
      return config;
    });

    // On 401, redirect back to Keycloak login
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Token expired or invalid — oidc-client-ts will handle silent renew,
          // but if that fails too the user ends up back at the login screen.
          window.location.reload();
        }
        return Promise.reject(error);
      }
    );
  }

  setBearerToken(token: string) {
    this.bearerToken = token;
  }

  /** @deprecated Use setBearerToken instead */
  setApiKey(key: string) {
    this.bearerToken = key;
  }

  // Health & Status
  async getHealth() {
    const response = await this.client.get('/health');
    return response.data;
  }

  async getSystemHealth(): Promise<SystemHealth> {
    const response = await this.client.get('/admin/system/health');
    return response.data;
  }

  // Overview & Stats
  async getOverview(): Promise<OverviewStats> {
    const response = await this.client.get('/admin/stats/overview');
    return response.data;
  }

  async getSearchStats(days: number = 30): Promise<SearchStats> {
    const response = await this.client.get('/admin/stats/searches', {
      params: { days },
    });
    return response.data;
  }

  // Client Management
  async getClients(): Promise<Client[]> {
    const response = await this.client.get('/admin/clients');
    return response.data;
  }

  async getClient(clientId: string): Promise<Client> {
    const response = await this.client.get(`/clients/${clientId}`);
    return response.data;
  }

  async createClient(data: Partial<Client>): Promise<Client> {
    const response = await this.client.post('/clients', data);
    return response.data;
  }

  async updateClient(clientId: string, data: Partial<Client>): Promise<Client> {
    const response = await this.client.put(`/clients/${clientId}`, data);
    return response.data;
  }

  async deleteClient(clientId: string): Promise<void> {
    await this.client.delete(`/clients/${clientId}`);
  }

  // Audit Logs
  async getAuditLogs(params?: {
    client_id?: string;
    action?: string;
    start_date?: string;
    end_date?: string;
    limit?: number;
  }): Promise<AuditLog[]> {
    const response = await this.client.get('/admin/audit-logs', { params });
    // Backend returns {total, skip, limit, logs}, we just need logs array
    return response.data.logs || response.data;
  }

  // Search Providers
  async getProviderStatus() {
    const response = await this.client.post('/search/providers/health-check');
    return response.data;
  }

  // System Settings
  async getSettings(): Promise<SystemSettings> {
    const response = await this.client.get('/admin/settings');
    return response.data;
  }

  async updateSettings(settings: SystemSettings): Promise<SystemSettings> {
    const response = await this.client.put('/admin/settings', settings);
    return response.data;
  }

  // Users
  async getUsers(): Promise<any[]> {
    const response = await this.client.get('/admin/users');
    return response.data;
  }

  async getUser(userId: string): Promise<any> {
    const response = await this.client.get(`/admin/users/${userId}`);
    return response.data;
  }

  async updateUser(userId: string, data: any): Promise<any> {
    const response = await this.client.put(`/admin/users/${userId}`, data);
    return response.data;
  }

  async deleteUser(userId: string): Promise<void> {
    await this.client.delete(`/admin/users/${userId}`);
  }

  // Groups
  async getGroups(): Promise<any[]> {
    const response = await this.client.get('/admin/groups');
    return response.data;
  }

  async getGroup(groupId: string): Promise<any> {
    const response = await this.client.get(`/admin/groups/${groupId}`);
    return response.data;
  }

  // CSV Import
  async importUsersCSV(file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);
    const response = await this.client.post('/admin/users/import-csv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }

  // Policies
  async getPolicies(): Promise<any[]> {
    const response = await this.client.get('/admin/policies');
    return response.data;
  }

  async getPolicy(policyId: string): Promise<any> {
    const response = await this.client.get(`/admin/policies/${policyId}`);
    return response.data;
  }

  async createPolicy(data: any): Promise<any> {
    const response = await this.client.post('/admin/policies', data);
    return response.data;
  }

  async updatePolicy(policyId: string, data: any): Promise<any> {
    const response = await this.client.put(`/admin/policies/${policyId}`, data);
    return response.data;
  }

  async deletePolicy(policyId: string): Promise<void> {
    await this.client.delete(`/admin/policies/${policyId}`);
  }
}

export const api = new ApiService();
export default api;
