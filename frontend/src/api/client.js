import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const client = axios.create({ baseURL: API_BASE })

export const api = {
  getDashboard: () => client.get('/dashboard').then((r) => r.data),

  getTransactions: (params = {}) => client.get('/transactions', { params }).then((r) => r.data),
  getTransaction: (id) => client.get(`/transactions/${id}`).then((r) => r.data),

  getVendors: () => client.get('/vendors').then((r) => r.data),
  getVendor: (id) => client.get(`/vendors/${id}`).then((r) => r.data),

  getBudgets: () => client.get('/budgets').then((r) => r.data),

  getReceivables: () => client.get('/receivables').then((r) => r.data),
  getRepeatedLatePayers: () => client.get('/receivables/repeated-late-payers').then((r) => r.data),

  getCashflow: () => client.get('/cashflow').then((r) => r.data),

  getAnomalies: (status) => client.get('/anomalies', { params: status ? { status } : {} }).then((r) => r.data),
  getAnomaly: (id) => client.get(`/anomalies/${id}`).then((r) => r.data),
  investigateAnomaly: (id) => client.post(`/anomalies/${id}/investigate`).then((r) => r.data),

  approveAction: (payload) => client.post('/actions/approve', payload).then((r) => r.data),
  rejectAction: (payload) => client.post('/actions/reject', payload).then((r) => r.data),
  escalateAction: (payload) => client.post('/actions/escalate', payload).then((r) => r.data),

  getAuditLogs: (investigationId) =>
    client.get('/audit-logs', { params: investigationId ? { investigation_id: investigationId } : {} }).then((r) => r.data),

  queryAssistant: (question) => client.post('/assistant/query', { question }).then((r) => r.data),
}

export default api
