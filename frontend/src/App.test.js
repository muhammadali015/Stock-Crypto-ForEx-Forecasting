import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import App from '../App';
import InstrumentSelector from '../components/InstrumentSelector';
import ModelSelector from '../components/ModelSelector';
import ForecastControls from '../components/ForecastControls';
import PerformanceMetrics from '../components/PerformanceMetrics';

// Mock API service
jest.mock('../services/api', () => ({
  getInstruments: jest.fn(() => Promise.resolve([
    { id: 1, symbol: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ', instrument_type: 'STOCK' },
    { id: 2, symbol: 'BTC-USD', name: 'Bitcoin', exchange: 'CRYPTO', instrument_type: 'CRYPTO' }
  ])),
  getPriceData: jest.fn(() => Promise.resolve([
    { id: 1, date: '2023-01-01', open_price: 100, high_price: 105, low_price: 95, close_price: 102, volume: 1000 },
    { id: 2, date: '2023-01-02', open_price: 102, high_price: 108, low_price: 98, close_price: 106, volume: 1200 }
  ])),
  refreshPriceData: jest.fn(() => Promise.resolve({ message: 'Data refreshed successfully' })),
  createModel: jest.fn(() => Promise.resolve({ model_id: 'model123' })),
  trainModel: jest.fn(() => Promise.resolve({ message: 'Model trained successfully' })),
  evaluateModel: jest.fn(() => Promise.resolve({ 
    metrics: { rmse: 0.05, mae: 0.03, mape: 2.5, directional_accuracy: 85.0 }
  })),
  generateForecast: jest.fn(() => Promise.resolve({
    predictions: [110, 112, 115],
    confidence_intervals: { lower: [108, 110, 113], upper: [112, 114, 117] }
  }))
}));

describe('App Component', () => {
  test('renders main dashboard', async () => {
    render(<App />);
    
    expect(screen.getByText('FinTech Forecasting Dashboard')).toBeInTheDocument();
    expect(screen.getByText('Select Financial Instrument')).toBeInTheDocument();
    expect(screen.getByText('Forecasting Models')).toBeInTheDocument();
    expect(screen.getByText('Generate Forecast')).toBeInTheDocument();
  });

  test('loads instruments on mount', async () => {
    render(<App />);
    
    await waitFor(() => {
      expect(screen.getByText('AAPL - Apple Inc. (NASDAQ)')).toBeInTheDocument();
      expect(screen.getByText('BTC-USD - Bitcoin (CRYPTO)')).toBeInTheDocument();
    });
  });
});

describe('InstrumentSelector Component', () => {
  const mockInstruments = [
    { id: 1, symbol: 'AAPL', name: 'Apple Inc.', exchange: 'NASDAQ', instrument_type: 'STOCK' },
    { id: 2, symbol: 'BTC-USD', name: 'Bitcoin', exchange: 'CRYPTO', instrument_type: 'CRYPTO' }
  ];

  test('renders instrument selector', () => {
    render(
      <InstrumentSelector
        instruments={mockInstruments}
        selectedInstrument={null}
        onInstrumentChange={jest.fn()}
        onRefreshData={jest.fn()}
      />
    );

    expect(screen.getByText('Select Financial Instrument')).toBeInTheDocument();
    expect(screen.getByText('Select an instrument...')).toBeInTheDocument();
  });

  test('displays instrument options', () => {
    render(
      <InstrumentSelector
        instruments={mockInstruments}
        selectedInstrument={null}
        onInstrumentChange={jest.fn()}
        onRefreshData={jest.fn()}
      />
    );

    expect(screen.getByText('AAPL - Apple Inc. (NASDAQ)')).toBeInTheDocument();
    expect(screen.getByText('BTC-USD - Bitcoin (CRYPTO)')).toBeInTheDocument();
  });

  test('calls onInstrumentChange when instrument is selected', () => {
    const mockOnInstrumentChange = jest.fn();
    
    render(
      <InstrumentSelector
        instruments={mockInstruments}
        selectedInstrument={null}
        onInstrumentChange={mockOnInstrumentChange}
        onRefreshData={jest.fn()}
      />
    );

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: '1' } });

    expect(mockOnInstrumentChange).toHaveBeenCalledWith(mockInstruments[0]);
  });

  test('displays selected instrument details', () => {
    render(
      <InstrumentSelector
        instruments={mockInstruments}
        selectedInstrument={mockInstruments[0]}
        onInstrumentChange={jest.fn()}
        onRefreshData={jest.fn()}
      />
    );

    expect(screen.getByText('Symbol: AAPL')).toBeInTheDocument();
    expect(screen.getByText('Type: STOCK')).toBeInTheDocument();
  });
});

