# app.py - COMPLETE STOCK MARKET ANALYSIS TOOL
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import plotly.express as px
from datetime import datetime, timedelta
import requests
import json
from typing import List, Dict, Tuple
import warnings
import ta
from dateutil.relativedelta import relativedelta
import time
from scipy import stats
from functools import lru_cache

warnings.filterwarnings('ignore')

# ==================== PAGE CONFIG ====================
st.set_page_config(
    page_title="Market Master Pro",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== CUSTOM CSS ====================
st.markdown("""

    /* Main styling */
    .main-header {
        font-size: 2.8rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .sub-header {
        font-size: 1.8rem;
        color: #2c3e50;
        font-weight: 700;
        margin: 1.5rem 0 1rem 0;
        padding-bottom: 0.5rem;
        border-bottom: 3px solid #3498db;
    }
    
    /* Cards */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 12px;
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.08);
        border-left: 5px solid #3498db;
        margin: 0.5rem 0;
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
    }
    
    .stock-card {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.2rem;
        border-radius: 10px;
        margin: 0.8rem 0;
        border: 1px solid #e0e0e0;
    }
    
    .signal-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    
    /* Color schemes */
    .green-text { color: #27ae60; font-weight: 600; }
    .red-text { color: #e74c3c; font-weight: 600; }
    .blue-text { color: #3498db; font-weight: 600; }
    .orange-text { color: #f39c12; font-weight: 600; }
    .purple-text { color: #9b59b6; font-weight: 600; }
    
    /* Progress bars */
    .stProgress > div > div > div > div {
        background-color: #3498db;
    }
    
    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: #f8f9fa;
        border-radius: 8px 8px 0px 0px;
        padding: 10px 20px;
        font-weight: 600;
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    }
    
    /* Dataframes */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
    }
    
    /* Dashboard metrics */
    .dashboard-metric {
        text-align: center;
        padding: 1rem;
    }
    
    .dashboard-metric h3 {
        font-size: 1.2rem;
        color: #7f8c8d;
        margin-bottom: 0.5rem;
    }
    
    .dashboard-metric .value {
        font-size: 2rem;
        font-weight: 700;
    }
    
    /* Alerts */
    .alert-box {
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        background: #fff3cd;
        border: 1px solid #ffeaa7;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .fade-in {
        animation: fadeIn 0.5s ease-out;
    }
    
    /* Tooltips */
    .tooltip {
        position: relative;
        display: inline-block;
        border-bottom: 1px dotted black;
    }
    
    .tooltip .tooltiptext {
        visibility: hidden;
        width: 200px;
        background-color: #2c3e50;
        color: white;
        text-align: center;
        border-radius: 6px;
        padding: 8px;
        position: absolute;
        z-index: 1;
        bottom: 125%;
        left: 50%;
        margin-left: -100px;
        opacity: 0;
        transition: opacity 0.3s;
    }
    
    .tooltip:hover .tooltiptext {
        visibility: visible;
        opacity: 1;
    }

""", unsafe_allow_html=True)

# ==================== DATA MANAGER ====================
class DataManager:
    def __init__(self):
        self.cache = {}
        self.market_status = None
        
    @lru_cache(maxsize=128)
    def get_stock_data(self, symbol: str, period: str = "1mo", interval: str = "1d"):
        """Get stock data with caching"""
        try:
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=period, interval=interval)
            
            if hist.empty:
                # Try alternative period
                if period == "1d":
                    hist = ticker.history(period="5d", interval="5m")
                else:
                    hist = ticker.history(period="1y")
            
            # Get additional info
            info = ticker.info
            
            return {
                'history': hist,
                'info': info,
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'sector': info.get('sector', 'Unknown'),
                'industry': info.get('industry', 'Unknown')
            }
        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return None

