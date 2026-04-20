// Type definitions for the WebSearch API Admin Dashboard

export interface Client {
  client_id: string;
  client_name: string;
  client_type: string;
  owner_id: string;
  is_active: boolean;
  quota_per_day: number;
  quota_per_month: number;
  created_at: string;
  updated_at: string;
  last_used: string | null;
  metadata?: Record<string, any>;
  api_key?: string; // Only returned on creation
}

export interface SearchStats {
  period_days: number;
  start_date: string;
  end_date: string;
  daily_stats: Array<{
    date: string;
    searches: number;
    avg_response_time_ms: number;
    total_results: number;
  }>;
  searches_by_provider?: Record<string, number>;
  top_queries?: Array<{ query: string; count: number }>;
}

export interface SystemHealth {
  status: string;
  components: {
    database: {
      status: string;
      type: string;
    };
    cache: {
      status: string;
      type: string;
      memory_used?: string;
    };
  };
  timestamp: string;
}

export interface OverviewStats {
  total_clients: number;
  total_users: number;
  total_policies: number;
  searches_24h: number;
  active_clients_24h: number;
  avg_response_time_ms: number;
  timestamp: string;
}

export interface AuditLog {
  audit_id: string;
  timestamp: string;
  client_id: string;
  user_id?: string;
  user_email?: string;
  user_name?: string;
  action: string;
  resource_type: string;
  resource_id?: string;
  status: string;
  ip_address?: string;
  user_agent?: string;
  details?: Record<string, any>;
  trace?: {
    trace_id: string;
    span_id: string;
  };
  request?: {
    method: string;
    path: string;
    query?: string;
    ip_address?: string;
    user_agent?: string;
  };
  response?: {
    status_code: number;
    provider?: string;
    results_count?: number;
    response_time_ms?: number;
    blocked_reason?: string;
  };
  policies_details?: Array<{
    policy_id: string;
    policy_name?: string;
    priority: number;
    blocked_keywords?: string[];
  }>;
  quotas?: {
    used_today: number;
    limit_today: number;
    used_month: number;
    limit_month: number;
  };
  filtering?: {
    total_results: number;
    blocked_results: number;
    returned_results: number;
  };
}

export interface PolicyRule {
  id: string;
  name: string;
  type: string;
  enabled: boolean;
  config: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface DashboardState {
  apiKey: string;
  isLoading: boolean;
  error: string | null;
}

export interface ProviderHealth {
  provider: string;
  status: string;
  available: boolean;
  response_time_ms?: number;
  last_check?: string;
}

export interface SearchPolicy {
  level: 'strict' | 'moderate' | 'open' | 'custom';
  enabled: boolean;
  block_keywords: string[];
}

export interface ParentalControls {
  enabled: boolean;
  age_restriction: number;
  block_adult_content: boolean;
  block_violence: boolean;
  block_gambling: boolean;
  block_drugs: boolean;
}

export interface SystemSettings {
  otel_endpoint: string;
  search_policy: SearchPolicy;
  parental_controls: ParentalControls;
  integrations: {
    grafana_url: string;
    prometheus_url: string;
    jaeger_url: string;
  };
  user_sync?: UserSyncSettings;
}

export interface UserSyncSettings {
  enabled: boolean;
  sync_interval_hours: number;
  sources: UserSyncSource[];
  group_sync_enabled: boolean;
  auto_create_users: boolean;
  auto_assign_policies: boolean;
}

export interface UserSyncSource {
  source_id: string;
  name: string;
  type: 'active_directory' | 'entra_id' | 'okta' | 'csv' | 'ldap';
  enabled: boolean;
  config: {
    server_url?: string;
    domain?: string;
    tenant_id?: string;
    client_id?: string;
    client_secret?: string;
    base_dn?: string;
    bind_user?: string;
    bind_password?: string;
    csv_path?: string;
    sync_groups?: boolean;
    group_filter?: string;
    user_filter?: string;
  };
  last_sync?: string;
  last_sync_status?: 'success' | 'failed' | 'pending';
  users_synced?: number;
  groups_synced?: number;
}