describe('ModelSelector Component', () => {
  const mockModels = ['moving_average', 'arima', 'lstm', 'gru'];

  test('renders model selector', () => {
    render(
      <ModelSelector
        models={mockModels}
        selectedModel=""
        onModelChange={jest.fn()}
        onTrainModel={jest.fn()}
        onEvaluateModel={jest.fn()}
        isTraining={false}
        trainedModelId={null}
      />
    );

    expect(screen.getByText('Forecasting Models')).toBeInTheDocument();
    expect(screen.getByText('Select a model...')).toBeInTheDocument();
  });

  test('displays model options', () => {
    render(
      <ModelSelector
        models={mockModels}
        selectedModel=""
        onModelChange={jest.fn()}
        onTrainModel={jest.fn()}
        onEvaluateModel={jest.fn()}
        isTraining={false}
        trainedModelId={null}
      />
    );

    expect(screen.getByText('MOVING_AVERAGE')).toBeInTheDocument();
    expect(screen.getByText('ARIMA')).toBeInTheDocument();
    expect(screen.getByText('LSTM')).toBeInTheDocument();
    expect(screen.getByText('GRU')).toBeInTheDocument();
  });

  test('calls onModelChange when model is selected', () => {
    const mockOnModelChange = jest.fn();
    
    render(
      <ModelSelector
        models={mockModels}
        selectedModel=""
        onModelChange={mockOnModelChange}
        onTrainModel={jest.fn()}
        onEvaluateModel={jest.fn()}
        isTraining={false}
        trainedModelId={null}
      />
    );

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'lstm' } });

    expect(mockOnModelChange).toHaveBeenCalledWith('lstm');
  });

  test('shows training state', () => {
    render(
      <ModelSelector
        models={mockModels}
        selectedModel="lstm"
        onModelChange={jest.fn()}
        onTrainModel={jest.fn()}
        onEvaluateModel={jest.fn()}
        isTraining={true}
        trainedModelId={null}
      />
    );

    expect(screen.getByText('Training...')).toBeInTheDocument();
  });

  test('shows trained model status', () => {
    render(
      <ModelSelector
        models={mockModels}
        selectedModel="lstm"
        onModelChange={jest.fn()}
        onTrainModel={jest.fn()}
        onEvaluateModel={jest.fn()}
        isTraining={false}
        trainedModelId="model123"
      />
    );

    expect(screen.getByText('Model trained successfully')).toBeInTheDocument();
  });
});

describe('ForecastControls Component', () => {
  test('renders forecast controls', () => {
    render(
      <ForecastControls
        onGenerateForecast={jest.fn()}
        isGenerating={false}
        trainedModelId="model123"
      />
    );

    expect(screen.getByText('Generate Forecast')).toBeInTheDocument();
    expect(screen.getByText('Forecast Horizon')).toBeInTheDocument();
    expect(screen.getByText('Confidence Level')).toBeInTheDocument();
  });

  test('shows generating state', () => {
    render(
      <ForecastControls
        onGenerateForecast={jest.fn()}
        isGenerating={true}
        trainedModelId="model123"
      />
    );

    expect(screen.getByText('Generating...')).toBeInTheDocument();
  });

  test('shows warning when no model trained', () => {
    render(
      <ForecastControls
        onGenerateForecast={jest.fn()}
        isGenerating={false}
        trainedModelId={null}
      />
    );

    expect(screen.getByText('Please train a model first')).toBeInTheDocument();
  });

  test('calls onGenerateForecast with correct parameters', () => {
    const mockOnGenerateForecast = jest.fn();
    
    render(
      <ForecastControls
        onGenerateForecast={mockOnGenerateForecast}
        isGenerating={false}
        trainedModelId="model123"
      />
    );

    const button = screen.getByText('Generate Forecast');
    fireEvent.click(button);

    expect(mockOnGenerateForecast).toHaveBeenCalledWith(24, 0.95);
  });
});

describe('PerformanceMetrics Component', () => {
  const mockMetrics = {
    rmse: 0.05,
    mae: 0.03,
    mape: 2.5,
    directional_accuracy: 85.0
  };

  test('renders performance metrics', () => {
    render(<PerformanceMetrics metrics={mockMetrics} />);

    expect(screen.getByText('Model Performance')).toBeInTheDocument();
    expect(screen.getByText('RMSE')).toBeInTheDocument();
    expect(screen.getByText('MAE')).toBeInTheDocument();
    expect(screen.getByText('MAPE')).toBeInTheDocument();
    expect(screen.getByText('Directional Accuracy')).toBeInTheDocument();
  });

  test('displays metric values correctly', () => {
    render(<PerformanceMetrics metrics={mockMetrics} />);

    expect(screen.getByText('0.0500')).toBeInTheDocument();
    expect(screen.getByText('0.0300')).toBeInTheDocument();
    expect(screen.getByText('2.50%')).toBeInTheDocument();
    expect(screen.getByText('85.0%')).toBeInTheDocument();
  });

  test('returns null when no metrics provided', () => {
    const { container } = render(<PerformanceMetrics metrics={null} />);
    expect(container.firstChild).toBeNull();
  });

  test('returns null when empty metrics object', () => {
    const { container } = render(<PerformanceMetrics metrics={{}} />);
    expect(container.firstChild).toBeNull();
  });
});
