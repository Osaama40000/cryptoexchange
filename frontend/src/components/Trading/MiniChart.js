/**
 * MiniChart Component
 * ===================
 * Small sparkline chart for market overview cards
 */

import React, { useEffect, useRef } from 'react';
import { createChart } from 'lightweight-charts';

const MiniChart = ({ data = [], color = '#22c55e', height = 60 }) => {
  const chartContainerRef = useRef(null);
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartContainerRef.current) return;

    const chart = createChart(chartContainerRef.current, {
      layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: 'transparent',
      },
      grid: {
        vertLines: { visible: false },
        horzLines: { visible: false },
      },
      rightPriceScale: { visible: false },
      timeScale: { visible: false },
      crosshair: { visible: false },
      handleScroll: false,
      handleScale: false,
    });

    const lineSeries = chart.addAreaSeries({
      lineColor: color,
      topColor: `${color}40`,
      bottomColor: `${color}05`,
      lineWidth: 2,
      priceLineVisible: false,
      lastValueVisible: false,
      crosshairMarkerVisible: false,
    });

    // Generate mock data if not provided
    const chartData = data.length > 0 ? data : generateMockData();
    lineSeries.setData(chartData);
    
    chart.timeScale().fitContent();
    chartRef.current = chart;

    const handleResize = () => {
      if (chartContainerRef.current) {
        chart.applyOptions({
          width: chartContainerRef.current.clientWidth,
          height: height,
        });
      }
    };

    window.addEventListener('resize', handleResize);
    handleResize();

    return () => {
      window.removeEventListener('resize', handleResize);
      chart.remove();
    };
  }, [data, color, height]);

  const generateMockData = () => {
    const points = 50;
    const now = Math.floor(Date.now() / 1000);
    let value = 100;
    
    return Array.from({ length: points }, (_, i) => {
      value += (Math.random() - 0.48) * 2;
      return {
        time: now - (points - i) * 3600,
        value: value,
      };
    });
  };

  return (
    <div 
      ref={chartContainerRef} 
      style={{ height: `${height}px` }}
      className="w-full"
    />
  );
};

export default MiniChart;
