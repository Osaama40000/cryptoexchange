import P2PTransfer from '../components/P2PTransfer';
import React from 'react';

const P2PTransferPage = () => {
  return (
    <div className="p2p-transfer-page">
      <style>{`
        .p2p-transfer-page {
          min-height: 100vh;
          background: linear-gradient(180deg, #0f172a 0%, #1e293b 100%);
          padding: 40px 20px;
        }

        .page-header {
          max-width: 480px;
          margin: 0 auto 32px;
          text-align: center;
        }

        .page-title {
          color: white;
          font-size: 32px;
          font-weight: 700;
          margin: 0 0 12px 0;
          background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }

        .page-subtitle {
          color: #94a3b8;
          font-size: 16px;
          margin: 0;
        }

        .security-notice {
          max-width: 480px;
          margin: 32px auto 0;
          background: rgba(234, 179, 8, 0.1);
          border: 1px solid rgba(234, 179, 8, 0.3);
          border-radius: 12px;
          padding: 16px;
          display: flex;
          gap: 12px;
          align-items: flex-start;
        }

        .security-icon {
          font-size: 20px;
          flex-shrink: 0;
        }

        .security-text {
          color: #fbbf24;
          font-size: 13px;
          line-height: 1.5;
        }

        .security-text strong {
          display: block;
          margin-bottom: 4px;
        }

        .features-grid {
          max-width: 480px;
          margin: 32px auto 0;
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 12px;
        }

        .feature-item {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 12px;
          padding: 16px;
          text-align: center;
        }
        .feature-icon {
          font-size: 24px;
          margin-bottom: 8px;
        }

        .feature-text {
          color: #94a3b8;
          font-size: 12px;
        }
      `}</style>

      <div className="page-header">
        <h1 className="page-title">P2P Crypto Transfer</h1>
        <p className="page-subtitle">
          Send and receive cryptocurrency directly from your wallet
        </p>
      </div>

      <P2PTransfer />

      <div className="security-notice">
        <span className="security-icon">⚠️</span>
        <div className="security-text">
          <strong>Security Reminder</strong>
          Always verify the recipient address before sending. Cryptocurrency transactions
          are irreversible. We never ask for your private keys or seed phrases.
        </div>
      </div>

      <div className="features-grid">
        <div className="feature-item">
          <div className="feature-icon">🔒</div>
          <div className="feature-text">Non-Custodial</div>
        </div>
        <div className="feature-item">
          <div className="feature-icon">⚡</div>
          <div className="feature-text">Instant Transfers</div>
        </div>
        <div className="feature-item">
          <div className="feature-icon">🌐</div>
          <div className="feature-text">Multi-Network</div>
        </div>
      </div>
    </div>
  );
};

export default P2PTransferPage;