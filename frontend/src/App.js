import React, { useState, useEffect } from 'react';
import { TrendingUp } from 'lucide-react';
import CandlestickChart from './components/CandlestickChart';
import InstrumentSelector from './components/InstrumentSelector';
import ModelSelector from './components/ModelSelector';
import ForecastControls from './components/ForecastControls';
import PerformanceMetrics from './components/PerformanceMetrics';
import TechnicalIndicators from './components/TechnicalIndicators';
import LoadingSpinner from './components/LoadingSpinner';
import ErrorMessage from './components/ErrorMessage';
import SuccessMessage from './components/SuccessMessage';
import apiService from './services/api';

function App() {
  const [instruments, setInstruments] = useState([]);
  const [selectedInstrument, setSelectedInstrument] = useState(null);
  const [priceData, setPriceData] = useState([]);
  const [models] = useState(['moving_average', 'arima', 'lstm', 'gru', 'transformer']);
  const [selectedModel, setSelectedModel] = useState('');
  const [trainedModelId, setTrainedModelId] = useState(null);
  const [forecasts, setForecasts] = useState(null);
  const [performanceMetrics, setPerformanceMetrics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [isTraining, setIsTraining] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const [timeRange, setTimeRange] = useState('1w');

  // Load instruments on component mount
  useEffect(() => {
    loadInstruments();
  }, []);

  const loadInstruments = async () => {
    try {
      const data = await apiService.getInstruments();
      setInstruments(data);
    } catch (err) {
      console.error('Error loading instruments:', err);
      setError(`Failed to load instruments: ${err.message}`);
    }
  };

  const loadPriceData = async (instrumentId) => {
    try {
      setLoading(true);
      const data = await apiService.getPriceData(instrumentId, 1000);
      setPriceData(data);
    } catch (err) {
      console.error('Error loading price data:', err);
      setError(`Failed to load price data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const refreshData = async () => {
    if (!selectedInstrument) return;
    
    try {
      setLoading(true);
      setError(null);
      setSuccess(null);
      
      await apiService.refreshPriceData(selectedInstrument.id);
      setSuccess('Data refreshed successfully');
      await loadPriceData(selectedInstrument.id);
    } catch (err) {
      console.error('Error refreshing data:', err);
      setError(`Failed to refresh data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const trainModel = async () => {
    if (!selectedModel || !selectedInstrument) return;
    
    try {
      setIsTraining(true);
      setError(null);
      
      const modelResponse = await apiService.createModel(selectedModel, {});
      const modelId = modelResponse.model_id;
      await apiService.trainModel(modelId, selectedInstrument.id);
      
      setSuccess(`${selectedModel.toUpperCase()} model trained successfully`);
      setTrainedModelId(modelId);
    } catch (err) {
      console.error('Error training model:', err);
      setError(`Failed to train model: ${err.message}`);
    } finally {
      setIsTraining(false);
    }
  };

  const evaluateModel = async () => {
    if (!selectedModel || !selectedInstrument) return;
    
    try {
      setLoading(true);
      setError(null);
      
      let modelId = trainedModelId;
      
      if (!modelId) {
        const modelsData = await apiService.getModels();
        const model = modelsData.find(m => 
          m.model_name === selectedModel && 
          m.instrument_id === selectedInstrument.id
        );
        
        if (!model) {
          setError('Model not found. Please train the model first.');
          return;
        }
        
        modelId = model.model_id;
      }
      
      const data = await apiService.evaluateModel(modelId, selectedInstrument.id, 7);
      setPerformanceMetrics(data.metrics);
      setSuccess('Model evaluation completed');
    } catch (err) {
      console.error('Error evaluating model:', err);
      setError(`Failed to evaluate model: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const generateForecast = async (horizon, confidenceLevel) => {
    if (!selectedModel || !selectedInstrument) return;
    
    try {
      setIsGenerating(true);
      setError(null);
      
      let modelId = trainedModelId;
      
      if (!modelId) {
        const modelsData = await apiService.getModels();
        const model = modelsData.find(m => 
          m.model_name === selectedModel && 
          m.instrument_id === selectedInstrument.id
        );
        
        if (!model) {
          setError('Model not found. Please train the model first.');
          return;
        }
        
        modelId = model.model_id;
      }
      
      const data = await apiService.generateForecast(modelId, horizon, confidenceLevel, selectedInstrument.id);
      setForecasts(data);
      setSuccess(`Forecast generated for ${horizon} hours`);
    } catch (err) {
      console.error('Error generating forecast:', err);
      setError(`Failed to generate forecast: ${err.message}`);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleInstrumentChange = (instrument) => {
    setSelectedInstrument(instrument);
    setTrainedModelId(null);
    if (instrument) {
      loadPriceData(instrument.id);
    }
    setForecasts(null);
    setPerformanceMetrics(null);
  };

  const handleTimeRangeChange = (range) => {
    setTimeRange(range);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-indigo-500 via-purple-500 to-pink-500 relative overflow-hidden">
      {/* Background Effects */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-600/20 via-purple-600/20 to-pink-600/20"></div>
      <div className="absolute top-0 left-0 w-full h-full">
        <div className="absolute top-20 left-20 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-20 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 w-80 h-80 bg-pink-500/10 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="title flex items-center justify-center gap-4">
            <TrendingUp className="w-12 h-12" />
            FinTech Forecasting Dashboard
          </h1>
        </div>

        {/* Messages */}
        {error && <ErrorMessage message={error} />}
        {success && <SuccessMessage message={success} />}

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Left Sidebar */}
          <div className="lg:col-span-1 space-y-6">
            <InstrumentSelector
              instruments={instruments}
              selectedInstrument={selectedInstrument}
              onInstrumentChange={handleInstrumentChange}
              onRefreshData={refreshData}
            />
            
            <ModelSelector
              models={models}
              selectedModel={selectedModel}
              onModelChange={setSelectedModel}
              onTrainModel={trainModel}
              onEvaluateModel={evaluateModel}
              isTraining={isTraining}
              trainedModelId={trainedModelId}
            />
            
            <ForecastControls
              onGenerateForecast={generateForecast}
              isGenerating={isGenerating}
              trainedModelId={trainedModelId}
            />
          </div>
          
          {/* Main Content */}
          <div className="lg:col-span-3 space-y-6">
            {loading ? (
              <LoadingSpinner />
            ) : (
              <>
                <CandlestickChart
                  priceData={priceData}
                  forecasts={forecasts}
                  timeRange={timeRange}
                  onTimeRangeChange={handleTimeRangeChange}
                />
                
                <PerformanceMetrics
                  metrics={performanceMetrics}
                />
                
                <TechnicalIndicators
                  priceData={priceData}
                  forecasts={forecasts}
                />
              </>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
