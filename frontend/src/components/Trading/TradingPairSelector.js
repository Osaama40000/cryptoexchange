import React, { useState } from 'react';
import { ChevronDownIcon, MagnifyingGlassIcon } from '@heroicons/react/24/outline';

const TradingPairSelector = ({ pairs = [], currentPair, onSelect, ticker }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [search, setSearch] = useState('');

  // Ensure pairs is an array
  const pairsArray = Array.isArray(pairs) ? pairs : [];

  const filteredPairs = pairsArray.filter(pair =>
    pair.symbol.toLowerCase().includes(search.toLowerCase()) ||
    pair.base_currency?.toLowerCase().includes(search.toLowerCase()) ||
    pair.quote_currency?.toLowerCase().includes(search.toLowerCase())
  );

  // Format pair symbol as "BTC/USDT"
  const formatPairSymbol = (pair) => {
    if (!pair) return 'Select Pair';
    if (pair.base_currency && pair.quote_currency) {
      return `${pair.base_currency}/${pair.quote_currency}`;
    }
    return pair.symbol;
  };

  const formatPrice = (price) => {
    if (!price) return '-';
    return parseFloat(price).toLocaleString(undefined, {
      minimumFractionDigits: 2,
      maximumFractionDigits: 8,
    });
  };

  const formatChange = (change) => {
    if (!change) return '-';
    const num = parseFloat(change);
    const sign = num >= 0 ? '+' : '';
    return sign + num.toFixed(2) + '%';
  };

  const priceChangeColor = ticker?.price_change_24h
    ? parseFloat(ticker.price_change_24h) >= 0
      ? 'text-success'
      : 'text-danger'
    : 'text-exchange-muted';

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="card w-full p-4 flex items-center justify-between hover:bg-exchange-bg transition-colors"
      >
        <div>
          <div className="flex items-center gap-2">
            <span className="text-lg font-bold text-exchange-text">
              {formatPairSymbol(currentPair)}
            </span>
            <ChevronDownIcon className={`w-4 h-4 text-exchange-muted transition-transform ${isOpen ? 'rotate-180' : ''}`} />
          </div>
          <div className="flex items-center gap-4 mt-1">
            <span className="text-xl font-mono text-exchange-text">
              {formatPrice(ticker?.last_price || currentPair?.last_price)}
            </span>
            <span className={`text-sm font-medium ${priceChangeColor}`}>
              {formatChange(ticker?.price_change_24h || currentPair?.price_change_24h)}
            </span>
          </div>
        </div>
      </button>

      {isOpen && (
        <>
          <div className="fixed inset-0 z-10" onClick={() => setIsOpen(false)} />
          <div className="absolute top-full left-0 right-0 mt-2 card z-20 max-h-96 overflow-hidden">
            <div className="p-3 border-b border-exchange-border">
              <div className="relative">
                <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-exchange-muted" />
                <input
                  type="text"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                  placeholder="Search pairs..."
                  className="input pl-10"
                  autoFocus
                />
              </div>
            </div>
            <div className="overflow-y-auto max-h-72">
              {filteredPairs.length > 0 ? (
                filteredPairs.map((pair) => {
                  const isSelected = currentPair?.symbol === pair.symbol;
                  const changeColor = pair.price_change_24h
                    ? parseFloat(pair.price_change_24h) >= 0 ? 'text-success' : 'text-danger'
                    : 'text-exchange-muted';

                  return (
                    <button
                      key={pair.symbol}
                      onClick={() => {
                        onSelect(pair);
                        setIsOpen(false);
                        setSearch('');
                      }}
                      className={`w-full px-4 py-3 flex items-center justify-between hover:bg-exchange-bg transition-colors ${isSelected ? 'bg-exchange-bg' : ''}`}
                    >
                      <div>
                        <div className="font-medium text-exchange-text">
                          {formatPairSymbol(pair)}
                        </div>
                        <div className="text-xs text-exchange-muted">
                          Vol: {parseFloat(pair.volume_24h || 0).toFixed(2)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className="font-mono text-exchange-text">
                          {formatPrice(pair.last_price)}
                        </div>
                        <div className={`text-xs ${changeColor}`}>
                          {formatChange(pair.price_change_24h)}
                        </div>
                      </div>
                    </button>
                  );
                })
              ) : (
                <div className="p-8 text-center text-exchange-muted">
                  {pairsArray.length === 0 ? 'No trading pairs available' : 'No pairs found'}
                </div>
              )}
            </div>
          </div>
        </>
      )}
    </div>
  );
};

export default TradingPairSelector;
