export const API_BASE = (window.location.origin.startsWith('http') && (window.location.port === '8000' || !window.location.port))
  ? `${window.location.origin}/api/v1`
  : 'http://localhost:8000/api/v1';

export const RISK_LEVELS = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
  CRITICAL: 'critical'
};

export const STATUSES = {
  PENDING: 'pending',
  APPROVED: 'approved',
  DISMISSED: 'dismissed',
  UNDER_REVIEW: 'under_review',
  ESCALATED: 'escalated',
  COMPLETED: 'completed',
  FAILED: 'failed'
};