# ==================== ANALYSIS ENGINE ====================
class AnalysisEngine:
    def __init__(self):
        self.data_manager = DataManager()
        
    def calculate_technical_indicators(self, df):
        """Calculate comprehensive technical indicators"""
        df = df.copy()
        
        # Price indicators
        df['SMA_20'] = df['Close'].rolling(window=20).mean()
        df['SMA_50'] = df['Close'].rolling(window=50).mean()
        df['SMA_200'] = df['Close'].rolling(window=200).mean()
        
        df['EMA_12'] = df['Close'].ewm(span=12, adjust=False).mean()
        df['EMA_26'] = df['Close'].ewm(span=26, adjust=False).mean()
        
        # Momentum indicators
        df['RSI'] = ta.momentum.RSIIndicator(df['Close'], window=14).rsi()
        
        # MACD
        macd = ta.trend.MACD(df['Close'])
        df['MACD'] = macd.macd()
        df['MACD_Signal'] = macd.macd_signal()
        df['MACD_Diff'] = macd.macd_diff()
        
        # Volatility
        bb = ta.volatility.BollingerBands(df['Close'], window=20, window_dev=2)
        df['BB_Upper'] = bb.bollinger_hband()
        df['BB_Lower'] = bb.bollinger_lband()
        df['BB_Middle'] = bb.bollinger_mavg()
        
        # Volume indicators
        df['Volume_SMA'] = df['Volume'].rolling(window=20).mean()
        df['Volume_Ratio'] = df['Volume'] / df['Volume_SMA']
        
        # ATR for volatility measurement
        df['ATR'] = ta.volatility.AverageTrueRange(
            df['High'], df['Low'], df['Close'], window=14
        ).average_true_range()
        
        # Support and Resistance levels (simplified)
        df['Resistance_1'] = df['High'].rolling(20).max()
        df['Support_1'] = df['Low'].rolling(20).min()
        
        return df
    
    def analyze_stock(self, symbol: str, analysis_type: str = "both"):
        """Comprehensive stock analysis"""
        data = self.data_manager.get_stock_data(symbol, period="6mo")
        
        if not data or data['history'].empty:
            return None
        
        df = data['history']
        info = data['info']
        
        # Add technical indicators
        df = self.calculate_technical_indicators(df)
        
        analysis = {
            'symbol': symbol,
            'name': data['name'],
            'sector': data['sector'],
            'industry': data['industry'],
            'current_price': df['Close'].iloc[-1],
            'prev_close': df['Close'].iloc[-2] if len(df) > 1 else df['Close'].iloc[-1],
            'volume': df['Volume'].iloc[-1],
            'market_cap': info.get('marketCap', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'forward_pe': info.get('forwardPE', 0),
            'peg_ratio': info.get('pegRatio', 0),
            'pb_ratio': info.get('priceToBook', 0),
            'ps_ratio': info.get('priceToSalesTrailing12Months', 0),
            'dividend_yield': info.get('dividendYield', 0) * 100 if info.get('dividendYield') else 0,
            'beta': info.get('beta', 1),
            'debt_to_equity': info.get('debtToEquity', 0),
            'return_on_equity': info.get('returnOnEquity', 0),
            'profit_margins': info.get('profitMargins', 0),
            'revenue_growth': info.get('revenueGrowth', 0),
            'earnings_growth': info.get('earningsGrowth', 0),
            'technical_data': df,
            'info': info
        }
        
        # Calculate metrics
        analysis['daily_change'] = ((analysis['current_price'] - analysis['prev_close']) / analysis['prev_close']) * 100
        
        # Technical signals
        analysis['signals'] = self.get_technical_signals(df)
        
        # Calculate scores
        analysis['technical_score'] = self.calculate_technical_score(df)
        analysis['fundamental_score'] = self.calculate_fundamental_score(analysis)
        analysis['momentum_score'] = self.calculate_momentum_score(df)
        analysis['volatility_score'] = self.calculate_volatility_score(df)
        
        return analysis
    
    def get_technical_signals(self, df):
        """Extract technical trading signals"""
        signals = []
        
        if len(df) < 30:
            return signals
        
        current_rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
        current_price = df['Close'].iloc[-1]
        sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else current_price
        sma_50 = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else current_price
        macd_diff = df['MACD_Diff'].iloc[-1] if not pd.isna(df['MACD_Diff'].iloc[-1]) else 0
        
        # RSI signals
        if current_rsi < 30:
            signals.append(("RSI Oversold", "buy", "Bullish reversal possible"))
        elif current_rsi > 70:
            signals.append(("RSI Overbought", "sell", "Bearish reversal possible"))
        
        # Moving average signals
        if current_price > sma_20 > sma_50:
            signals.append(("Golden Cross", "buy", "Strong uptrend"))
        elif current_price < sma_20 < sma_50:
            signals.append(("Death Cross", "sell", "Strong downtrend"))
        
        # MACD signals
        if macd_diff > 0:
            signals.append(("MACD Bullish", "buy", "Positive momentum"))
        else:
            signals.append(("MACD Bearish", "sell", "Negative momentum"))
        
        # Bollinger Bands signals
        bb_upper = df['BB_Upper'].iloc[-1] if not pd.isna(df['BB_Upper'].iloc[-1]) else current_price
        bb_lower = df['BB_Lower'].iloc[-1] if not pd.isna(df['BB_Lower'].iloc[-1]) else current_price
        
        if current_price <= bb_lower * 1.02:
            signals.append(("BB Lower Touch", "buy", "Potential bounce"))
        elif current_price >= bb_upper * 0.98:
            signals.append(("BB Upper Touch", "sell", "Potential pullback"))
        
        # Volume signals
        volume_ratio = df['Volume_Ratio'].iloc[-1] if not pd.isna(df['Volume_Ratio'].iloc[-1]) else 1
        if volume_ratio > 1.5:
            signals.append(("High Volume", "alert", "Unusual activity"))
        
        return signals
    
    def calculate_technical_score(self, df):
        """Calculate technical analysis score (0-100)"""
        score = 50
        
        if len(df) < 20:
            return score
        
        # Add scoring based on technical indicators
        current_rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
        current_price = df['Close'].iloc[-1]
        
        # RSI scoring (ideal: 40-60)
        if 40 <= current_rsi <= 60:
            score += 15
        elif 30 <= current_rsi <= 70:
            score += 10
        else:
            score += 5
        
        # Trend scoring
        sma_20 = df['SMA_20'].iloc[-1] if not pd.isna(df['SMA_20'].iloc[-1]) else current_price
        sma_50 = df['SMA_50'].iloc[-1] if not pd.isna(df['SMA_50'].iloc[-1]) else current_price
        
        if current_price > sma_20 > sma_50:
            score += 20  # Strong uptrend
        elif current_price < sma_20 < sma_50:
            score += 10  # Strong downtrend
        
        # Volume scoring
        volume_ratio = df['Volume_Ratio'].iloc[-1] if not pd.isna(df['Volume_Ratio'].iloc[-1]) else 1
        if 0.8 <= volume_ratio <= 1.2:
            score += 10  # Normal volume
        
        # MACD scoring
        macd_diff = df['MACD_Diff'].iloc[-1] if not pd.isna(df['MACD_Diff'].iloc[-1]) else 0
        if macd_diff > 0:
            score += 5
        
        return min(100, max(0, score))
    
    def calculate_fundamental_score(self, analysis):
        """Calculate fundamental analysis score (0-100)"""
        score = 50
        
        # P/E ratio scoring (lower is better, but not too low)
        pe = analysis['pe_ratio']
        if 0 < pe < 20:
            score += 15
        elif 20 <= pe < 30:
            score += 10
        elif pe >= 30:
            score += 5
        
        # Profit margin scoring
        profit_margin = analysis['profit_margins']
        if profit_margin > 0.2:
            score += 20
        elif profit_margin > 0.1:
            score += 15
        elif profit_margin > 0:
            score += 10
        
        # ROE scoring
        roe = analysis['return_on_equity']
        if roe > 0.15:
            score += 15
        elif roe > 0:
            score += 10
        
        # Revenue growth scoring
        rev_growth = analysis['revenue_growth']
        if rev_growth > 0.1:
            score += 10
        elif rev_growth > 0:
            score += 5
        
        # Debt to equity scoring (lower is better)
        dte = analysis['debt_to_equity']
        if dte < 0.5:
            score += 10
        elif dte < 1:
            score += 5
        
        return min(100, max(0, score))
    
    def calculate_momentum_score(self, df):
        """Calculate momentum score (0-100)"""
        if len(df) < 20:
            return 50
        
        score = 50
        
        # Price momentum (last 20 days vs 50 days)
        if len(df) >= 50:
            price_change_20 = (df['Close'].iloc[-1] / df['Close'].iloc[-20] - 1) * 100
            price_change_50 = (df['Close'].iloc[-1] / df['Close'].iloc[-50] - 1) * 100
            
            if price_change_20 > 5:
                score += 15
            elif price_change_20 > 0:
                score += 10
            
            if price_change_50 > 10:
                score += 10
            elif price_change_50 > 0:
                score += 5
        
        # RSI momentum
        rsi = df['RSI'].iloc[-1] if not pd.isna(df['RSI'].iloc[-1]) else 50
        if 50 < rsi <= 70:
            score += 10
        elif rsi > 70:
            score -= 5
        
        return min(100, max(0, score))
    
    def calculate_volatility_score(self, df):
        """Calculate volatility score (higher = more volatile)"""
        if len(df) < 20:
            return 50
        
        # Calculate daily returns
        returns = df['Close'].pct_change().dropna()
        
        if len(returns) == 0:
            return 50
        
        # Volatility (annualized)
        volatility = returns.std() * np.sqrt(252) * 100
        
        # Convert to score (0-100)
        score = min(100, max(0, volatility * 5))
        
        return score
    
    def screen_intraday_stocks(self):
        """Screen for intraday trading opportunities"""
        intraday_watchlist = [
            ('SPY', 'S&P 500 ETF', 'ETF'),
            ('QQQ', 'Nasdaq 100 ETF', 'ETF'),
            ('AAPL', 'Apple Inc.', 'Technology'),
            ('MSFT', 'Microsoft Corp', 'Technology'),
            ('NVDA', 'NVIDIA Corp', 'Semiconductors'),
            ('TSLA', 'Tesla Inc.', 'Automotive'),
            ('AMD', 'Advanced Micro Devices', 'Semiconductors'),
            ('AMZN', 'Amazon.com Inc.', 'E-Commerce'),
            ('GOOGL', 'Alphabet Inc.', 'Technology'),
            ('META', 'Meta Platforms', 'Technology'),
            ('JPM', 'JPMorgan Chase', 'Financial'),
            ('BAC', 'Bank of America', 'Financial'),
            ('GS', 'Goldman Sachs', 'Financial'),
            ('IWM', 'Russell 2000 ETF', 'ETF'),
            ('TLT', '20+ Year Treasury ETF', 'ETF'),
            ('GLD', 'SPDR Gold Trust', 'Commodities'),
            ('USO', 'US Oil Fund', 'Commodities'),
            ('VIXY', 'VIX Short-Term Futures', 'Volatility')
        ]
        
        results = []
        
        for symbol, name, category in intraday_watchlist:
            try:
                data = self.data_manager.get_stock_data(symbol, period="5d", interval="5m")
                
                if data and not data['history'].empty:
                    df = data['history']
                    
                    # Calculate intraday metrics
                    if len(df) >= 10:
                        current_price = df['Close'].iloc[-1]
                        open_price = df['Open'].iloc[0] if len(df) > 0 else current_price
                        high_price = df['High'].max()
                        low_price = df['Low'].min()
                        
                        daily_range = ((high_price - low_price) / low_price) * 100
                        current_change = ((current_price - open_price) / open_price) * 100
                        
                        avg_volume = df['Volume'].mean()
                        recent_volume = df['Volume'].iloc[-1]
                        volume_ratio = recent_volume / avg_volume if avg_volume > 0 else 1
                        
                        # Calculate intraday momentum
                        recent_returns = df['Close'].pct_change().dropna()
                        momentum = recent_returns.tail(5).mean() * 100 if len(recent_returns) >= 5 else 0
                        
                        signals = []
                        if daily_range > 2:
                            signals.append("High Range")
                        if volume_ratio > 1.5:
                            signals.append("High Volume")
                        if abs(current_change) > 1:
                            signals.append("Active Move")
                        
                        results.append({
                            'symbol': symbol,
                            'name': name,
                            'category': category,
                            'current_price': current_price,
                            'open_price': open_price,
                            'change_pct': current_change,
                            'daily_range': daily_range,
                            'volume_ratio': volume_ratio,
                            'momentum': momentum,
                            'signals': signals,
                            'liquidity_score': self.calculate_liquidity_score(df),
                            'opportunity_score': self.calculate_intraday_opportunity_score(
                                daily_range, volume_ratio, momentum
                            )
                        })
                        
            except Exception as e:
                continue
        
        # Sort by opportunity score
        results.sort(key=lambda x: x['opportunity_score'], reverse=True)
        return results
    
    def calculate_liquidity_score(self, df):
        """Calculate liquidity score based on volume"""
        if df.empty or 'Volume' not in df.columns:
            return 50
        
        avg_volume = df['Volume'].mean()
        
        if avg_volume > 10000000:
            return 95
        elif avg_volume > 5000000:
            return 85
        elif avg_volume > 1000000:
            return 75
        elif avg_volume > 500000:
            return 65
        else:
            return 50
    
    def calculate_intraday_opportunity_score(self, daily_range, volume_ratio, momentum):
        """Calculate intraday trading opportunity score"""
        score = 50
        
        # Range scoring (higher range = more opportunity)
        score += min(25, daily_range * 5)
        
        # Volume scoring (higher volume = better liquidity)
        score += min(15, (volume_ratio - 1) * 30)
        
        # Momentum scoring (absolute momentum)
        score += min(10, abs(momentum) * 5)
        
        return min(100, max(0, score))
    
    def screen_longterm_stocks(self):
        """Screen for long-term investment opportunities"""
        longterm_watchlist = [
            ('JNJ', 'Johnson & Johnson', 'Healthcare'),
            ('PG', 'Procter & Gamble', 'Consumer Staples'),
            ('JPM', 'JPMorgan Chase', 'Financial'),
            ('HD', 'Home Depot', 'Consumer Discretionary'),
            ('UNH', 'UnitedHealth Group', 'Healthcare'),
            ('V', 'Visa Inc.', 'Financial'),
            ('MA', 'Mastercard', 'Financial'),
            ('DIS', 'Walt Disney', 'Entertainment'),
            ('KO', 'Coca-Cola', 'Consumer Staples'),
            ('PEP', 'PepsiCo', 'Consumer Staples'),
            ('MRK', 'Merck & Co', 'Healthcare'),
            ('ABBV', 'AbbVie', 'Healthcare'),
            ('CVX', 'Chevron', 'Energy'),
            ('XOM', 'Exxon Mobil', 'Energy'),
            ('WMT', 'Walmart', 'Consumer Staples'),
            ('COST', 'Costco', 'Consumer Staples'),
            ('MCD', "McDonald's", 'Consumer Discretionary'),
            ('NKE', 'Nike', 'Consumer Discretionary'),
            ('TMO', 'Thermo Fisher Scientific', 'Healthcare'),
            ('LLY', 'Eli Lilly', 'Healthcare'),
            ('TXN', 'Texas Instruments', 'Semiconductors'),
            ('ADBE', 'Adobe', 'Software'),
            ('CRM', 'Salesforce', 'Software'),
            ('ORCL', 'Oracle', 'Software'),
            ('IBM', 'IBM', 'Technology')
        ]
        
        results = []
        
        for symbol, name, sector in longterm_watchlist:
            try:
                analysis = self.analyze_stock(symbol)
                
                if analysis:
                    # Calculate long-term metrics
                    quality_score = analysis['fundamental_score']
                    growth_potential = self.calculate_growth_potential(analysis)
                    stability_score = self.calculate_stability_score(analysis)
                    
                    risk_factors = []
                    if analysis['beta'] > 1.5:
                        risk_factors.append(f"High Beta ({analysis['beta']:.2f})")
                    if analysis['debt_to_equity'] > 2:
                        risk_factors.append(f"High Debt (D/E: {analysis['debt_to_equity']:.2f})")
                    if analysis['pe_ratio'] > 50:
                        risk_factors.append(f"High P/E ({analysis['pe_ratio']:.1f})")
                    
                    # Calculate long-term score
                    longterm_score = (
                        quality_score * 0.4 +
                        growth_potential * 0.3 +
                        stability_score * 0.3
                    )
                    
                    # Dividend assessment
                    dividend_score = self.calculate_dividend_score(analysis)
                    
                    # ESG factors (simplified)
                    esg_factors = []
                    if 'Healthcare' in sector or 'Consumer Staples' in sector:
                        esg_factors.append("Defensive Sector")
                    if analysis['dividend_yield'] > 2:
                        esg_factors.append("Dividend Payer")
                    
                    results.append({
                        'symbol': symbol,
                        'name': name,
                        'sector': sector,
                        'current_price': analysis['current_price'],
                        'market_cap': analysis['market_cap'],
                        'pe_ratio': analysis['pe_ratio'],
                        'dividend_yield': analysis['dividend_yield'],
                        'quality_score': quality_score,
                        'growth_potential': growth_potential,
                        'stability_score': stability_score,
                        'longterm_score': longterm_score,
                        'dividend_score': dividend_score,
                        'risk_factors': risk_factors,
                        'esg_factors': esg_factors,
                        'recommendation': self.get_longterm_recommendation(longterm_score, risk_factors)
                    })
                    
            except Exception as e:
                continue
        
        # Sort by long-term score
        results.sort(key=lambda x: x['longterm_score'], reverse=True)
        return results
    
    def calculate_growth_potential(self, analysis):
        """Calculate growth potential score"""
        score = 50
        
        # Revenue growth
        rev_growth = analysis['revenue_growth']
        if rev_growth > 0.15:
            score += 30
        elif rev_growth > 0.1:
            score += 20
        elif rev_growth > 0.05:
            score += 10
        elif rev_growth > 0:
            score += 5
        
        # Earnings growth
        earnings_growth = analysis['earnings_growth']
        if earnings_growth > 0.2:
            score += 20
        elif earnings_growth > 0.1:
            score += 15
        elif earnings_growth > 0.05:
            score += 10
        elif earnings_growth > 0:
            score += 5
        
        # Sector growth potential
        sector = analysis['sector']
        if sector in ['Technology', 'Healthcare', 'Clean Energy']:
            score += 10
        elif sector in ['Consumer Discretionary', 'Communication Services']:
            score += 5
        
        return min(100, max(0, score))
    
    def calculate_stability_score(self, analysis):
        """Calculate stability score"""
        score = 70  # Base for established companies
        
        # Profit margins
        profit_margin = analysis['profit_margins']
        if profit_margin > 0.2:
            score += 15
        elif profit_margin > 0.1:
            score += 10
        elif profit_margin > 0:
            score += 5
        
        # Debt levels
        dte = analysis['debt_to_equity']
        if dte < 0.5:
            score += 10
        elif dte < 1:
            score += 5
        elif dte > 2:
            score -= 10
        
        # Beta (volatility)
        beta = analysis['beta']
        if beta < 0.8:
            score += 10  # Less volatile than market
        elif beta > 1.2:
            score -= 5   # More volatile than market
        
        # Market cap (larger = more stable)
        market_cap = analysis['market_cap']
        if market_cap > 100e9:  # > $100B
            score += 10
        elif market_cap > 10e9:  # > $10B
            score += 5
        
        return min(100, max(0, score))
    
    def calculate_dividend_score(self, analysis):
        """Calculate dividend safety and growth score"""
        score = 0
        
        dividend_yield = analysis['dividend_yield']
        
        if dividend_yield > 4:
            score += 40  # High yield
        elif dividend_yield > 2:
            score += 60  # Moderate yield (often more sustainable)
        elif dividend_yield > 0:
            score += 30  # Low yield
        
        # Additional factors
        if analysis['profit_margins'] > 0.15:
            score += 20  # Profitable
        
        if analysis['debt_to_equity'] < 1:
            score += 20  # Low debt
        
        if analysis['market_cap'] > 50e9:
            score += 20  # Large cap stability
        
        return min(100, max(0, score))
    
    def get_longterm_recommendation(self, score, risk_factors):
        """Generate long-term recommendation"""
        if score >= 80 and len(risk_factors) == 0:
            return "Strong Buy - Core Holding"
        elif score >= 70 and len(risk_factors) <= 1:
            return "Buy - Accumulate"
        elif score >= 60:
            return "Hold - Monitor"
        elif score >= 50:
            return "Hold - Risk Aware"
        else:
            return "Review Required"
    
    def get_market_overview(self):
        """Get overall market overview"""
        indices = ['^GSPC', '^IXIC', '^DJI', '^RUT', '^VIX']
        overview = {}
        
        for index in indices:
            try:
                data = self.data_manager.get_stock_data(index, period="1d")
                if data and not data['history'].empty:
                    df = data['history']
                    
                    current = df['Close'].iloc[-1]
                    prev_close = df['Close'].iloc[-2] if len(df) > 1 else current
                    
                    overview[index] = {
                        'name': self.get_index_name(index),
                        'price': current,
                        'change': current - prev_close,
                        'change_pct': ((current - prev_close) / prev_close) * 100,
                        'volume': df['Volume'].iloc[-1] if 'Volume' in df.columns else 0
                    }
            except:
                continue
        
        return overview
    
    def get_index_name(self, symbol):
        """Get friendly name for index symbol"""
        names = {
            '^GSPC': 'S&P 500',
            '^IXIC': 'Nasdaq',
            '^DJI': 'Dow Jones',
            '^RUT': 'Russell 2000',
            '^VIX': 'VIX Fear Index'
        }
        return names.get(symbol, symbol)
    
    def get_sector_performance(self):
        """Get sector performance data"""
        # Sector ETF symbols
        sectors = {
            'XLK': 'Technology',
            'XLV': 'Healthcare',
            'XLE': 'Energy',
            'XLF': 'Financials',
            'XLI': 'Industrials',
            'XLP': 'Consumer Staples',
            'XLY': 'Consumer Discretionary',
            'XLU': 'Utilities',
            'XLC': 'Communication',
            'XLB': 'Materials',
            'XLRE': 'Real Estate'
        }
        
        performance = []
        
        for symbol, name in sectors.items():
            try:
                data = self.data_manager.get_stock_data(symbol, period="1mo")
                if data and not data['history'].empty:
                    df = data['history']
                    
                    current = df['Close'].iloc[-1]
                    month_ago = df['Close'].iloc[0] if len(df) > 20 else current
                    
                    performance.append({
                        'sector': name,
                        'symbol': symbol,
                        'current': current,
                        'month_change': ((current - month_ago) / month_ago) * 100,
                        'volume': df['Volume'].iloc[-1] if 'Volume' in df.columns else 0
                    })
            except:
                continue
        
        # Sort by performance
        performance.sort(key=lambda x: x['month_change'], reverse=True)
        return performance

# ==================== VISUALIZATION ====================
class VisualizationEngine:
    def __init__(self):
        self.colors = px.colors.qualitative.Set3
    
    def create_candlestick_chart(self, df, title="Stock Chart"):
        """Create interactive candlestick chart"""
        fig = go.Figure(data=[
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price',
                increasing_line_color='#27ae60',
                decreasing_line_color='#e74c3c'
            )
        ])
        
        fig.update_layout(
            title={
                'text': title,
                'y':0.95,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24, color='#2c3e50')
            },
            yaxis_title='Price ($)',
            xaxis_title='Date',
            template='plotly_white',
            height=500,
            hovermode='x unified',
            showlegend=True,
            xaxis_rangeslider_visible=False,
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0.9)',
            font=dict(family="Arial, sans-serif")
        )
        
        return fig
    
    def create_technical_chart(self, df, title="Technical Analysis"):
        """Create comprehensive technical analysis chart"""
        fig = make_subplots(
            rows=3, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            row_heights=[0.6, 0.2, 0.2],
            subplot_titles=('Price & Moving Averages', 'Volume', 'RSI & MACD')
        )
        
        # Candlestick with moving averages
        fig.add_trace(
            go.Candlestick(
                x=df.index,
                open=df['Open'],
                high=df['High'],
                low=df['Low'],
                close=df['Close'],
                name='Price',
                increasing_line_color='#27ae60',
                decreasing_line_color='#e74c3c'
            ),
            row=1, col=1
        )
        
        # Moving averages
        if 'SMA_20' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['SMA_20'],
                    name='SMA 20',
                    line=dict(color='#3498db', width=2),
                    opacity=0.8
                ),
                row=1, col=1
            )
        
        if 'SMA_50' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['SMA_50'],
                    name='SMA 50',
                    line=dict(color='#e74c3c', width=2),
                    opacity=0.8
                ),
                row=1, col=1
            )
        
        if 'SMA_200' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['SMA_200'],
                    name='SMA 200',
                    line=dict(color='#9b59b6', width=2),
                    opacity=0.8
                ),
                row=1, col=1
            )
        
        # Volume
        colors = ['#e74c3c' if df['Close'].iloc[i] < df['Open'].iloc[i] else '#27ae60' 
                 for i in range(len(df))]
        
        fig.add_trace(
            go.Bar(
                x=df.index,
                y=df['Volume'],
                name='Volume',
                marker_color=colors,
                opacity=0.7
            ),
            row=2, col=1
        )
        
        # RSI
        if 'RSI' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['RSI'],
                    name='RSI',
                    line=dict(color='#f39c12', width=2)
                ),
                row=3, col=1
            )
            
            # RSI bands
            fig.add_hline(y=70, line_dash="dash", line_color="#e74c3c", opacity=0.5, row=3, col=1)
            fig.add_hline(y=30, line_dash="dash", line_color="#27ae60", opacity=0.5, row=3, col=1)
            fig.add_hline(y=50, line_dash="dot", line_color="#7f8c8d", opacity=0.3, row=3, col=1)
        
        # MACD
        if 'MACD' in df.columns and 'MACD_Signal' in df.columns:
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['MACD'],
                    name='MACD',
                    line=dict(color='#3498db', width=2)
                ),
                row=3, col=1
            )
            
            fig.add_trace(
                go.Scatter(
                    x=df.index,
                    y=df['MACD_Signal'],
                    name='Signal',
                    line=dict(color='#e74c3c', width=2)
                ),
                row=3, col=1
            )
        
        fig.update_layout(
            title={
                'text': title,
                'y':0.98,
                'x':0.5,
                'xanchor': 'center',
                'yanchor': 'top',
                'font': dict(size=24, color='#2c3e50')
            },
            template='plotly_white',
            height=800,
            hovermode='x unified',
            showlegend=True,
            xaxis_rangeslider_visible=False,
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0.9)',
            font=dict(family="Arial, sans-serif")
        )
        
        fig.update_xaxes(title_text="Date", row=3, col=1)
        fig.update_yaxes(title_text="Price ($)", row=1, col=1)
        fig.update_yaxes(title_text="Volume", row=2, col=1)
        fig.update_yaxes(title_text="RSI/MACD", row=3, col=1)
        
        return fig
    
    def create_gauge_chart(self, value, title="Score", min_val=0, max_val=100):
        """Create gauge chart for scores"""
        fig = go.Figure(go.Indicator(
            mode="gauge+number+delta",
            value=value,
            domain={'x': [0, 1], 'y': [0, 1]},
            title={'text': title, 'font': {'size': 20}},
            delta={'reference': 50},
            gauge={
                'axis': {'range': [min_val, max_val]},
                'bar': {'color': "#3498db"},
                'steps': [
                    {'range': [0, 33], 'color': "#e74c3c"},
                    {'range': [33, 66], 'color': "#f39c12"},
                    {'range': [66, 100], 'color': "#27ae60"}
                ],
                'threshold': {
                    'line': {'color': "black", 'width': 4},
                    'thickness': 0.75,
                    'value': value
                }
            }
        ))
        
        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=50, b=20),
            paper_bgcolor='rgba(255, 255, 255, 0.9)'
        )
        
        return fig
    
    def create_sector_performance_chart(self, sectors):
        """Create sector performance heatmap"""
        df = pd.DataFrame(sectors)
        
        fig = px.bar(
            df,
            x='sector',
            y='month_change',
            color='month_change',
            color_continuous_scale=['#e74c3c', '#f39c12', '#27ae60'],
            title='Sector Performance (1 Month)',
            labels={'month_change': 'Change (%)', 'sector': 'Sector'},
            text_auto='.1f'
        )
        
        fig.update_layout(
            height=500,
            xaxis_tickangle=-45,
            template='plotly_white',
            plot_bgcolor='rgba(240, 240, 240, 0.5)',
            paper_bgcolor='rgba(255, 255, 255, 0.9)',
            font=dict(family="Arial, sans-serif")
        )
        
        fig.update_traces(
            textposition='outside',
            marker_line_color='black',
            marker_line_width=0.5
        )
        
        return fig

