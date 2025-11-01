import React, { useState, useEffect } from 'react';
import { Wallet, TrendingUp, TrendingDown, DollarSign, Activity, Trash2, X } from 'lucide-react';
import apiService from '../services/api';

const PortfolioManager = ({ selectedInstrument, onPortfolioDataUpdate }) => {
  const [portfolios, setPortfolios] = useState([]);
  const [selectedPortfolio, setSelectedPortfolio] = useState(null);
  const [positions, setPositions] = useState([]);
  const [metrics, setMetrics] = useState(null);
  const [transactions, setTransactions] = useState([]);
  const [metricsHistory, setMetricsHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [newPortfolioName, setNewPortfolioName] = useState('');
  const [newPortfolioCapital, setNewPortfolioCapital] = useState(10000);

  useEffect(() => {
    loadPortfolios();
  }, []);

  useEffect(() => {
    if (selectedPortfolio) {
      loadPortfolioData(selectedPortfolio.id);
    }
  }, [selectedPortfolio]);

  const loadPortfolios = async () => {
    try {
      const data = await apiService.getPortfolios();
      setPortfolios(data);
      if (data.length > 0 && !selectedPortfolio) {
        setSelectedPortfolio(data[0]);
      }
    } catch (err) {
      console.error('Error loading portfolios:', err);
      setError(`Failed to load portfolios: ${err.message}`);
    }
  };

  const loadPortfolioData = async (portfolioId) => {
    try {
      setLoading(true);
      const [positionsData, metricsData, transactionsData, historyData] = await Promise.all([
        apiService.getPortfolioPositions(portfolioId),
        apiService.getPortfolioMetrics(portfolioId),
        apiService.getPortfolioTransactions(portfolioId),
        apiService.getPortfolioMetricsHistory(portfolioId, 100).catch(() => []) // Get history, fallback to empty array
      ]);
      
      setPositions(positionsData);
      setMetrics(metricsData);
      setTransactions(transactionsData.slice(0, 10)); // Show last 10 transactions
      setMetricsHistory(historyData);
      
      // Notify parent component if callback provided
      if (onPortfolioDataUpdate) {
        onPortfolioDataUpdate({
          history: historyData,
          initialCapital: metricsData?.initial_capital || 10000
        });
      }
    } catch (err) {
      console.error('Error loading portfolio data:', err);
      setError(`Failed to load portfolio data: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const createPortfolio = async () => {
    try {
      setLoading(true);
      const newPortfolio = await apiService.createPortfolio(newPortfolioName, newPortfolioCapital);
      await loadPortfolios();
      setSelectedPortfolio(newPortfolio);
      setNewPortfolioName('');
      setNewPortfolioCapital(10000);
    } catch (err) {
      console.error('Error creating portfolio:', err);
      setError(`Failed to create portfolio: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const buyInstrument = async (instrumentId, price, quantity) => {
    if (!selectedPortfolio || !instrumentId) return;
    
    try {
      setLoading(true);
      await apiService.buyInstrument(
        selectedPortfolio.id,
        instrumentId,
        quantity,
        price
      );
      await loadPortfolioData(selectedPortfolio.id);
    } catch (err) {
      console.error('Error buying instrument:', err);
      setError(`Failed to buy: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const sellInstrument = async (instrumentId, price, quantity) => {
    if (!selectedPortfolio || !instrumentId) return;
    
    try {
      setLoading(true);
      await apiService.sellInstrument(
        selectedPortfolio.id,
        instrumentId,
        quantity,
        price
      );
      await loadPortfolioData(selectedPortfolio.id);
    } catch (err) {
      console.error('Error selling instrument:', err);
      setError(`Failed to sell: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const deletePortfolio = async (portfolioId) => {
    if (!window.confirm('Are you sure you want to delete this portfolio? This action cannot be undone.')) {
      return;
    }
    
    try {
      setLoading(true);
      await apiService.deletePortfolio(portfolioId);
      
      // Reload portfolios
      const updatedPortfolios = await apiService.getPortfolios();
      setPortfolios(updatedPortfolios);
      
      // Select first portfolio if available
      if (updatedPortfolios.length > 0) {
        setSelectedPortfolio(updatedPortfolios[0]);
      } else {
        setSelectedPortfolio(null);
      }
      
      setSuccess('Portfolio deleted successfully');
    } catch (err) {
      console.error('Error deleting portfolio:', err);
      setError(`Failed to delete portfolio: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const deleteAllWithSameName = async (name) => {
    if (!window.confirm(`Are you sure you want to delete ALL portfolios named "${name}"? This action cannot be undone.`)) {
      return;
    }
    
    try {
      setLoading(true);
      const result = await apiService.deletePortfoliosByName(name);
      
      // Reload portfolios
      const updatedPortfolios = await apiService.getPortfolios();
      setPortfolios(updatedPortfolios);
      
      // Select first portfolio if available
      if (updatedPortfolios.length > 0) {
        setSelectedPortfolio(updatedPortfolios[0]);
      } else {
        setSelectedPortfolio(null);
      }
      
      setSuccess(`Deleted ${result.deleted_count} portfolio(s) with name "${name}"`);
    } catch (err) {
      console.error('Error deleting portfolios:', err);
      setError(`Failed to delete portfolios: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  if (!selectedPortfolio) {
    return (
      <div className="glass-card p-6">
        <h3 className="section-title mb-4">
          <Wallet />
          Portfolio Management
        </h3>
        <div className="space-y-4">
          <div className="text-white/80">No portfolio selected. Create a new portfolio:</div>
          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Portfolio Name"
              value={newPortfolioName}
              onChange={(e) => setNewPortfolioName(e.target.value)}
              className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 modern-input"
            />
            <input
              type="number"
              placeholder="Initial Capital"
              value={newPortfolioCapital}
              onChange={(e) => setNewPortfolioCapital(parseFloat(e.target.value))}
              className="w-32 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 modern-input"
            />
            <button
              onClick={createPortfolio}
              className="modern-btn"
            >
              Create
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Error and Success Messages */}
      {error && (
        <div className="bg-[#ff4444]/10 border border-[#ff4444]/30 rounded-lg p-4 text-[#ff4444] flex items-center justify-between relative z-10" style={{backgroundColor: 'rgba(255, 68, 68, 0.2)', backdropFilter: 'none', borderColor: 'rgba(255, 68, 68, 0.5)'}}>
          <span style={{color: '#ff4444', fontSize: '1rem', fontWeight: '600', textShadow: '0 0 10px rgba(255, 68, 68, 0.5)'}}>{error}</span>
          <button onClick={() => setError(null)} className="text-[#ff4444] hover:text-[#ff6666]" style={{filter: 'drop-shadow(0 0 5px rgba(255, 68, 68, 0.6))'}}>
            <X className="w-4 h-4" />
          </button>
        </div>
      )}
      {success && (
        <div className="bg-[#00ff9f]/10 border border-[#00ff9f]/30 rounded-lg p-4 text-[#00ff9f] flex items-center justify-between relative z-10" style={{backgroundColor: 'rgba(0, 255, 159, 0.2)', backdropFilter: 'none', borderColor: 'rgba(0, 255, 159, 0.5)'}}>
          <span style={{color: '#00ff9f', fontSize: '1rem', fontWeight: '600', textShadow: '0 0 10px rgba(0, 255, 159, 0.5)'}}>{success}</span>
          <button onClick={() => setSuccess(null)} className="text-[#00ff9f] hover:text-[#33ffb3]" style={{filter: 'drop-shadow(0 0 5px rgba(0, 255, 159, 0.6))'}}>
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Portfolio Selector */}
      <div className="glass-card p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="section-title">
            <Wallet />
            Portfolio Management
          </h3>
          <div className="flex items-center gap-2">
            <select
              value={selectedPortfolio.id}
              onChange={(e) => {
                const portfolio = portfolios.find(p => p.id === parseInt(e.target.value));
                setSelectedPortfolio(portfolio);
              }}
              className="modern-input"
            >
              {portfolios.map(p => {
                const duplicateCount = portfolios.filter(port => port.name === p.name).length;
                const displayName = duplicateCount > 1 ? `${p.name} (ID: ${p.id})` : p.name;
                return (
                  <option key={p.id} value={p.id}>{displayName}</option>
                );
              })}
            </select>
            <button
              onClick={() => deletePortfolio(selectedPortfolio.id)}
              className="px-3 py-2 bg-[#ff4444]/10 text-[#ff4444] rounded-lg hover:bg-[#ff4444]/20 border border-[#ff4444]/30 transition"
              title="Delete this portfolio"
            >
              <Trash2 className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Delete duplicates button */}
        {portfolios.filter(p => p.name === selectedPortfolio?.name).length > 1 && (
          <div className="mb-4 p-3 bg-[#00fff2]/10 border border-[#00fff2]/20 rounded-lg backdrop-filter blur-sm">
            <div className="flex items-center justify-between">
              <div className="text-[#00fff2] text-sm">
                ⚠️ Found {portfolios.filter(p => p.name === selectedPortfolio.name).length} portfolios with name "{selectedPortfolio.name}"
              </div>
              <button
                onClick={() => deleteAllWithSameName(selectedPortfolio.name)}
                className="px-4 py-2 bg-[#ff4444]/10 text-[#ff4444] rounded-lg text-sm hover:bg-[#ff4444]/20 border border-[#ff4444]/30 transition flex items-center gap-2"
              >
                <Trash2 className="w-4 h-4" />
                Delete All "{selectedPortfolio.name}"
              </button>
            </div>
          </div>
        )}

        {/* Portfolio Metrics */}
        {metrics && (
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-white/60 text-sm mb-1">Total Value</div>
              <div className="text-2xl font-bold text-white">
                ${metrics.total_value?.toFixed(2) || '0.00'}
              </div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-white/60 text-sm mb-1">Total Return</div>
              <div className={`text-2xl font-bold ${metrics.total_return >= 0 ? 'text-[#00ff9f]' : 'text-[#ff4444]'}`}>
                {metrics.total_return?.toFixed(2) || '0.00'}%
              </div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-white/60 text-sm mb-1">Sharpe Ratio</div>
              <div className="text-2xl font-bold text-white">
                {metrics.sharpe_ratio?.toFixed(2) || '0.00'}
              </div>
            </div>
            <div className="bg-white/5 rounded-lg p-4">
              <div className="text-white/60 text-sm mb-1">Volatility</div>
              <div className="text-2xl font-bold text-white">
                {metrics.volatility?.toFixed(2) || '0.00'}%
              </div>
            </div>
          </div>
        )}

        {/* Positions */}
        <div className="mb-6">
          <h4 className="text-white font-semibold mb-3">Positions</h4>
          {loading ? (
            <div className="text-white/60">Loading...</div>
          ) : positions.length === 0 ? (
            <div className="text-white/60">No positions</div>
          ) : (
            <div className="space-y-2">
              {positions.map(position => (
                <div key={position.id} className="bg-white/5 rounded-lg p-4 flex items-center justify-between">
                  <div>
                    <div className="text-white font-semibold">{position.symbol}</div>
                    <div className="text-white/60 text-sm">
                      {position.quantity.toFixed(4)} @ ${position.average_price.toFixed(2)}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="text-white">
                      ${position.current_value?.toFixed(2) || '0.00'}
                    </div>
                    <div className={`text-sm ${position.unrealized_pnl >= 0 ? 'text-[#00ff9f]' : 'text-[#ff4444]'}`}>
                      {position.unrealized_pnl >= 0 ? '+' : ''}{position.unrealized_pnl_pct?.toFixed(2) || '0.00'}%
                    </div>
                    {selectedInstrument && selectedInstrument.id === position.instrument_id && (
                      <button
                        onClick={() => sellInstrument(position.instrument_id, position.current_price, position.quantity)}
                        className="mt-2 px-4 py-1 bg-red-500/20 text-red-400 rounded text-sm hover:bg-red-500/30 transition"
                      >
                        Sell
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Trading Actions */}
        {selectedInstrument && (
          <div className="bg-white/5 rounded-lg p-4">
            <h4 className="text-white font-semibold mb-3">Trading Actions</h4>
            <div className="space-y-2">
              <div className="flex gap-2">
                <input
                  type="number"
                  placeholder="Quantity"
                  id="buy-quantity"
                  className="flex-1 px-4 py-2 bg-white/5 border border-white/10 rounded-lg text-white placeholder-white/40 modern-input"
                />
                <button
                  onClick={() => {
                    const quantity = parseFloat(document.getElementById('buy-quantity').value);
                    if (quantity > 0 && selectedInstrument) {
                      const currentPrice = positions.find(p => p.instrument_id === selectedInstrument.id)?.current_price || 150;
                      buyInstrument(selectedInstrument.id, currentPrice, quantity);
                    }
                  }}
                  className="px-6 py-2 bg-[#00ff9f]/10 text-[#00ff9f] rounded-lg font-semibold hover:bg-[#00ff9f]/20 border border-[#00ff9f]/30 transition"
                >
                  Buy
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Recent Transactions */}
      {transactions.length > 0 && (
        <div className="glass-card p-6">
          <h4 className="text-white font-semibold mb-3 flex items-center gap-2">
            <Activity />
            Recent Transactions
          </h4>
          <div className="space-y-2">
            {transactions.map(transaction => (
              <div key={transaction.id} className="bg-white/5 rounded-lg p-3 flex items-center justify-between text-sm">
                <div>
                  <div className="text-white font-semibold">{transaction.symbol}</div>
                  <div className="text-white/60">{transaction.transaction_type.toUpperCase()}</div>
                </div>
                <div className="text-right">
                  <div className="text-white">{transaction.quantity.toFixed(4)} @ ${transaction.price.toFixed(2)}</div>
                  <div className="text-white/60">${transaction.total_value.toFixed(2)}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default PortfolioManager;
