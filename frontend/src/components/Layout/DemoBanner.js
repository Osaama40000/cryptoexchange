import React, { useState } from 'react';
import { XMarkIcon, ExclamationTriangleIcon } from '@heroicons/react/24/outline';

const DemoBanner = () => {
  const [isVisible, setIsVisible] = useState(false);

  if (!isVisible) return null;

  return (
    <div className="bg-gradient-to-r from-warning/20 via-warning/10 to-warning/20 border-b border-warning/30">
      <div className="max-w-7xl mx-auto px-4 py-2">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2 text-warning text-sm">
            <ExclamationTriangleIcon className="h-5 w-5 flex-shrink-0" />
            <span className="font-medium">
              <span className="hidden sm:inline">⚠️ DEMO MODE: This is a demonstration exchange. No real funds are involved. </span>
              <span className="sm:hidden">⚠️ DEMO MODE - No real funds</span>
            </span>
          </div>
          <button
            onClick={() => setIsVisible(false)}
            className="p-1 hover:bg-warning/20 rounded transition-colors"
          >
            <XMarkIcon className="h-4 w-4 text-warning" />
          </button>
        </div>
      </div>
    </div>
  );
};

export default DemoBanner;