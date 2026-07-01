export interface Config {
  API_KEY_SECRET?: string;
  PASSIVE_MONITORING?: string;
  SCHEMA_REGISTRY_PROVIDER?: string;
  VECTOR_DB_PROVIDER?: string;
  [key: string]: string | undefined;
}

export interface Metrics {
  llm_requests_current_min: number;
  llm_rate_limit: number;
  max_payload_size: number;
  total_requests_current_min?: number;
  llm_average_latency_ms?: number;
  agent_circuit_breakers?: Record<string, { failures: number; last_failure_time: number }>;
}

export interface DlqItem {
  idx?: number;
  source: string;
  target: string;
  payload: string | any;
  reason: string;
  timestamp: number;
}

export interface AuditLog {
  TraceId?: string;
  SpanId?: string;
  id?: string;
  Timestamp?: number;
  timestamp?: string;
  SeverityNumber?: number;
  SeverityText?: string;
  reason?: string;
  source?: string;
  target?: string;
  Attributes?: Record<string, any>;
}

export interface Agent {
  id: string;
  errors: number | { failures: number; last_failure_time: number };
  status: 'HEALTHY' | 'TRIPPED';
  threshold: number;
}

export interface Example {
  id: string;
  name: string;
  description: string;
  category: string;
  difficulty: string;
}
