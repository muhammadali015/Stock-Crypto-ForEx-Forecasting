"""
Portfolio management system for simulated financial trading.
Supports buy, sell, hold actions based on model predictions or user-defined rules.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass
class Position:
    """Represents a position in a portfolio."""
    instrument_id: int
    quantity: float
    average_price: float
    current_price: float
    
    @property
    def current_value(self) -> float:
        return self.quantity * self.current_price
    
    @property
    def unrealized_pnl(self) -> float:
        return (self.current_price - self.average_price) * self.quantity
    
    @property
    def unrealized_pnl_pct(self) -> float:
        if self.average_price == 0:
            return 0.0
        return ((self.current_price - self.average_price) / self.average_price) * 100


@dataclass
class Transaction:
    """Represents a trading transaction."""
    instrument_id: int
    transaction_type: str  # 'buy' or 'sell'
    quantity: float
    price: float
    total_value: float
    timestamp: datetime
    model_id: Optional[int] = None
    signal_strength: Optional[float] = None


class Portfolio:
    """Manages a simulated financial portfolio."""
    
    def __init__(self, name: str, initial_capital: float, portfolio_id: Optional[int] = None):
        self.portfolio_id = portfolio_id
        self.name = name
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[int, Position] = {}  # {instrument_id: Position}
        self.transaction_history: List[Transaction] = []
        self.performance_history: List[Dict[str, Any]] = []
        
    def buy(self, instrument_id: int, quantity: float, price: float,
            model_id: Optional[int] = None, signal_strength: Optional[float] = None) -> Dict[str, Any]:
        """Execute a buy order."""
        total_cost = quantity * price
        
        if total_cost > self.cash:
            return {
                'success': False,
                'error': 'Insufficient funds',
                'required': total_cost,
                'available': self.cash
            }
        
        # Update position
        if instrument_id in self.positions:
            pos = self.positions[instrument_id]
            # Calculate new average price
            total_quantity = pos.quantity + quantity
            total_cost_old = pos.quantity * pos.average_price
            total_cost_new = quantity * price
            new_avg_price = (total_cost_old + total_cost_new) / total_quantity
            
            self.positions[instrument_id] = Position(
                instrument_id=instrument_id,
                quantity=total_quantity,
                average_price=new_avg_price,
                current_price=price
            )
        else:
            self.positions[instrument_id] = Position(
                instrument_id=instrument_id,
                quantity=quantity,
                average_price=price,
                current_price=price
            )
        
        # Update cash
        self.cash -= total_cost
        
        # Record transaction
        transaction = Transaction(
            instrument_id=instrument_id,
            transaction_type='buy',
            quantity=quantity,
            price=price,
            total_value=total_cost,
            timestamp=datetime.now(),
            model_id=model_id,
            signal_strength=signal_strength
        )
        self.transaction_history.append(transaction)
        
        return {
            'success': True,
            'transaction_id': len(self.transaction_history),
            'remaining_cash': self.cash,
            'position': self.positions[instrument_id]
        }
    
    def sell(self, instrument_id: int, quantity: float, price: float,
            model_id: Optional[int] = None, signal_strength: Optional[float] = None) -> Dict[str, Any]:
        """Execute a sell order."""
        if instrument_id not in self.positions:
            return {
                'success': False,
                'error': 'No position found for this instrument'
            }
        
        pos = self.positions[instrument_id]
        
        if quantity > pos.quantity:
            return {
                'success': False,
                'error': 'Insufficient quantity',
                'required': quantity,
                'available': pos.quantity
            }
        
        # Calculate realized PnL
        realized_pnl = (price - pos.average_price) * quantity
        total_value = quantity * price
        
        # Update position
        if quantity == pos.quantity:
            # Selling entire position
            del self.positions[instrument_id]
        else:
            # Partial sale
            self.positions[instrument_id] = Position(
                instrument_id=instrument_id,
                quantity=pos.quantity - quantity,
                average_price=pos.average_price,  # Average price remains the same
                current_price=price
            )
        
        # Update cash
        self.cash += total_value
        
        # Record transaction
        transaction = Transaction(
            instrument_id=instrument_id,
            transaction_type='sell',
            quantity=quantity,
            price=price,
            total_value=total_value,
            timestamp=datetime.now(),
            model_id=model_id,
            signal_strength=signal_strength
        )
        self.transaction_history.append(transaction)
        
        return {
            'success': True,
            'transaction_id': len(self.transaction_history),
            'realized_pnl': realized_pnl,
            'remaining_cash': self.cash,
            'remaining_position': self.positions.get(instrument_id)
        }
    
    def update_prices(self, price_updates: Dict[int, float]):
        """Update current prices for positions."""
        for instrument_id, price in price_updates.items():
            if instrument_id in self.positions:
                self.positions[instrument_id].current_price = price
    
    @property
    def total_value(self) -> float:
        """Calculate total portfolio value."""
        positions_value = sum(pos.current_value for pos in self.positions.values())
        return self.cash + positions_value
    
    @property
    def total_return(self) -> float:
        """Calculate total return percentage."""
        return ((self.total_value - self.initial_capital) / self.initial_capital) * 100
    
    @property
    def unrealized_pnl(self) -> float:
        """Calculate total unrealized PnL."""
        return sum(pos.unrealized_pnl for pos in self.positions.values())
    
    def get_positions_summary(self) -> List[Dict[str, Any]]:
        """Get summary of all positions."""
        return [
            {
                'instrument_id': pos.instrument_id,
                'quantity': pos.quantity,
                'average_price': pos.average_price,
                'current_price': pos.current_price,
                'current_value': pos.current_value,
                'unrealized_pnl': pos.unrealized_pnl,
                'unrealized_pnl_pct': pos.unrealized_pnl_pct
            }
            for pos in self.positions.values()
        ]
    
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate portfolio performance metrics."""
        if len(self.performance_history) == 0:
            return {
                'total_return': self.total_return,
                'unrealized_pnl': self.unrealized_pnl,
                'sharpe_ratio': 0.0,
                'volatility': 0.0,
                'max_drawdown': 0.0
            }
        
        # Calculate returns
        values = [p['total_value'] for p in self.performance_history]
        returns = np.diff(values) / values[:-1] if len(values) > 1 else [0.0]
        
        # Sharpe ratio (annualized)
        if len(returns) > 0 and np.std(returns) > 0:
            sharpe_ratio = (np.mean(returns) / np.std(returns)) * np.sqrt(252)  # Annualized
        else:
            sharpe_ratio = 0.0
        
        # Volatility (annualized)
        volatility = np.std(returns) * np.sqrt(252) * 100 if len(returns) > 0 else 0.0
        
        # Max drawdown
        cumulative = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = cumulative - running_max
        max_drawdown = np.min(drawdown) * 100 if len(drawdown) > 0 else 0.0
        
        return {
            'total_return': self.total_return,
            'unrealized_pnl': self.unrealized_pnl,
            'sharpe_ratio': sharpe_ratio,
            'volatility': volatility,
            'max_drawdown': max_drawdown,
            'total_value': self.total_value,
            'cash': self.cash
        }
    
    def record_performance_snapshot(self):
        """Record current portfolio state for historical tracking."""
        snapshot = {
            'date': datetime.now().isoformat(),
            'total_value': self.total_value,
            'cash': self.cash,
            'positions_count': len(self.positions),
            'total_return': self.total_return
        }
        
        # Add calculated metrics
        metrics = self.calculate_metrics()
        snapshot.update(metrics)
        
        self.performance_history.append(snapshot)
        
        return snapshot


