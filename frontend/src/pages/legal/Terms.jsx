/**
 * Terms of Service Page
 */
import React from 'react';

const Terms = () => {
  return (
    <div className="max-w-4xl mx-auto py-8 px-4">
      <h1 className="text-3xl font-bold text-white mb-8">Terms of Service</h1>
      
      <div className="prose prose-invert max-w-none">
        <p className="text-gray-300 mb-6">
          Last updated: {new Date().toLocaleDateString()}
        </p>
        
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">1. Acceptance of Terms</h2>
          <p className="text-gray-300">
            By accessing and using CryptoExchange, you agree to be bound by these Terms of Service
            and all applicable laws and regulations. If you do not agree with any of these terms,
            you are prohibited from using this service.
          </p>
        </section>
        
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">2. Eligibility</h2>
          <p className="text-gray-300">
            You must be at least 18 years old and legally able to enter into contracts to use our services.
            By using our platform, you represent that you meet these requirements.
          </p>
        </section>
        
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">3. Account Registration</h2>
          <p className="text-gray-300">
            You agree to provide accurate, current, and complete information during registration
            and to update such information to keep it accurate, current, and complete.
          </p>
        </section>
        
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">4. Risk Disclosure</h2>
          <p className="text-gray-300">
            Cryptocurrency trading involves substantial risk of loss and is not suitable for every investor.
            The valuation of cryptocurrencies may fluctuate, and you may sustain a total loss of the funds
            you have deposited. You should not trade with funds you cannot afford to lose.
          </p>
        </section>
        
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">5. Prohibited Activities</h2>
          <ul className="text-gray-300 list-disc pl-6 space-y-2">
            <li>Money laundering or terrorist financing</li>
            <li>Market manipulation or wash trading</li>
            <li>Using the platform from restricted jurisdictions</li>
            <li>Attempting to circumvent security measures</li>
            <li>Creating multiple accounts</li>
          </ul>
        </section>
        
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-white mb-4">6. Contact</h2>
          <p className="text-gray-300">
            For questions about these Terms, please contact us at legal@tokenly.com
          </p>
        </section>
      </div>
    </div>
  );
};

export default Terms;
