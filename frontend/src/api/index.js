import axios from 'axios';

const API_URL = `${process.env.REACT_APP_BACKEND_URL}/api`;

const api = axios.create({
  baseURL: API_URL,
});

// Add token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const uploadCSV = async (file) => {
  const formData = new FormData();
  formData.append('file', file);
  const response = await api.post('/uploads', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  });
  return response.data;
};

export const getUploads = async () => {
  const response = await api.get('/uploads');
  return response.data;
};

export const getInvoices = async (status = null) => {
  const response = await api.get('/invoices', { params: { status } });
  return response.data;
};

export const getInvoice = async (id) => {
  const response = await api.get(`/invoices/${id}`);
  return response.data;
};

export const updateInvoice = async (id, data) => {
  const response = await api.put(`/invoices/${id}`, data);
  return response.data;
};

export const deleteInvoice = async (id) => {
  const response = await api.delete(`/invoices/${id}`);
  return response.data;
};

export const generatePDF = async (id) => {
  const response = await api.post(`/pdf/generate/${id}`);
  return response.data;
};

export const calculateTax = async (amount, state_code, client_address) => {
  const response = await api.post('/tax/calculate', { amount, state_code, client_address });
  return response.data;
};

export const getBranding = async () => {
  const response = await api.get('/branding');
  return response.data;
};

export const updateBranding = async (data) => {
  const response = await api.put('/branding', data);
  return response.data;
};

export const getDashboardStats = async () => {
  const response = await api.get('/dashboard/stats');
  return response.data;
};

export default api;
