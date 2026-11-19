import axios from 'axios'

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

const client = axios.create({ baseURL: API_BASE })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('finguard_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

export const api = {
  register: (payload) => client.post('/auth/register', payload).then((r) => r.data),
  login: (payload) => client.post('/auth/login', payload).then((r) => r.data),
  getCurrentUser: () => client.get('/auth/me').then((r) => r.data),
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

  getIngestionRuns: () => client.get('/ingestion/runs').then((r) => r.data),
  getWorkspaceSummary: () => client.get('/ingestion/workspace').then((r) => r.data),
  getIngestionRun: (id) => client.get(`/ingestion/runs/${id}`).then((r) => r.data),
  uploadCsv: (datasetType, file) => {
    const form = new FormData()
    form.append('dataset_type', datasetType)
    form.append('file', file)
    return client.post('/ingestion/upload', form).then((r) => r.data)
  },
  uploadBundle: (files) => {
    const form = new FormData()
    form.append('transactions', files.transactions)
    for (const type of ['vendors', 'budgets', 'receivables']) {
      if (files[type]) form.append(type, files[type])
    }
    return client.post('/ingestion/upload-batch', form).then((r) => r.data)
  },
}

export default api