class TradingStrategy:
    """Base class for trading strategies."""
    
    def generate_signal(self, prediction: float, current_price: float,
                       confidence: float, **kwargs) -> Tuple[str, float]:
        """
        Generate trading signal.
        Returns: (action, quantity) where action is 'buy', 'sell', or 'hold'
        """
        raise NotImplementedError


class SimplePredictionStrategy(TradingStrategy):
    """Simple strategy based on prediction vs current price."""
    
    def __init__(self, threshold_pct: float = 2.0, confidence_threshold: float = 0.7):
        self.threshold_pct = threshold_pct  # Minimum expected gain to trade
        self.confidence_threshold = confidence_threshold
    
    def generate_signal(self, prediction: float, current_price: float,
                       confidence: float, portfolio_value: float = 10000.0, **kwargs) -> Tuple[str, float]:
        """Generate signal based on prediction."""
        if confidence < self.confidence_threshold:
            return ('hold', 0.0)
        
        expected_return_pct = ((prediction - current_price) / current_price) * 100
        
        if expected_return_pct > self.threshold_pct:
            # Buy signal
            # Allocate 10% of portfolio value
            quantity = (portfolio_value * 0.1) / prediction
            return ('buy', quantity)
        elif expected_return_pct < -self.threshold_pct:
            # Sell signal (if we have position)
            return ('sell', 0.0)  # Quantity determined by existing position
        else:
            return ('hold', 0.0)


