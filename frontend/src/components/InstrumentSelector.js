import React from 'react';
import { motion } from 'framer-motion';
import { TrendingUp, RefreshCw } from 'lucide-react';

const InstrumentSelector = ({ instruments, selectedInstrument, onInstrumentChange, onRefreshData }) => {
  return (
    <div className="glass-card p-6">
      <h3 className="section-title">
        <TrendingUp />
        Select Financial Instrument
      </h3>
      <div className="space-y-4">
        <div>
          <select 
            className="modern-input w-full" 
            value={selectedInstrument?.id || ''} 
            onChange={(e) => {
              const instrument = instruments.find(i => i.id === parseInt(e.target.value));
              onInstrumentChange(instrument);
            }}
          >
            <option value="">Select an instrument...</option>
            {instruments.map(instrument => (
              <option key={instrument.id} value={instrument.id}>
                {instrument.symbol} - {instrument.name} ({instrument.exchange})
              </option>
            ))}
          </select>
        </div>
        <button 
          className="modern-btn w-full"
          onClick={onRefreshData}
          disabled={!selectedInstrument}
        >
          <RefreshCw className="w-4 h-4 mr-2" />
          Refresh Data
        </button>
        {selectedInstrument && (
          <div className="mt-4 p-4 bg-white/10 rounded-lg">
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div>
                <strong>Symbol:</strong> {selectedInstrument.symbol}
              </div>
              <div>
                <strong>Type:</strong> {selectedInstrument.instrument_type}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default InstrumentSelector;