# ==================== MAIN APPLICATION ====================
class StockMarketTool:
    def __init__(self):
        self.analysis_engine = AnalysisEngine()
        self.viz_engine = VisualizationEngine()
        self.current_symbol = "AAPL"
        self.user_portfolio = {}
        
    def run(self):
        """Main application runner"""
        # Sidebar
        self.render_sidebar()
        
        # Main content based on selected tab
        self.render_main_content()
        
        # Footer with disclaimer
        self.render_footer()
    
    def render_sidebar(self):
        """Render sidebar with controls"""
        with st.sidebar:
            st.image("https://img.icons8.com/color/96/000000/stock-share.png", width=80)
            st.markdown('Market Master Pro', unsafe_allow_html=True)
            st.markdown("---")
            
            # Quick Access
            st.markdown("### 🔍 Quick Analysis")
            self.current_symbol = st.text_input("Stock Symbol", value="AAPL").upper()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔍 Analyze", use_container_width=True):
                    st.session_state.analyze_symbol = self.current_symbol
            
            with col2:
                if st.button("📊 Overview", use_container_width=True):
                    st.session_state.current_tab = "Market Overview"
            
            st.markdown("---")
            
            # User Profile
            st.markdown("### 👤 Investor Profile")
            self.user_profile = {
                'risk_tolerance': st.select_slider(
                    "Risk Tolerance",
                    options=["Very Conservative", "Conservative", "Moderate", "Aggressive", "Very Aggressive"],
                    value="Moderate"
                ),
                'investment_horizon': st.select_slider(
                    "Time Horizon",
                    options=["Intraday", "Swing (Days)", "Short-term (Weeks)", "Medium-term (Months)", "Long-term (Years)"],
                    value="Long-term (Years)"
                ),
                'capital': st.number_input(
                    "Investment Capital ($)",
                    min_value=1000,
                    max_value=1000000,
                    value=25000,
                    step=5000
                ),
                'strategy': st.selectbox(
                    "Primary Strategy",
                    ["Growth", "Dividend", "Value", "Momentum", "Balanced"]
                )
            }
            
            st.markdown("---")
            
            # Scanner Settings
            st.markdown("### ⚙️ Scanner Settings")
            
            intraday_settings = {
                'min_volume': st.number_input("Min Volume (M)", value=1.0, min_value=0.1, step=0.5),
                'min_volatility': st.slider("Min Volatility %", 0.5, 5.0, 1.5, 0.5),
                'max_volatility': st.slider("Max Volatility %", 2.0, 10.0, 5.0, 0.5)
            }
            
            longterm_settings = {
                'min_market_cap': st.selectbox(
                    "Min Market Cap",
                    ["Any", "$1B+", "$10B+", "$50B+", "$100B+"],
                    index=2
                ),
                'max_pe': st.number_input("Max P/E Ratio", value=30.0, min_value=5.0, max_value=100.0, step=5.0),
                'min_dividend': st.number_input("Min Dividend Yield %", value=0.0, min_value=0.0, max_value=10.0, step=0.5),
                'sectors': st.multiselect(
                    "Preferred Sectors",
                    ["Technology", "Healthcare", "Financials", "Consumer", "Energy", "Industrial", "All"],
                    default=["All"]
                )
            }
            
            st.session_state.scanner_settings = {
                'intraday': intraday_settings,
                'longterm': longterm_settings
            }
            
            st.markdown("---")
            
            # Quick Links
            st.markdown("### ⚡ Quick Actions")
            
            if st.button("🔄 Refresh All Data", use_container_width=True):
                st.rerun()
            
            if st.button("📈 Intraday Scanner", use_container_width=True):
                st.session_state.current_tab = "Intraday Scanner"
            
            if st.button("🏆 Long-term Picks", use_container_width=True):
                st.session_state.current_tab = "Long-term Investments"
            
            if st.button("📊 Portfolio Builder", use_container_width=True):
                st.session_state.current_tab = "Portfolio Builder"
            
            if st.button("🛡️ Risk Tools", use_container_width=True):
                st.session_state.current_tab = "Risk Management"
    
    def render_main_content(self):
        """Render main content area"""
        # Initialize session state
        if 'current_tab' not in st.session_state:
            st.session_state.current_tab = "Market Overview"
        
        # Create tabs
        tabs = st.tabs([
            "📊 Market Overview",
            "🔍 Stock Analyzer",
            "⚡ Intraday Scanner", 
            "🏆 Long-term Investments",
            "📊 Portfolio Builder",
            "🛡️ Risk Management",
            "📚 Learning Center"
        ])
        
        # Tab 1: Market Overview
        with tabs[0]:
            self.render_market_overview()
        
        # Tab 2: Stock Analyzer
        with tabs[1]:
            self.render_stock_analyzer()
        
        # Tab 3: Intraday Scanner
        with tabs[2]:
            self.render_intraday_scanner()
        
        # Tab 4: Long-term Investments
        with tabs[3]:
            self.render_longterm_investments()
        
        # Tab 5: Portfolio Builder
        with tabs[4]:
            self.render_portfolio_builder()
        
        # Tab 6: Risk Management
        with tabs[5]:
            self.render_risk_management()
        
        # Tab 7: Learning Center
        with tabs[6]:
            self.render_learning_center()
    
    def render_market_overview(self):
        """Render market overview dashboard"""
        st.markdown('📊 Market Overview Dashboard', unsafe_allow_html=True)
        
        # Fetch market data
        with st.spinner("Loading market data..."):
            market_data = self.analysis_engine.get_market_overview()
            sector_data = self.analysis_engine.get_sector_performance()
        
        # Market Indices
        st.markdown('📈 Major Indices', unsafe_allow_html=True)
        
        cols = st.columns(5)
        indices = ['^GSPC', '^IXIC', '^DJI', '^RUT', '^VIX']
        
        for idx, symbol in enumerate(indices):
            with cols[idx]:
                if symbol in market_data:
                    data = market_data[symbol]
                    delta_color = "normal"
                    
                    st.metric(
                        label=data['name'],
                        value=f"${data['price']:.2f}",
                        delta=f"{data['change_pct']:.2f}%"
                    )
        
        # Market Summary
        st.markdown('📋 Market Summary', unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Market Sentiment
            st.markdown('', unsafe_allow_html=True)
            st.markdown("### 📊 Market Sentiment")
            
            # Calculate sentiment
            bullish_count = sum(1 for s in ['^GSPC', '^IXIC', '^DJI'] 
                               if s in market_data and market_data[s]['change_pct'] > 0)
            
            if bullish_count >= 2:
                sentiment = "Bullish"
                sentiment_color = "green-text"
                sentiment_icon = "🟢"
            elif bullish_count == 1:
                sentiment = "Neutral"
                sentiment_color = "blue-text"
                sentiment_icon = "🔵"
            else:
                sentiment = "Bearish"
                sentiment_color = "red-text"
                sentiment_icon = "🔴"
            
            st.markdown(f'### {sentiment_icon} {sentiment}', 
                       unsafe_allow_html=True)
            
            # VIX analysis
            if '^VIX' in market_data:
                vix = market_data['^VIX']['price']
                if vix > 30:
                    st.markdown(f"**VIX**: {vix:.1f} (High Fear)", unsafe_allow_html=True)
                elif vix < 15:
                    st.markdown(f"**VIX**: {vix:.1f} (Low Fear)", unsafe_allow_html=True)
                else:
                    st.markdown(f"**VIX**: {vix:.1f} (Neutral)")
            
            st.markdown('', unsafe_allow_html=True)
        
        with col2:
            # Economic Indicators
            st.markdown('', unsafe_allow_html=True)
            st.markdown("### 📅 Key Levels")
            
            levels = [
                ("S&P 500 Support", "4,600 - 4,650"),
                ("S&P 500 Resistance", "4,750 - 4,800"),
                ("Nasdaq Support", "16,000 - 16,200"), 
                ("Nasdaq Resistance", "16,800 - 17,000"),
                ("Critical VIX Level", "18.0")
            ]
            
            for level, value in levels:
                st.markdown(f"- **{level}**: {value}")
            
            st.markdown('', unsafe_allow_html=True)
        
        # Sector Performance
        st.markdown('🏢 Sector Performance', unsafe_allow_html=True)
        
        if sector_data:
            # Create sector chart
            chart = self.viz_engine.create_sector_performance_chart(sector_data)
            st.plotly_chart(chart, use_container_width=True)
            
            # Top and bottom performers
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('', unsafe_allow_html=True)
                st.markdown("### 🥇 Top Performers")
                for sector in sector_data[:3]:
                    change_color = "green-text" if sector['month_change'] > 0 else "red-text"
                    st.markdown(f"**{sector['sector']}**: {sector['month_change']:.1f}%",
                               unsafe_allow_html=True)
                st.markdown('', unsafe_allow_html=True)
            
            with col2:
                st.markdown('', unsafe_allow_html=True)
                st.markdown("### 🥉 Bottom Performers")
                for sector in sector_data[-3:]:
                    change_color = "green-text" if sector['month_change'] > 0 else "red-text"
                    st.markdown(f"**{sector['sector']}**: {sector['month_change']:.1f}%",
                               unsafe_allow_html=True)
                st.markdown('', unsafe_allow_html=True)
        
        # Market News (simulated)
        st.markdown('📰 Market News', unsafe_allow_html=True)
        
        news_items = [
            ("Fed Meeting This Week", "Markets await interest rate decision", "High Impact"),
            ("Earnings Season Begins", "Tech giants report this week", "Medium Impact"),
            ("Oil Prices Volatile", "Middle East tensions affect supply", "High Impact"),
            ("AI Conference Highlights", "New tech announcements expected", "Low Impact")
        ]
        
        for title, description, impact in news_items:
            with st.expander(f"{title} - {impact}"):
                st.markdown(description)
                if impact == "High Impact":
                    st.warning("⚠️ High impact on markets expected")
                elif impact == "Medium Impact":
                    st.info("ℹ️ Moderate market impact possible")
    
    def render_stock_analyzer(self):
        """Render individual stock analyzer"""
        st.markdown('🔍 Stock Analyzer', unsafe_allow_html=True)
        
        # Input section
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            symbol = st.text_input("Enter Stock Symbol", 
                                  value=st.session_state.get('analyze_symbol', 'AAPL')).upper()
        
        with col2:
            period = st.selectbox(
                "Time Period",
                ["1mo", "3mo", "6mo", "1y", "2y", "5y"],
                index=2
            )
        
        with col3:
            if st.button("Analyze Stock", type="primary", use_container_width=True):
                st.session_state.current_analysis = symbol
        
        # Main analysis
        if 'current_analysis' in st.session_state or symbol:
            analyze_symbol = st.session_state.get('current_analysis', symbol)
            
            with st.spinner(f"Analyzing {analyze_symbol}..."):
                analysis = self.analysis_engine.analyze_stock(analyze_symbol)
                
                if analysis:
                    # Header with key metrics
                    st.markdown(f"## {analysis['name']} ({analyze_symbol})")
                    
                    # Quick stats
                    cols = st.columns(6)
                    stats = [
                        ("Price", f"${analysis['current_price']:.2f}", 
                         f"{analysis['daily_change']:+.2f}%"),
                        ("Market Cap", f"${analysis['market_cap']/1e9:.1f}B", ""),
                        ("P/E Ratio", f"{analysis['pe_ratio']:.1f}", ""),
                        ("Dividend", f"{analysis['dividend_yield']:.2f}%", ""),
                        ("Beta", f"{analysis['beta']:.2f}", ""),
                        ("ROE", f"{analysis['return_on_equity']*100:.1f}%", "")
                    ]
                    
                    for idx, (label, value, change) in enumerate(stats):
                        with cols[idx]:
                            if change:
                                st.metric(label, value, change)
                            else:
                                st.metric(label, value)
                    
                    # Charts
                    tab1, tab2, tab3 = st.tabs(["📈 Price Chart", "📊 Technical Analysis", "📋 Fundamentals"])
                    
                    with tab1:
                        chart = self.viz_engine.create_candlestick_chart(
                            analysis['technical_data'],
                            f"{analyze_symbol} Price Chart"
                        )
                        st.plotly_chart(chart, use_container_width=True)
                    
                    with tab2:
                        tech_chart = self.viz_engine.create_technical_chart(
                            analysis['technical_data'],
                            f"{analyze_symbol} Technical Analysis"
                        )
                        st.plotly_chart(tech_chart, use_container_width=True)
                        
                        # Technical signals
                        st.markdown("### 🚦 Technical Signals")
                        if analysis['signals']:
                            cols = st.columns(3)
                            for idx, (signal, action, reason) in enumerate(analysis['signals'][:6]):
                                with cols[idx % 3]:
                                    color = "#27ae60" if action == "buy" else "#e74c3c" if action == "sell" else "#f39c12"
                                    st.markdown(f''
                                               f'{signal}'
                                               f'{reason}'
                                               f'', unsafe_allow_html=True)
                        else:
                            st.info("No strong technical signals detected")
                    
                    with tab3:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("### 📊 Valuation Metrics")
                            metrics = [
                                ("P/E Ratio", analysis['pe_ratio']),
                                ("Forward P/E", analysis['forward_pe']),
                                ("P/B Ratio", analysis['pb_ratio']),
                                ("P/S Ratio", analysis['ps_ratio']),
                                ("PEG Ratio", analysis['peg_ratio']),
                                ("Dividend Yield", analysis['dividend_yield'])
                            ]
                            
                            for name, value in metrics:
                                if value:
                                    st.metric(name, f"{value:.2f}")
                        
                        with col2:
                            st.markdown("### 📈 Growth Metrics")
                            metrics = [
                                ("Revenue Growth", analysis['revenue_growth'] * 100),
                                ("Earnings Growth", analysis['earnings_growth'] * 100),
                                ("Profit Margin", analysis['profit_margins'] * 100),
                                ("Return on Equity", analysis['return_on_equity'] * 100),
                                ("Debt to Equity", analysis['debt_to_equity']),
                                ("Beta", analysis['beta'])
                            ]
                            
                            for name, value in metrics:
                                if value is not None:
                                    st.metric(name, f"{value:.2f}{'%' if name != 'Beta' and name != 'Debt to Equity' else ''}")
                    
                    # Scores
                    st.markdown("### 🎯 Analysis Scores")
                    
                    score_cols = st.columns(4)
                    
                    scores = [
                        ("Technical Score", analysis['technical_score']),
                        ("Fundamental Score", analysis['fundamental_score']),
                        ("Momentum Score", analysis['momentum_score']),
                        ("Volatility Score", analysis['volatility_score'])
                    ]
                    
                    for idx, (name, score) in enumerate(scores):
                        with score_cols[idx]:
                            chart = self.viz_engine.create_gauge_chart(score, name)
                            st.plotly_chart(chart, use_container_width=True)
                    
                    # Recommendations
                    st.markdown("### 💡 Investment Recommendation")
                    
                    total_score = (
                        analysis['technical_score'] * 0.3 +
                        analysis['fundamental_score'] * 0.4 +
                        analysis['momentum_score'] * 0.3
                    )
                    
                    if total_score >= 75:
                        st.success(f"**STRONG BUY** - Overall Score: {total_score:.0f}/100")
                        st.markdown("This stock shows strong fundamentals, positive momentum, and good technical setup.")
                    elif total_score >= 60:
                        st.info(f"**BUY** - Overall Score: {total_score:.0f}/100")
                        st.markdown("Good investment opportunity with balanced risk-reward profile.")
                    elif total_score >= 50:
                        st.warning(f"**HOLD** - Overall Score: {total_score:.0f}/100")
                        st.markdown("Neutral outlook. Consider waiting for better entry or monitoring closely.")
                    else:
                        st.error(f"**AVOID/SELL** - Overall Score: {total_score:.0f}/100")
                        st.markdown("High risk or poor fundamentals detected. Consider reducing exposure.")
                    
                    # Position Sizing
                    st.markdown("### 🎯 Position Sizing Calculator")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        account_size = st.number_input("Account Size ($)", 
                                                      value=self.user_profile['capital'],
                                                      min_value=1000, step=1000)
                    
                    with col2:
                        risk_percent = st.slider("Risk per Trade (%)", 
                                                min_value=0.5, max_value=5.0, 
                                                value=2.0, step=0.5)
                    
                    with col3:
                        stop_loss = st.slider("Stop Loss (%)", 
                                             min_value=1.0, max_value=10.0, 
                                             value=5.0, step=0.5)
                    
                    risk_amount = account_size * (risk_percent / 100)
                    position_size = risk_amount / (analysis['current_price'] * (stop_loss / 100))
                    
                    st.markdown(f"""
                    **Position Calculation:**
                    - Risk Amount: ${risk_amount:.2f}
                    - Stop Loss: {stop_loss}% (${analysis['current_price'] * (stop_loss/100):.2f})
                    - **Position Size: {position_size:.0f} shares**
                    - **Position Value: ${position_size * analysis['current_price']:.2f}**
                    """)
                
                else:
                    st.error(f"Could not fetch data for {analyze_symbol}. Please check the symbol and try again.")
        
        else:
            st.info("👆 Enter a stock symbol above to begin analysis")
    
    def render_intraday_scanner(self):
        """Render intraday trading scanner"""
        st.markdown('⚡ Intraday Trading Scanner', unsafe_allow_html=True)
        st.markdown("### Real-time scanning for high-probability intraday opportunities")
        
        # Scanner controls
        col1, col2 = st.columns([2, 1])
        
        with col1:
            if st.button("🚀 Scan for Opportunities", type="primary", use_container_width=True):
                st.session_state.run_intraday_scan = True
        
        with col2:
            update_freq = st.selectbox("Update Frequency", 
                                      ["5 min", "15 min", "30 min", "1 hour"], 
                                      index=1)
        
        # Run scan
        if st.session_state.get('run_intraday_scan', False):
            with st.spinner("Scanning market for intraday opportunities..."):
                results = self.analysis_engine.screen_intraday_stocks()
                
                if results:
                    # Top Opportunities
                    st.markdown(f"### 🎯 Top {len(results)} Intraday Opportunities")
                    
                    # Filters
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        min_score = st.slider("Minimum Opportunity Score", 50, 100, 70)
                    
                    with col2:
                        max_volatility = st.slider("Max Volatility %", 1.0, 10.0, 5.0)
                    
                    with col3:
                        min_volume = st.slider("Min Volume Ratio", 0.5, 3.0, 1.0)
                    
                    # Filter results
                    filtered_results = [
                        r for r in results 
                        if (r['opportunity_score'] >= min_score and 
                            r['daily_range'] <= max_volatility and
                            r['volume_ratio'] >= min_volume)
                    ]
                    
                    if filtered_results:
                        # Display results
                        for i, stock in enumerate(filtered_results[:15]):  # Show top 15
                            with st.container():
                                col1, col2, col3, col4 = st.columns([1, 2, 2, 2])
                                
                                with col1:
                                    st.markdown(f'', unsafe_allow_html=True)
                                    st.markdown(f"**{stock['symbol']}**")
                                    st.markdown(f"*{stock['category']}*")
                                    st.markdown('', unsafe_allow_html=True)
                                
                                with col2:
                                    st.markdown(f"**{stock['name']}**")
                                    st.markdown(f"Price: ${stock['current_price']:.2f}")
                                    
                                    change_color = "green-text" if stock['change_pct'] >= 0 else "red-text"
                                    st.markdown(f"Change: {stock['change_pct']:+.2f}%",
                                               unsafe_allow_html=True)
                                    
                                    st.markdown(f"Range: {stock['daily_range']:.2f}%")
                                
                                with col3:
                                    st.markdown("**Signals**")
                                    for signal in stock['signals'][:3]:
                                        st.markdown(f"• {signal}")
                                    
                                    st.markdown(f"Vol Ratio: {stock['volume_ratio']:.1f}x")
                                    st.markdown(f"Momentum: {stock['momentum']:+.2f}%")
                                
                                with col4:
                                    st.markdown("**Scores**")
                                    
                                    # Opportunity score progress bar
                                    opp_score = stock['opportunity_score']
                                    st.progress(opp_score / 100, 
                                                text=f"Opportunity: {opp_score:.0f}/100")
                                    
                                    # Liquidity score
                                    liq_score = stock['liquidity_score']
                                    color = "#27ae60" if liq_score >= 70 else "#f39c12" if liq_score >= 50 else "#e74c3c"
                                    st.markdown(f"Liquidity: {liq_score:.0f}/100",
                                               unsafe_allow_html=True)
                                    
                                    # Quick action buttons
                                    if st.button(f"Analyze {stock['symbol']}", key=f"analyze_{i}"):
                                        st.session_state.current_analysis = stock['symbol']
                                        st.rerun()
                                
                                st.markdown("---")
                        
                        # Strategy Recommendations
                        st.markdown("### 🎯 Intraday Trading Strategies")
                        
                        cols = st.columns(3)
                        
                        with cols[0]:
                            st.markdown('', unsafe_allow_html=True)
                            st.markdown("#### 📈 Momentum Trading")
                            st.markdown("**Best for**: NVDA, AMD, TSLA")
                            st.markdown("""
                            - Trade with strong trends
                            - Enter on pullbacks to moving averages
                            - Use ATR for stop placement
                            - Target 2-3% gains
                            """)
                            st.markdown('', unsafe_allow_html=True)
                        
                        with cols[1]:
                            st.markdown('', unsafe_allow_html=True)
                            st.markdown("#### 🔄 Mean Reversion")
                            st.markdown("**Best for**: SPY, QQQ, IWM")
                            st.markdown("""
                            - Fade extreme moves
                            - Enter at Bollinger Band extremes
                            - Use RSI oversold/overbought
                            - Target 1-2% bounce
                            """)
                            st.markdown('', unsafe_allow_html=True)
                        
                        with cols[2]:
                            st.markdown('', unsafe_allow_html=True)
                            st.markdown("#### 🚀 Breakout Trading")
                            st.markdown("**Best for**: AAPL, MSFT, GOOGL")
                            st.markdown("""
                            - Enter on new highs/lows
                            - Confirm with volume surge
                            - Trail stops from entry
                            - Target 3-5% moves
                            """)
                            st.markdown('', unsafe_allow_html=True)
                        
                        # Risk Management
                        st.markdown("### 🛡️ Intraday Risk Management")
                        
                        risk_cols = st.columns(4)
                        
                        with risk_cols[0]:
                            max_trades = st.number_input("Max Trades/Day", 1, 20, 5)
                        
                        with risk_cols[1]:
                            max_loss = st.number_input("Max Daily Loss %", 1.0, 10.0, 3.0)
                        
                        with risk_cols[2]:
                            stop_type = st.selectbox("Stop Type", 
                                                    ["Fixed %", "ATR-based", "Moving Average"])
                        
                        with risk_cols[3]:
                            profit_target = st.number_input("Profit Target %", 
                                                          1.0, 10.0, 3.0)
                        
                        st.info(f"""
                        **Risk Parameters:**
                        - Maximum {max_trades} trades per day
                        - Stop trading after {max_loss}% daily loss
                        - {stop_type} stops
                        - {profit_target}% profit targets
                        - Risk-Reward Ratio: 1:{profit_target/max_loss:.1f}
                        """)
                    
                    else:
                        st.warning("No opportunities match your current filters. Try adjusting your criteria.")
                
                else:
                    st.error("Could not fetch intraday data. Market may be closed.")
            
            # Auto-refresh option
            if st.checkbox("Auto-refresh scans"):
                refresh_seconds = {"5 min": 300, "15 min": 900, "30 min": 1800, "1 hour": 3600}
                time.sleep(2)
                st.rerun()
        
        else:
            # Pre-scan instructions
            st.markdown("""
            ### 🎯 What This Scanner Finds:
            
            **High Probability Intraday Setups:**
            
            1. **Momentum Movers** - Stocks with strong directional movement
            2. **Volume Surges** - Unusual trading activity
            3. **Breakout Candidates** - Stocks at key technical levels
            4. **Mean Reversion Plays** - Oversold/overbought opportunities
            
            ### ⚡ Recommended Intraday Stocks:
            
            | Symbol | Volatility | Liquidity | Best For |
            |--------|------------|-----------|----------|
            | **SPY/QQQ** | Medium | Very High | Core market exposure |
            | **AAPL/MSFT** | Low-Med | Very High | Reliable blue-chip moves |
            | **NVDA/AMD** | High | High | Momentum & volatility |
            | **TSLA** | Very High | High | Aggressive momentum |
            | **IWM** | Medium | High | Small-cap beta plays |
            
            Click **'Scan for Opportunities'** to begin!
            """)
    
    def render_longterm_investments(self):
        """Render long-term investment screener"""
        st.markdown('🏆 Long-term Investment Screener', unsafe_allow_html=True)
        st.markdown("### Fundamental analysis for wealth building & dividend growth")
        
        # Strategy selection
        col1, col2, col3 = st.columns(3)
        
        with col1:
            strategy = st.selectbox(
                "Investment Strategy",
                ["Dividend Growth", "Value Investing", "Growth at Reasonable Price", 
                 "Blue Chip Core", "Sector Rotation", "ESG Focus"]
            )
        
        with col2:
            time_horizon = st.select_slider(
                "Time Horizon",
                options=["1-3 years", "3-5 years", "5-10 years", "10+ years"],
                value="5-10 years"
            )
        
        with col3:
            if st.button("🔍 Find Investments", type="primary", use_container_width=True):
                st.session_state.run_longterm_scan = True
        
        if st.session_state.get('run_longterm_scan', False):
            with st.spinner("Analyzing long-term investment opportunities..."):
                results = self.analysis_engine.screen_longterm_stocks()
                
                if results:
                    # Portfolio Construction
                    st.markdown("### 📊 Portfolio Allocation")
                    
                    # Strategy-based allocation
                    allocations = {
                        "Dividend Growth": {"Dividend": 60, "Growth": 30, "Value": 10},
                        "Value Investing": {"Value": 70, "Dividend": 20, "Growth": 10},
                        "Growth at Reasonable Price": {"Growth": 50, "Value": 30, "Dividend": 20},
                        "Blue Chip Core": {"Blue Chip": 80, "Dividend": 15, "Growth": 5},
                        "Sector Rotation": {"Cyclical": 40, "Defensive": 40, "Growth": 20},
                        "ESG Focus": {"ESG Leaders": 70, "Clean Energy": 20, "Sustainable": 10}
                    }
                    
                    allocation = allocations.get(strategy, allocations["Dividend Growth"])
                    
                    col1, col2, col3 = st.columns(3)
                    for i, (category, percent) in enumerate(allocation.items()):
                        st.markdown(f"**{category}**: {percent}% (${self.user_profile['capital'] * percent/100:,.0f})")
                    
                    # Investment Recommendations
                    st.markdown(f"### 🏆 Top {len(results)} Long-term Picks")
                    
                    # Convert to DataFrame for better display
                    df_display = pd.DataFrame(results)[[
                        'symbol', 'name', 'sector', 'current_price', 
                        'dividend_yield', 'pe_ratio', 'quality_score',
                        'longterm_score', 'recommendation'
                    ]]
                    
                    # Style the DataFrame
                    def color_score(val):
                        if val >= 80:
                            color = '#27ae60'
                        elif val >= 60:
                            color = '#f39c12'
                        else:
                            color = '#e74c3c'
                        return f'color: {color}; font-weight: bold'
                    
                    styled_df = df_display.style.applymap(
                        lambda x: color_score(x) if isinstance(x, (int, float)) and x <= 100 else '', 
                        subset=['quality_score', 'longterm_score']
                    )
                    
                    st.dataframe(
                        styled_df,
                        column_config={
                            "symbol": "Symbol",
                            "name": "Company",
                            "sector": "Sector", 
                            "current_price": st.column_config.NumberColumn("Price", format="$%.2f"),
                            "dividend_yield": st.column_config.NumberColumn("Div Yield %", format="%.2f%%"),
                            "pe_ratio": st.column_config.NumberColumn("P/E", format="%.1f"),
                            "quality_score": st.column_config.NumberColumn("Quality", format="%.0f"),
                            "longterm_score": st.column_config.NumberColumn("Total Score", format="%.0f"),
                            "recommendation": "Recommendation"
                        },
                        use_container_width=True,
                        height=400
                    )
                    
                    # Detailed Analysis
                    st.markdown("### 🔍 Detailed Analysis")
                    
                    # Top 5 picks
                    top_picks = results[:5]
                    
                    for pick in top_picks:
                        with st.expander(f"📊 {pick['symbol']} - {pick['name']} (Score: {pick['longterm_score']:.0f}/100)"):
                            col1, col2 = st.columns(2)
                            
                            with col1:
                                st.markdown("**Investment Thesis**")
                                st.markdown(f"""
                                - **Sector**: {pick['sector']}
                                - **Market Cap**: ${pick['market_cap']/1e9:.1f}B
                                - **Strategy Fit**: {strategy}
                                """)
                                
                                st.markdown("**Key Strengths**")
                                if pick['quality_score'] >= 80:
                                    st.markdown("- Excellent fundamentals")
                                if pick['growth_potential'] >= 70:
                                    st.markdown("- Strong growth potential")
                                if pick['stability_score'] >= 80:
                                    st.markdown("- High stability")
                                if pick['dividend_score'] >= 60:
                                    st.markdown("- Attractive dividend profile")
                                
                                if pick['esg_factors']:
                                    st.markdown("**ESG Factors**")
                                    for factor in pick['esg_factors']:
                                        st.markdown(f"- {factor}")
                            
                            with col2:
                                st.markdown("**Risk Assessment**")
                                if pick['risk_factors']:
                                    for risk in pick['risk_factors']:
                                        st.markdown(f"- ⚠️ {risk}")
                                else:
                                    st.markdown("- ✅ No major risk factors detected")
                                
                                st.markdown("**Allocation Suggestion**")
                                
                                # Calculate suggested allocation
                                if pick['longterm_score'] >= 80:
                                    allocation_pct = 8.0
                                elif pick['longterm_score'] >= 70:
                                    allocation_pct = 5.0
                                elif pick['longterm_score'] >= 60:
                                    allocation_pct = 3.0
                                else:
                                    allocation_pct = 1.0
                                
                                suggested_allocation = st.slider(
                                    f"Allocation to {pick['symbol']} (%)",
                                    min_value=1.0,
                                    max_value=20.0,
                                    value=allocation_pct,
                                    step=0.5,
                                    key=f"alloc_{pick['symbol']}"
                                )
                                
                                position_value = self.user_profile['capital'] * (suggested_allocation / 100)
                                shares = position_value / pick['current_price']
                                
                                st.markdown(f"""
                                **Position Details:**
                                - Allocation: {suggested_allocation}%
                                - Value: ${position_value:,.0f}
                                - Shares: {shares:.0f}
                                - Annual Dividend: ${position_value * (pick['dividend_yield']/100):,.0f}
                                """)
                    
                    # Portfolio Summary
                    st.markdown("### 📈 Portfolio Summary")
                    
                    # Calculate portfolio metrics
                    selected_symbols = st.multiselect(
                        "Select stocks for your portfolio:",
                        options=[r['symbol'] for r in results],
                        default=[r['symbol'] for r in results[:5]]
                    )
                    
                    if selected_symbols:
                        selected_stocks = [r for r in results if r['symbol'] in selected_symbols]
                        
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            avg_quality = np.mean([s['quality_score'] for s in selected_stocks])
                            st.metric("Avg Quality", f"{avg_quality:.1f}/100")
                        
                        with col2:
                            avg_dividend = np.mean([s['dividend_yield'] for s in selected_stocks])
                            st.metric("Avg Dividend", f"{avg_dividend:.2f}%")
                        
                        with col3:
                            avg_pe = np.mean([s['pe_ratio'] for s in selected_stocks])
                            st.metric("Avg P/E", f"{avg_pe:.1f}")
                        
                        with col4:
                            portfolio_beta = np.mean([1.0 for s in selected_stocks])  # Simplified
                            st.metric("Portfolio Beta", f"{portfolio_beta:.2f}")
                        
                        # Portfolio characteristics
                        st.markdown("#### 🏗️ Portfolio Characteristics")
                        
                        sectors = {}
                        for stock in selected_stocks:
                            sectors[stock['sector']] = sectors.get(stock['sector'], 0) + 1
                        
                        # Create sector distribution chart
                        sector_df = pd.DataFrame({
                            'Sector': list(sectors.keys()),
                            'Count': list(sectors.values())
                        })
                        
                        fig = px.pie(sector_df, values='Count', names='Sector', 
                                    title='Portfolio Sector Distribution')
                        st.plotly_chart(fig, use_container_width=True)
                        
                        st.success(f"""
                        **Portfolio Construction Complete:**
                        - {len(selected_stocks)} stocks selected
                        - Projected dividend income: ${self.user_profile['capital'] * avg_dividend/100:,.0f}/year
                        - Diversified across {len(sectors)} sectors
                        - Average quality score: {avg_quality:.1f}/100
                        """)
                    
                    # Investment Checklist
                    st.markdown("### ✅ Long-term Investment Checklist")
                    
                    checklist = [
                        "✅ Strong competitive moat",
                        "✅ Consistent revenue growth", 
                        "✅ Healthy profit margins",
                        "✅ Manageable debt levels",
                        "✅ Proven management team",
                        "✅ Industry leadership position",
                        "✅ Sustainable dividend (if applicable)",
                        "✅ Reasonable valuation",
                        "✅ Positive long-term trends",
                        "✅ Risk management in place"
                    ]
                    
                    for item in checklist:
                        st.markdown(item)
                
                else:
                    st.error("Could not fetch long-term data. Please try again later.")
        
        else:
            # Education section
            st.markdown("""
            ### 🎓 Long-term Investment Strategies
            
            **1. Dividend Growth Investing**
            - Focus on companies with consistent dividend increases
            - Reinvest dividends for compound growth
            - Look for payout ratios < 60%
            - **Example Stocks**: JNJ, PG, HD, JPM
            
            **2. Value Investing**
            - Buy undervalued companies with strong fundamentals
            - Focus on P/E, P/B, and P/S ratios
            - Look for margin of safety
            - **Example Stocks**: BRK.B, JPM, BAC, GM
            
            **3. Growth at Reasonable Price (GARP)**
            - Balance between growth and value
            - PEG ratio < 1.5
            - Sustainable growth rates
            - **Example Stocks**: MSFT, GOOGL, V, MA
            
            **4. Blue Chip Core**
            - Largest, most stable companies
            - Market leaders in their industries
            - Low to moderate volatility
            - **Example Stocks**: AAPL, MSFT, JNJ, WMT
            
            ### 📊 Key Metrics to Watch:
            - **P/E Ratio**: < 25 for growth, < 15 for value
            - **Debt/Equity**: < 1.0 (lower is better)
            - **ROE**: > 15% (higher is better)
            - **Dividend Yield**: 2-4% for balanced portfolios
            - **Revenue Growth**: > 5% annually
            
            Click **'Find Investments'** to begin screening!
            """)
    
    def render_portfolio_builder(self):
        """Render portfolio builder tool"""
        st.markdown('📊 Portfolio Builder', unsafe_allow_html=True)
        
        # Portfolio setup
        col1, col2, col3 = st.columns(3)
        
        with col1:
            portfolio_name = st.text_input("Portfolio Name", "My Investment Portfolio")
        
        with col2:
            initial_capital = st.number_input("Initial Capital ($)", 
                                            min_value=1000, 
                                            max_value=1000000,
                                            value=self.user_profile['capital'],
                                            step=1000)
        
        with col3:
            rebalance_frequency = st.selectbox(
                "Rebalance Frequency",
                ["Monthly", "Quarterly", "Semi-Annually", "Annually", "Never"]
            )
        
        # Portfolio allocation
        st.markdown("### 🎯 Portfolio Allocation")
        
        # Modern portfolio theory allocation
        risk_allocation = {
            "Very Conservative": {"Stocks": 30, "Bonds": 60, "Cash": 10},
            "Conservative": {"Stocks": 50, "Bonds": 40, "Cash": 10},
            "Moderate": {"Stocks": 70, "Bonds": 25, "Cash": 5},
            "Aggressive": {"Stocks": 85, "Bonds": 10, "Cash": 5},
            "Very Aggressive": {"Stocks": 95, "Bonds": 5, "Cash": 0}
        }
        
        allocation = risk_allocation[self.user_profile['risk_tolerance']]
        
        # Display allocation
        cols = st.columns(5)
        asset_classes = ["Stocks", "Bonds", "Cash", "Real Estate", "Alternative"]
        
        for idx, asset in enumerate(asset_classes):
            with cols[idx]:
                if asset in allocation:
                    percent = allocation[asset]
                    value = initial_capital * (percent / 100)
                    
                    st.metric(
                        label=asset,
                        value=f"{percent}%",
                        delta=f"${value:,.0f}"
                    )
                    
                    # Allocation slider
                    if asset != "Alternative":
                        new_percent = st.slider(
                            f"{asset} %",
                            min_value=0,
                            max_value=100,
                            value=percent,
                            key=f"alloc_{asset}"
                        )
                        allocation[asset] = new_percent
        
        # Stock selection
        st.markdown("### 📈 Stock Selection")
        
        # Pre-built model portfolios
        model_portfolios = {
            "Conservative Income": ["JNJ", "PG", "JPM", "KO", "XOM", "T", "O", "VZ", "ED", "SO"],
            "Balanced Growth": ["AAPL", "MSFT", "GOOGL", "AMZN", "V", "MA", "HD", "UNH", "JNJ", "CRM"],
            "Aggressive Growth": ["NVDA", "TSLA", "AMD", "META", "ADBE", "NOW", "SNOW", "PLTR", "NET", "SHOP"],
            "Dividend Aristocrats": ["JNJ", "PG", "KO", "MMM", "TGT", "ABBV", "CVX", "WMT", "PEP", "CL"]
        }
        
        selected_model = st.selectbox("Choose a Model Portfolio", list(model_portfolios.keys()))
        
        # Display selected stocks
        selected_stocks = model_portfolios[selected_model]
        
        # Create portfolio table
        portfolio_data = []
        
        st.markdown(f"#### Selected Portfolio: {selected_model}")
        
        for symbol in selected_stocks:
            try:
                data = self.analysis_engine.analyze_stock(symbol)
                if data:
                    allocation_pct = 100 / len(selected_stocks)  # Equal weight
                    value = initial_capital * (allocation_pct / 100)
                    shares = value / data['current_price']
                    
                    portfolio_data.append({
                        'Symbol': symbol,
                        'Name': data['name'],
                        'Sector': data['sector'],
                        'Price': data['current_price'],
                        'Shares': shares,
                        'Value': value,
                        'Weight': allocation_pct,
                        'Div Yield': data['dividend_yield'],
                        'Beta': data['beta']
                    })
            except:
                continue
        
        if portfolio_data:
            df_portfolio = pd.DataFrame(portfolio_data)
            
            # Calculate portfolio metrics
            total_value = df_portfolio['Value'].sum()
            avg_dividend = (df_portfolio['Value'] * df_portfolio['Div Yield'] / 100).sum() / total_value
            portfolio_beta = (df_portfolio['Value'] * df_portfolio['Beta']).sum() / total_value
            
            # Display portfolio
            st.dataframe(
                df_portfolio,
                column_config={
                    "Symbol": "Symbol",
                    "Name": "Company", 
                    "Sector": "Sector",
                    "Price": st.column_config.NumberColumn("Price", format="$%.2f"),
                    "Shares": st.column_config.NumberColumn("Shares", format="%.2f"),
                    "Value": st.column_config.NumberColumn("Value", format="$%.2f"),
                    "Weight": st.column_config.NumberColumn("Weight", format="%.1f%%"),
                    "Div Yield": st.column_config.NumberColumn("Yield", format="%.2f%%"),
                    "Beta": st.column_config.NumberColumn("Beta", format="%.2f")
                },
                use_container_width=True,
                height=400
            )
            
            # Portfolio metrics
            st.markdown("### 📊 Portfolio Metrics")
            
            metric_cols = st.columns(4)
            
            with metric_cols[0]:
                st.metric("Total Value", f"${total_value:,.2f}")
            
            with metric_cols[1]:
                st.metric("Number of Stocks", len(portfolio_data))
            
            with metric_cols[2]:
                st.metric("Avg Dividend Yield", f"{avg_dividend:.2f}%")
            
            with metric_cols[3]:
                st.metric("Portfolio Beta", f"{portfolio_beta:.2f}")
            
            # Risk Analysis
            st.markdown("### 🛡️ Risk Analysis")
            
            # Sector concentration
            sector_concentration = df_portfolio.groupby('Sector')['Value'].sum() / total_value * 100
            
            fig = px.pie(
                values=sector_concentration.values,
                names=sector_concentration.index,
                title='Portfolio Sector Concentration'
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Risk assessment
            st.markdown("#### 📋 Risk Assessment")
            
            if portfolio_beta > 1.2:
                st.warning("⚠️ **High Market Risk**: Portfolio is more volatile than market")
            elif portfolio_beta < 0.8:
                st.info("ℹ️ **Low Market Risk**: Portfolio is less volatile than market")
            else:
                st.success("✅ **Moderate Market Risk**: Portfolio volatility matches market")
            
            if len(df_portfolio) < 10:
                st.warning("⚠️ **Concentration Risk**: Consider more diversification")
            
            if sector_concentration.max() > 30:
                st.warning(f"⚠️ **Sector Concentration**: {sector_concentration.idxmax()} at {sector_concentration.max():.1f}%")
            
            # Rebalancing advice
            st.markdown("### 🔄 Rebalancing Strategy")
            
            rebalance_rules = """
            **When to Rebalance:**
            1. Any position grows beyond 150% of target weight
            2. Any position falls below 50% of target weight  
            3. Quarterly check regardless of changes
            4. After major market events
            
            **How to Rebalance:**
            - Trim winners to target weight
            - Add to laggards to reach target
            - Use new contributions for rebalancing
            - Consider tax implications
            """
            
            st.info(rebalance_rules)
            
            # Export portfolio
            if st.button("📥 Export Portfolio Plan", type="primary"):
                # Create export data
                export_data = {
                    'portfolio_name': portfolio_name,
                    'initial_capital': initial_capital,
                    'risk_profile': self.user_profile['risk_tolerance'],
                    'strategy': selected_model,
                    'stocks': portfolio_data,
                    'rebalance_frequency': rebalance_frequency,
                    'created_date': datetime.now().strftime("%Y-%m-%d")
                }
                
                # Convert to JSON for download
                json_str = json.dumps(export_data, indent=2)
                
                st.download_button(
                    label="Download Portfolio JSON",
                    data=json_str,
                    file_name=f"portfolio_{portfolio_name.replace(' ', '_')}.json",
                    mime="application/json"
                )
    
    def render_risk_management(self):
        """Render risk management tools"""
        st.markdown('🛡️ Risk Management Toolkit', unsafe_allow_html=True)
        
        tabs = st.tabs([
            "📊 Position Sizing", 
            "🎯 Risk-Reward Calculator",
            "📉 Drawdown Analysis",
            "🔗 Correlation Checker"
        ])
        
        # Tab 1: Position Sizing
        with tabs[0]:
            st.markdown("### 📊 Position Size Calculator")
            
            col1, col2 = st.columns(2)
            
            with col1:
                account_size = st.number_input(
                    "Total Account Size ($)",
                    min_value=1000,
                    value=self.user_profile['capital'],
                    step=1000,
                    key="pos_size_account"
                )
                
                risk_per_trade = st.slider(
                    "Risk per Trade (%)",
                    min_value=0.1,
                    max_value=5.0,
                    value=2.0,
                    step=0.1,
                    help="Maximum % of account to risk on a single trade"
                )
            
            with col2:
                entry_price = st.number_input(
                    "Entry Price ($)",
                    min_value=0.01,
                    value=100.0,
                    step=0.01
                )
                
                stop_loss = st.number_input(
                    "Stop Loss Price ($)",
                    min_value=0.01,
                    value=95.0,
                    step=0.01
                )
            
            if entry_price > stop_loss:
                # Calculate position size
                risk_amount = account_size * (risk_per_trade / 100)
                risk_per_share = entry_price - stop_loss
                shares = risk_amount / risk_per_share
                position_value = shares * entry_price
                
                # Display results
                st.markdown("### 🎯 Position Size Results")
                
                results_cols = st.columns(4)
                
                with results_cols[0]:
                    st.metric("Risk Amount", f"${risk_amount:.2f}")
                
                with results_cols[1]:
                    st.metric("Position Size", f"{shares:.0f} shares")
                
                with results_cols[2]:
                    st.metric("Position Value", f"${position_value:.2f}")
                
                with results_cols[3]:
                    stop_pct = (risk_per_share / entry_price) * 100
                    st.metric("Stop Loss %", f"{stop_pct:.1f}%")
                
                # Risk management guidelines
                st.markdown("### 📋 Risk Guidelines")
                
                guidelines = [
                    ("💰 Risk per Trade", "1-2% of account", "✅ Good: $200-$400"),
                    ("🛑 Max Daily Loss", "5% of account", "✅ Good: $1,000"),
                    ("📊 Max Open Positions", "5-10 positions", "✅ Good: 8 positions"),
                    ("🎯 Risk-Reward Ratio", "Minimum 1:2", "✅ Good: 1:3 or better"),
                    ("📈 Win Rate Required", "40% at 1:2 R:R", "✅ Requires 40% win rate")
                ]
                
                for name, recommendation, status in guidelines:
                    st.markdown(f"- **{name}**: {recommendation} - {status}")
            
            else:
                st.error("❌ Entry price must be greater than stop loss price")
        
        # Tab 2: Risk-Reward Calculator
        with tabs[1]:
            st.markdown("### 🎯 Risk-Reward Calculator")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                entry_price_rr = st.number_input(
                    "Entry Price ($)",
                    value=100.0,
                    step=0.01,
                    key="rr_entry"
                )
            
            with col2:
                stop_loss_rr = st.number_input(
                    "Stop Loss ($)",
                    value=95.0,
                    step=0.01,
                    key="rr_stop"
                )
            
            with col3:
                take_profit = st.number_input(
                    "Take Profit ($)",
                    value=110.0,
                    step=0.01
                )
            
            if entry_price_rr > stop_loss_rr and take_profit > entry_price_rr:
                # Calculate risk-reward
                risk = entry_price_rr - stop_loss_rr
                reward = take_profit - entry_price_rr
                rr_ratio = reward / risk
                
                # Display results
                st.markdown("### 📈 Risk-Reward Analysis")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    risk_pct = (risk / entry_price_rr) * 100
                    st.metric("Risk", f"${risk:.2f}", f"{risk_pct:.1f}%")
                
                with col2:
                    reward_pct = (reward / entry_price_rr) * 100
                    st.metric("Reward", f"${reward:.2f}", f"{reward_pct:.1f}%")
                
                with col3:
                    st.metric("Risk-Reward Ratio", f"1:{rr_ratio:.2f}")
                
                # Visual representation
                fig = go.Figure()
                
                fig.add_trace(go.Indicator(
                    mode="number+gauge+delta",
                    value=rr_ratio,
                    domain={'x': [0, 1], 'y': [0, 1]},
                    title={'text': "R:R Ratio"},
                    delta={'reference': 2},
                    gauge={
                        'shape': "bullet",
                        'axis': {'range': [None, 4]},
                        'threshold': {
                            'line': {'color': "black", 'width': 2},
                            'thickness': 0.75,
                            'value': 2
                        },
                        'steps': [
                            {'range': [0, 1], 'color': "#e74c3c"},
                            {'range': [1, 2], 'color': "#f39c12"},
                            {'range': [2, 4], 'color': "#27ae60"}
                        ],
                        'bar': {'color': "#3498db"}
                    }
                ))
                
                fig.update_layout(height=200)
                st.plotly_chart(fig, use_container_width=True)
                
                # Trading edge calculation
                st.markdown("### 🎲 Trading Edge Calculator")
                
                win_rate = st.slider(
                    "Expected Win Rate (%)",
                    min_value=10,
                    max_value=90,
                    value=50,
                    step=5
                )
                
                # Calculate expected value
                expected_value = (win_rate/100 * reward) - ((100-win_rate)/100 * risk)
                edge_percent = (expected_value / entry_price_rr) * 100
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Expected Value/Trade", f"${expected_value:.2f}")
                
                with col2:
                    st.metric("Edge per Trade", f"{edge_percent:.2f}%")
                
                if expected_value > 0:
                    st.success(f"✅ Positive edge trading system. Need {int((risk/(risk+reward))*100)}% win rate to break even.")
                else:
                    st.error(f"❌ Negative edge trading system. Need higher win rate or better R:R ratio.")
            else:
                st.error("❌ Take profit must be greater than entry price")
        
        # Tab 3: Drawdown Analysis
        with tabs[2]:
            st.markdown("### 📉 Drawdown Analysis")
            
            initial_portfolio = st.number_input(
                "Initial Portfolio Value ($)",
                min_value=1000,
                value=self.user_profile['capital'],
                step=1000
            )
            
            # Simulate different drawdown scenarios
            drawdown_levels = [5, 10, 15, 20, 25, 30, 40, 50]
            
            results = []
            for dd in drawdown_levels:
                loss_amount = initial_portfolio * (dd / 100)
                remaining = initial_portfolio - loss_amount
                recovery_needed = (loss_amount / remaining) * 100
                
                results.append({
                    'Drawdown': dd,
                    'Loss Amount': loss_amount,
                    'Remaining': remaining,
                    'Recovery Needed': recovery_needed
                })
            
            df_drawdown = pd.DataFrame(results)
            
            # Display table
            st.dataframe(
                df_drawdown,
                column_config={
                    "Drawdown": st.column_config.NumberColumn("Drawdown", format="%.0f%%"),
                    "Loss Amount": st.column_config.NumberColumn("Loss Amount", format="$%.0f"),
                    "Remaining": st.column_config.NumberColumn("Remaining", format="$%.0f"),
                    "Recovery Needed": st.column_config.NumberColumn("Recovery Needed", format="%.1f%%")
                },
                use_container_width=True
            )
            
            # Create recovery chart
            fig = go.Figure()
            
            fig.add_trace(go.Bar(
                x=df_drawdown['Drawdown'],
                y=df_drawdown['Recovery Needed'],
                name='Recovery Needed',
                marker_color=df_drawdown['Recovery Needed'],
                hovertemplate='Drawdown: %{x}%Recovery Needed: %{y:.1f}%'
            ))
            
            fig.update_layout(
                title="Recovery Needed After Drawdown",
                xaxis_title="Drawdown (%)",
                yaxis_title="Gain Needed to Recover (%)",
                template="plotly_white",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Risk management rules
            st.markdown("### 🛡️ Drawdown Prevention Rules")
            
            rules = [
                "**1. Maximum Position Size**: No single position > 5% of portfolio",
                "**2. Stop Loss Discipline**: Always use stop losses",
                "**3. Diversification**: Minimum 10 different positions",
                "**4. Sector Limits**: No sector > 25% of portfolio",
                "**5. Daily Loss Limit**: Stop trading after 3% daily loss",
                "**6. Weekly Loss Limit**: Stop trading after 7% weekly loss",
                "**7. Drawdown Response**: Reduce position size by 50% after 10% drawdown",
                "**8. Cash Reserve**: Maintain 10-20% cash for opportunities"
            ]
            
            for rule in rules:
                st.markdown(f"- {rule}")
        
        # Tab 4: Correlation Checker
        with tabs[3]:
            st.markdown("### 🔗 Portfolio Correlation Checker")
            
            # Input portfolio symbols
            symbols_input = st.text_input(
                "Enter Stock Symbols (comma-separated)",
                "AAPL, MSFT, GOOGL, AMZN, NVDA, JPM, JNJ, PG, WMT, V"
            )
            
            symbols = [s.strip().upper() for s in symbols_input.split(",") if s.strip()]
            
            if len(symbols) >= 2:
                with st.spinner("Calculating correlations..."):
                    # Fetch price data
                    price_data = {}
                    
                    for symbol in symbols:
                        try:
                            data = self.analysis_engine.data_manager.get_stock_data(symbol, period="3mo")
                            if data and not data['history'].empty:
                                price_data[symbol] = data['history']['Close']
                        except:
                            continue
                    
                    if len(price_data) >= 2:
                        # Create correlation matrix
                        df_prices = pd.DataFrame(price_data)
                        returns = df_prices.pct_change().dropna()
                        correlation_matrix = returns.corr()
                        
                        # Display heatmap
                        fig = px.imshow(
                            correlation_matrix,
                            text_auto='.2f',
                            color_continuous_scale='RdBu',
                            title="Portfolio Correlation Matrix"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Analysis
                        st.markdown("### 📊 Correlation Analysis")
                        
                        # Find highly correlated pairs
                        high_corr_pairs = []
                        for i in range(len(correlation_matrix.columns)):
                            for j in range(i+1, len(correlation_matrix.columns)):
                                corr = correlation_matrix.iloc[i, j]
                                if abs(corr) > 0.7:
                                    high_corr_pairs.append((
                                        correlation_matrix.columns[i],
                                        correlation_matrix.columns[j],
                                        corr
                                    ))
                        
                        if high_corr_pairs:
                            st.warning("⚠️ **High Correlation Detected**")
                            for stock1, stock2, corr in high_corr_pairs:
                                st.markdown(f"- {stock1} & {stock2}: {corr:.2f} correlation")
                            st.markdown("Consider reducing exposure to correlated positions.")
                        else:
                            st.success("✅ Good portfolio diversification - no highly correlated pairs")
                        
                        # Portfolio diversification score
                        avg_correlation = correlation_matrix.abs().mean().mean()
                        diversification_score = 100 * (1 - avg_correlation)
                        
                        st.metric("Diversification Score", f"{diversification_score:.0f}/100")
                        
                        # Suggestions for improvement
                        st.markdown("### 💡 Diversification Suggestions")
                        
                        suggestions = [
                            ("High Tech Concentration", "Add Healthcare/Consumer Staples"),
                            ("US Only", "Consider International Exposure"),
                            ("All Large Cap", "Add Small/Mid Cap"),
                            ("Growth Only", "Add Value/Dividend Stocks"),
                            ("Equities Only", "Consider Bonds/REITs")
                        ]
                        
                        for problem, suggestion in suggestions:
                            st.markdown(f"- **{problem}**: {suggestion}")
                    
                    else:
                        st.error("Could not fetch data for the provided symbols")
            else:
                st.info("Enter at least 2 stock symbols to check correlation")
    
    def render_learning_center(self):
        """Render educational content"""
        st.markdown('📚 Learning Center', unsafe_allow_html=True)
        
        tabs = st.tabs([
            "📖 Investment Basics", 
            "📈 Technical Analysis",
            "📊 Fundamental Analysis", 
            "🛡️ Risk Management",
            "💼 Trading Psychology"
        ])
        
        # Tab 1: Investment Basics
        with tabs[0]:
            st.markdown("### 📖 Investment Basics for Beginners")
            
            lessons = [
                {
                    "title": "💰 Stock Market 101",
                    "content": """
                    **What is a Stock?**
                    - A stock represents ownership in a company
                    - Shareholders own a piece of the company
                    - Stocks are traded on exchanges (NYSE, NASDAQ)
                    
                    **How to Make Money:**
                    1. **Capital Appreciation**: Buy low, sell high
                    2. **Dividends**: Regular payments from profits
                    3. **Options/Selling**: Advanced strategies
                    
                    **Key Terms:**
                    - **Bull Market**: Rising prices
                    - **Bear Market**: Falling prices
                    - **Volatility**: Price fluctuations
                    - **Liquidity**: Ease of buying/selling
                    """
                },
                {
                    "title": "🎯 Types of Investments",
                    "content": """
                    **Stocks (Equities):**
                    - Growth Stocks: High potential, higher risk
                    - Value Stocks: Undervalued, potential bargain
                    - Dividend Stocks: Regular income, stability
                    
                    **ETFs (Exchange Traded Funds):**
                    - Bundle of stocks
                    - Instant diversification
                    - Lower fees than mutual funds
                    
                    **Bonds:**
                    - Loan to company/government
                    - Fixed interest payments
                    - Lower risk than stocks
                    
                    **Alternative Investments:**
                    - Real Estate (REITs)
                    - Commodities (Gold, Oil)
                    - Cryptocurrencies
                    """
                },
                {
                    "title": "📊 Building Your First Portfolio",
                    "content": """
                    **Step 1: Determine Your Goals**
                    - Emergency fund first (3-6 months expenses)
                    - Retirement accounts (401k, IRA)
                    - Taxable brokerage account
                    
                    **Step 2: Asset Allocation**
                    - Age-based rule: (100 - Age) = % in stocks
                    - Example: 30 years old = 70% stocks, 30% bonds
                    
                    **Step 3: Choose Investments**
                    - Start with broad market ETFs (SPY, VTI)
                    - Add sector ETFs for diversification
                    - Individual stocks for "play money"
                    
                    **Step 4: Regular Contributions**
                    - Dollar-cost averaging
                    - Automatic investments
                    - Rebalance quarterly
                    """
                }
            ]
            
            for lesson in lessons:
                with st.expander(lesson["title"]):
                    st.markdown(lesson["content"])
        
        # Tab 2: Technical Analysis
        with tabs[1]:
            st.markdown("### 📈 Technical Analysis Guide")
            
            indicators = [
                {
                    "name": "📊 Moving Averages",
                    "description": "Trend identification & support/resistance",
                    "use": "Identify trend direction and potential reversals",
                    "buy_signal": "Price crosses above moving average (golden cross)",
                    "sell_signal": "Price crosses below moving average (death cross)"
                },
                {
                    "name": "📈 RSI (Relative Strength Index)",
                    "description": "Momentum oscillator measuring speed of price changes",
                    "use": "Identify overbought/oversold conditions",
                    "buy_signal": "RSI < 30 (oversold)",
                    "sell_signal": "RSI > 70 (overbought)"
                },
                {
                    "name": "📉 MACD (Moving Average Convergence Divergence)",
                    "description": "Trend-following momentum indicator",
                    "use": "Identify trend changes and momentum",
                    "buy_signal": "MACD line crosses above signal line",
                    "sell_signal": "MACD line crosses below signal line"
                },
                {
                    "name": "📊 Bollinger Bands",
                    "description": "Volatility bands placed above and below moving average",
                    "use": "Measure volatility and identify extremes",
                    "buy_signal": "Price touches lower band (potential bounce)",
                    "sell_signal": "Price touches upper band (potential pullback)"
                },
                {
                    "name": "📈 Volume Analysis",
                    "description": "Study of trading volume to confirm price movements",
                    "use": "Confirm strength of price moves",
                    "buy_signal": "Price up on high volume (strong move)",
                    "sell_signal": "Price down on high volume (distribution)"
                }
            ]
            
            for indicator in indicators:
                with st.expander(f"{indicator['name']} - {indicator['description']}"):
                    st.markdown(f"""
                    **How to Use:** {indicator['use']}
                    
                    **Buy Signal:** {indicator['buy_signal']}
                    
                    **Sell Signal:** {indicator['sell_signal']}
                    
                    **Pro Tip:** Combine with other indicators for confirmation
                    """)
            
            # Chart patterns
            st.markdown("### 📐 Common Chart Patterns")
            
            patterns = {
                "Head and Shoulders": "Reversal pattern - signals trend change",
                "Double Top/Bottom": "Reversal pattern - failed breakout",
                "Triangle (Ascending/Descending)": "Continuation pattern - breakout expected",
                "Cup and Handle": "Bullish continuation pattern",
                "Flags and Pennants": "Short-term continuation patterns"
            }
            
            for pattern, description in patterns.items():
                st.markdown(f"- **{pattern}**: {description}")
        
        # Tab 3: Fundamental Analysis  
        with tabs[2]:
            st.markdown("### 📊 Fundamental Analysis Guide")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("#### 📈 Valuation Metrics")
                
                metrics = [
                    ("P/E Ratio", "Price/Earnings - Lower is generally better", "< 20 good, > 30 expensive"),
                    ("P/B Ratio", "Price/Book Value - Value indicator", "< 1 could be undervalued"),
                    ("P/S Ratio", "Price/Sales - Growth companies", "< 2 good, > 10 expensive"),
                    ("PEG Ratio", "P/E divided by growth rate", "< 1 indicates undervalued growth"),
                    ("Dividend Yield", "Annual dividend/price", "2-4% typical for income"),
                    ("ROE", "Return on Equity - Profitability", "> 15% excellent")
                ]
                
                for metric, description, benchmark in metrics:
                    with st.expander(metric):
                        st.markdown(f"**Description**: {description}")
                        st.markdown(f"**Benchmark**: {benchmark}")
            
            with col2:
                st.markdown("#### 📊 Financial Health")
                
                health_metrics = [
                    ("Debt/Equity Ratio", "Financial leverage", "< 1.0 healthy"),
                    ("Current Ratio", "Short-term liquidity", "> 1.5 good"),
                    ("Profit Margin", "Profitability", "> 10% good, > 20% excellent"),
                    ("Revenue Growth", "Top line growth", "> 5% minimum"),
                    ("EPS Growth", "Earnings per share growth", "Consistent > 10% excellent"),
                    ("Free Cash Flow", "Cash available after expenses", "Positive & growing")
                ]
                
                for metric, description, benchmark in health_metrics:
                    with st.expander(metric):
                        st.markdown(f"**What it measures**: {description}")
                        st.markdown(f"**Healthy range**: {benchmark}")
        
        # Tab 4: Risk Management
        with tabs[3]:
            st.markdown("### 🛡️ Risk Management Principles")
            
            st.markdown("""
            #### 🎯 Rule #1: Preserve Capital
            "The first rule of investing is don't lose money. The second rule is don't forget rule #1." - Warren Buffett
            
            #### 📊 Position Sizing Rules
            1. **1-2% Rule**: Never risk more than 1-2% of capital on a single trade
            2. **5-10 Positions**: Maintain 5-10 positions for diversification
            3. **25% Sector Limit**: No sector should exceed 25% of portfolio
            
            #### 🛑 Stop Loss Strategies
            - **Fixed Percentage**: 5-10% below entry
            - **ATR-based**: 2x ATR below entry for volatility-adjusted stops
            - **Moving Average**: Below key moving average (20, 50, 200-day)
            - **Support/Resistance**: Below key support levels
            
            #### 📉 Drawdown Management
            - **10% Rule**: Reduce position sizes by 50% after 10% portfolio drawdown
            - **20% Rule**: Go to cash-heavy after 20% drawdown
            - **Daily/Weekly Limits**: Stop trading after 3% daily or 7% weekly loss
            
            #### 🔄 Portfolio Rebalancing
            - **Time-based**: Quarterly or annually
            - **Threshold-based**: When any asset deviates >5% from target
            - **Event-based**: After major market moves or life changes
            """)
        
        # Tab 5: Trading Psychology
        with tabs[4]:
            st.markdown("### 💼 Trading Psychology & Discipline")
            
            st.markdown("""
            #### 🧠 Common Psychological Traps
            
            **1. Fear of Missing Out (FOMO)**
            - Chasing stocks after big moves
            - Solution: Have a watchlist and wait for proper entries
            
            **2. Loss Aversion**
            - Holding losers too long, selling winners too early
            - Solution: Follow your trading plan, use stop losses
            
            **3. Confirmation Bias**
            - Seeing only information that confirms your beliefs
            - Solution: Consider opposing views, stay objective
            
            **4. Revenge Trading**
            - Trying to immediately recover losses
            - Solution: Take a break after losses, review what went wrong
            
            #### 🎯 Building Trading Discipline
            
            **1. Have a Written Trading Plan**
            - Entry criteria
            - Exit criteria (stop loss & take profit)
            - Position sizing rules
            - Risk management rules
            
            **2. Keep a Trading Journal**
            - Record every trade
            - Note emotions and psychology
            - Review weekly for patterns
            
            **3. Practice Patience**
            - Wait for your setup
            - Not every day is a trading day
            - Quality over quantity
            
            **4. Manage Expectations**
            - Aim for consistency, not home runs
            - Accept that losses are part of the game
            - Focus on process, not just outcomes
            
            #### 🧘‍♀️ Mindset Tips
            
            - **Treat trading like a business**
            - **Control what you can control** (risk, entries, emotions)
            - **Let profits run, cut losses short**
            - **Stay humble, markets are always right**
            """)
            
            # Interactive quiz
            st.markdown("### 🧠 Psychology Quiz")
            
            question = st.selectbox(
                "What's the most common emotional mistake traders make?",
                [
                    "Fear of Missing Out (FOMO)",
                    "Being too patient", 
                    "Not taking enough risk",
                    "Following the plan too closely"
                ]
            )
            
            if question == "Fear of Missing Out (FOMO)":
                st.success("✅ Correct! FOMO causes traders to chase moves and enter at poor prices.")
            else:
                st.error("❌ Try again. FOMO is often the biggest psychological challenge.")
    
    def render_footer(self):
        """Render footer with disclaimer"""
        st.markdown("---")
        
        disclaimer = """
        ### ⚠️ Important Disclaimer
        
        **This tool is for educational and informational purposes only.** 
        
        **Not Financial Advice:** The information provided by Market Master Pro is for educational purposes only and should not be considered financial advice. All investment decisions should be made based on your own research and in consultation with a qualified financial advisor.
        
        **Risk Disclosure:** Stock market investing involves substantial risk of loss and is not suitable for every investor. The valuation of investments may fluctuate, and as a result, you may lose more than your original investment.
        
        **Past Performance:** Past performance is not indicative of future results. Historical returns do not guarantee future performance.
        
        **Accuracy of Information:** While we strive to provide accurate information, we do not guarantee the accuracy, completeness, or timeliness of any information provided.
        
        **No Endorsement:** Nothing in this application constitutes a recommendation to buy or sell any security.
        
        **Your Responsibility:** You are solely responsible for your own investment decisions and should conduct your own due diligence.
        
        **Consult Professionals:** Always consult with qualified financial professionals before making any investment decisions.
        """
        
        st.markdown(disclaimer)

# ==================== RUN APPLICATION ====================

if __name__ == "__main__":
    # Initialize the application
    app = StockMarketTool()
    
    # Run the main application
    app.run()