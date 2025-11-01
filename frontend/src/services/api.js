import axios from 'axios';

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config) => {
    console.log(`Making ${config.method?.toUpperCase()} request to ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => {
    console.log(`✅ ${response.config.method?.toUpperCase()} ${response.config.url} - Status: ${response.status}`);
    return response.data;
  },
  (error) => {
    console.error('❌ API Error Details:', {
      message: error.message,
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      url: error.config?.url,
      method: error.config?.method
    });
    
    if (error.response) {
      const errorMessage = error.response.data?.error || error.response.data?.message || `API request failed (${error.response.status})`;
      throw new Error(errorMessage);
    } else if (error.request) {
      throw new Error('Network error - please check your connection');
    } else {
      throw new Error('Request failed');
    }
  }
);

export const apiService = {
  // Health check
  healthCheck: () => api.get('/health'),

  // Instruments
  getInstruments: () => api.get('/instruments'),
  getInstrument: (id) => api.get(`/instruments/${id}`),
  createInstrument: (data) => api.post('/instruments', data),
  updateInstrument: (id, data) => api.put(`/instruments/${id}`, data),
  deleteInstrument: (id) => api.delete(`/instruments/${id}`),

  // Price Data
  getPriceData: (instrumentId, limit = 100) => 
    api.get(`/instruments/${instrumentId}/price-data?limit=${limit}`),
  refreshPriceData: (instrumentId) => 
    api.post(`/instruments/${instrumentId}/price-data`),
  getPriceDataRange: (instrumentId, startDate, endDate) => 
    api.get(`/instruments/${instrumentId}/price-data?start_date=${startDate}&end_date=${endDate}`),

  // Models
  getModels: () => api.get('/models'),
  createModel: (modelName, modelParams) => 
    api.post('/models', { model_name: modelName, model_params: modelParams }),
  getModel: (id) => api.get(`/models/${id}`),
  updateModel: (id, data) => api.put(`/models/${id}`, data),
  deleteModel: (id) => api.delete(`/models/${id}`),

  // Training
  trainModel: (modelId, instrumentId) => 
    api.post(`/models/${modelId}/train`, { instrument_id: instrumentId }),
  evaluateModel: (modelId, instrumentId, testPeriodDays = 7) => 
    api.post(`/models/${modelId}/evaluate`, { 
      instrument_id: instrumentId, 
      test_period_days: testPeriodDays 
    }),

  // Forecasting
  generateForecast: (modelId, horizon, confidenceLevel, instrumentId) => 
    api.post(`/models/${modelId}/predict`, {
      horizon,
      confidence_level: confidenceLevel,
      instrument_id: instrumentId
    }),

  // Forecasts
  getForecasts: (instrumentId, limit = 100) => 
    api.get(`/instruments/${instrumentId}/forecasts?limit=${limit}`),
  getForecast: (id) => api.get(`/forecasts/${id}`),
  deleteForecast: (id) => api.delete(`/forecasts/${id}`),

  // Performance Metrics
  getPerformanceMetrics: (modelId) => 
    api.get(`/models/${modelId}/performance`),

  // News Data
  getNewsData: (instrumentId, limit = 100) => 
    api.get(`/instruments/${instrumentId}/news?limit=${limit}`),
  refreshNewsData: (instrumentId) => 
    api.post(`/instruments/${instrumentId}/news`),

  // Adaptive Learning
  adaptiveUpdate: (modelId, instrumentId, learningStrategy = 'incremental') =>
    api.post(`/models/${modelId}/adaptive-update`, {
      instrument_id: instrumentId,
      learning_strategy: learningStrategy
    }),
  createRetrainingSchedule: (modelId, scheduleType, frequencyHours, triggerThreshold) =>
    api.post(`/models/${modelId}/retraining-schedule`, {
      schedule_type: scheduleType,
      frequency_hours: frequencyHours,
      trigger_threshold: triggerThreshold
    }),

  // Continuous Evaluation
  evaluatePrediction: (modelId, forecastId, actualValues, instrumentId) =>
    api.post(`/evaluation/${modelId}/evaluate`, {
      forecast_id: forecastId,
      actual_values: actualValues,
      instrument_id: instrumentId
    }),
  getEvaluationMetrics: (modelId, limit = 50) =>
    api.get(`/evaluation/${modelId}/metrics?limit=${limit}`),
  getForecastErrors: (forecastId) =>
    api.get(`/forecasts/${forecastId}/errors`),

  // Portfolio Management
  createPortfolio: (name, initialCapital) =>
    api.post('/portfolios', {
      name: name,
      initial_capital: initialCapital
    }),
  getPortfolios: () => api.get('/portfolios'),
  getPortfolio: (id) => api.get(`/portfolios/${id}`),
  buyInstrument: (portfolioId, instrumentId, quantity, price, modelId = null) =>
    api.post(`/portfolios/${portfolioId}/buy`, {
      instrument_id: instrumentId,
      quantity: quantity,
      price: price,
      model_id: modelId
    }),
  sellInstrument: (portfolioId, instrumentId, quantity, price, modelId = null) =>
    api.post(`/portfolios/${portfolioId}/sell`, {
      instrument_id: instrumentId,
      quantity: quantity,
      price: price,
      model_id: modelId
    }),
  getPortfolioPositions: (portfolioId) =>
    api.get(`/portfolios/${portfolioId}/positions`),
    getPortfolioMetrics: (portfolioId) =>
      api.get(`/portfolios/${portfolioId}/metrics`),
    getPortfolioMetricsHistory: (portfolioId, limit = 100) =>
      api.get(`/portfolios/${portfolioId}/metrics/history?limit=${limit}`),
    getPortfolioTransactions: (portfolioId, limit = 100) =>
      api.get(`/portfolios/${portfolioId}/transactions?limit=${limit}`),
  deletePortfolio: (portfolioId) =>
    api.delete(`/portfolios/${portfolioId}`),
  deletePortfoliosByName: (name) =>
    api.post('/portfolios/delete-by-name', { name: name }),
};

export default apiService;