class MomentumStrategy(TradingStrategy):
    """Momentum-based trading strategy."""
    
    def __init__(self, lookback_period: int = 5, momentum_threshold: float = 0.03):
        self.lookback_period = lookback_period
        self.momentum_threshold = momentum_threshold
    
    def generate_signal(self, price_history: List[float], current_price: float,
                       prediction: float, **kwargs) -> Tuple[str, float]:
        """Generate signal based on momentum."""
        if len(price_history) < self.lookback_period:
            return ('hold', 0.0)
        
        recent_prices = price_history[-self.lookback_period:]
        momentum = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        if momentum > self.momentum_threshold and prediction > current_price:
            return ('buy', 0.0)  # Quantity determined elsewhere
        elif momentum < -self.momentum_threshold and prediction < current_price:
            return ('sell', 0.0)
        else:
            return ('hold', 0.0)


class PortfolioManager:
    """Manages multiple portfolios and trading operations."""
    
    def __init__(self):
        self.portfolios: Dict[int, Portfolio] = {}
        self.strategies: Dict[str, TradingStrategy] = {}
        
    def create_portfolio(self, name: str, initial_capital: float) -> Portfolio:
        """Create a new portfolio."""
        portfolio = Portfolio(name, initial_capital)
        if portfolio.portfolio_id:
            self.portfolios[portfolio.portfolio_id] = portfolio
        return portfolio
    
    def register_strategy(self, name: str, strategy: TradingStrategy):
        """Register a trading strategy."""
        self.strategies[name] = strategy
    
    def execute_strategy(self, portfolio: Portfolio, strategy_name: str,
                        instrument_id: int, prediction: float, current_price: float,
                        confidence: float, **kwargs) -> Dict[str, Any]:
        """Execute a trading strategy."""
        if strategy_name not in self.strategies:
            return {'success': False, 'error': f'Strategy {strategy_name} not found'}
        
        strategy = self.strategies[strategy_name]
        
        # Generate signal
        signal, quantity = strategy.generate_signal(
            prediction=prediction,
            current_price=current_price,
            confidence=confidence,
            portfolio_value=portfolio.total_value,
            **kwargs
        )
        
        # Execute trade
        if signal == 'buy' and quantity > 0:
            return portfolio.buy(instrument_id, quantity, current_price)
        elif signal == 'sell':
            # Sell entire position if available
            if instrument_id in portfolio.positions:
                pos = portfolio.positions[instrument_id]
                return portfolio.sell(instrument_id, pos.quantity, current_price)
            else:
                return {'success': False, 'error': 'No position to sell'}
        else:
            return {'success': True, 'action': 'hold'}
    
    def get_all_portfolio_metrics(self) -> Dict[int, Dict[str, Any]]:
        """Get metrics for all portfolios."""
        return {
            pid: portfolio.calculate_metrics()
            for pid, portfolio in self.portfolios.items()
        }
