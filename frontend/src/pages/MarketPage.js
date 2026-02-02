import React, { useState } from 'react';
import { usePrices } from '../contexts/PriceContext';
import { ArrowUpIcon, ArrowDownIcon } from '@heroicons/react/24/solid';

const COIN_INFO = {
  BTC: { name: 'Bitcoin', icon: '₿' },
  ETH: { name: 'Ethereum', icon: 'Ξ' },
  USDT: { name: 'Tether', icon: '₮' },
  SOL: { name: 'Solana', icon: '◎' },
  XRP: { name: 'Ripple', icon: '✕' },
  DOGE: { name: 'Dogecoin', icon: 'Ð' },
  ADA: { name: 'Cardano', icon: '₳' },
  BNB: { name: 'BNB', icon: '⬡' },
  AVAX: { name: 'Avalanche', icon: '🔺' },
  MATIC: { name: 'Polygon', icon: '⬡' },
  DOT: { name: 'Polkadot', icon: '●' },
  LINK: { name: 'Chainlink', icon: '⬡' },
};

const MarketPage = () => {
  const { prices, loading } = usePrices();
  const [sortBy, setSortBy] = useState('market_cap');
  const [sortOrder, setSortOrder] = useState('desc');

  const formatPrice = (price) => {
    if (!price) return '-';
    if (price >= 1000) {
      return '$' + price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } else if (price >= 1) {
      return '$' + price.toFixed(2);
    } else {
      return '$' + price.toFixed(4);
    }
  };

  const formatChange = (change) => {
    if (!change) return '0.00%';
    const formatted = Math.abs(change).toFixed(2) + '%';
    return change >= 0 ? '+' + formatted : '-' + formatted;
  };

  const formatMarketCap = (cap) => {
    if (!cap) return '-';
    if (cap >= 1e12) return '$' + (cap / 1e12).toFixed(2) + 'T';
    if (cap >= 1e9) return '$' + (cap / 1e9).toFixed(2) + 'B';
    if (cap >= 1e6) return '$' + (cap / 1e6).toFixed(2) + 'M';
    return '$' + cap.toLocaleString();
  };

  const formatVolume = (vol) => {
    if (!vol) return '-';
    if (vol >= 1e9) return '$' + (vol / 1e9).toFixed(2) + 'B';
    if (vol >= 1e6) return '$' + (vol / 1e6).toFixed(2) + 'M';
    return '$' + vol.toLocaleString();
  };

  const coinList = Object.entries(prices)
    .filter(([symbol]) => symbol !== 'USDT')
    .map(([symbol, data]) => ({
      symbol,
      ...COIN_INFO[symbol],
      ...data,
    }))
    .sort((a, b) => {
      const aVal = a[sortBy] || 0;
      const bVal = b[sortBy] || 0;
      return sortOrder === 'desc' ? bVal - aVal : aVal - bVal;
    });

  const toggleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'desc' ? 'asc' : 'desc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse">
          <div className="h-8 bg-exchange-card rounded w-48 mb-6"></div>
          <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
              <div key={i} className="h-16 bg-exchange-card rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold text-exchange-text mb-6">Market Overview</h1>
      
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card p-4">
          <div className="text-exchange-muted text-sm">Total Coins</div>
          <div className="text-xl font-bold text-exchange-text">{coinList.length}</div>
        </div>
        <div className="card p-4">
          <div className="text-exchange-muted text-sm">BTC Price</div>
          <div className="text-xl font-bold text-exchange-text">
            {prices.BTC ? formatPrice(prices.BTC.price) : '-'}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-exchange-muted text-sm">Top Gainer</div>
          <div className="text-xl font-bold text-success">
            {coinList.length > 0 
              ? coinList.reduce((max, c) => (c.change_24h || 0) > (max.change_24h || -999) ? c : max, {}).symbol || '-'
              : '-'}
          </div>
        </div>
        <div className="card p-4">
          <div className="text-exchange-muted text-sm">Top Loser</div>
          <div className="text-xl font-bold text-danger">
            {coinList.length > 0 
              ? coinList.reduce((min, c) => (c.change_24h || 0) < (min.change_24h || 999) ? c : min, {}).symbol || '-'
              : '-'}
          </div>
        </div>
      </div>

      <div className="card overflow-hidden">
        <table className="w-full">
          <thead className="bg-exchange-bg">
            <tr>
              <th className="text-left p-4 text-exchange-muted font-medium">#</th>
              <th className="text-left p-4 text-exchange-muted font-medium">Coin</th>
              <th 
                className="text-right p-4 text-exchange-muted font-medium cursor-pointer hover:text-exchange-text"
                onClick={() => toggleSort('price')}
              >
                Price {sortBy === 'price' && (sortOrder === 'desc' ? '↓' : '↑')}
              </th>
              <th 
                className="text-right p-4 text-exchange-muted font-medium cursor-pointer hover:text-exchange-text"
                onClick={() => toggleSort('change_24h')}
              >
                24h Change {sortBy === 'change_24h' && (sortOrder === 'desc' ? '↓' : '↑')}
              </th>
              <th 
                className="text-right p-4 text-exchange-muted font-medium cursor-pointer hover:text-exchange-text hidden md:table-cell"
                onClick={() => toggleSort('market_cap')}
              >
                Market Cap {sortBy === 'market_cap' && (sortOrder === 'desc' ? '↓' : '↑')}
              </th>
              <th 
                className="text-right p-4 text-exchange-muted font-medium cursor-pointer hover:text-exchange-text hidden lg:table-cell"
                onClick={() => toggleSort('volume_24h')}
              >
                Volume (24h) {sortBy === 'volume_24h' && (sortOrder === 'desc' ? '↓' : '↑')}
              </th>
            </tr>
          </thead>
          <tbody>
            {coinList.map((coin, index) => (
              <tr 
                key={coin.symbol}
                className="border-t border-exchange-border hover:bg-exchange-bg transition-colors"
              >
                <td className="p-4 text-exchange-muted">{index + 1}</td>
                <td className="p-4">
                  <div className="flex items-center gap-3">
                    <span className="text-2xl">{coin.icon || '●'}</span>
                    <div>
                      <div className="font-medium text-exchange-text">{coin.symbol}</div>
                      <div className="text-sm text-exchange-muted">{coin.name || coin.symbol}</div>
                    </div>
                  </div>
                </td>
                <td className="p-4 text-right font-mono text-exchange-text">
                  {formatPrice(coin.price)}
                </td>
                <td className="p-4 text-right">
                  <div className={`flex items-center justify-end gap-1 ${(coin.change_24h || 0) >= 0 ? 'text-success' : 'text-danger'}`}>
                    {(coin.change_24h || 0) >= 0 ? (
                      <ArrowUpIcon className="w-4 h-4" />
                    ) : (
                      <ArrowDownIcon className="w-4 h-4" />
                    )}
                    {formatChange(coin.change_24h)}
                  </div>
                </td>
                <td className="p-4 text-right text-exchange-muted hidden md:table-cell">
                  {formatMarketCap(coin.market_cap)}
                </td>
                <td className="p-4 text-right text-exchange-muted hidden lg:table-cell">
                  {formatVolume(coin.volume_24h)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default MarketPage;
