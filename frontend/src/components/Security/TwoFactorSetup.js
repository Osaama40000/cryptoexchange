/**
 * TwoFactorSetup Component
 * ========================
 * Setup and manage 2FA with QR code
 */

import React, { useState, useEffect } from 'react';
import {
  ShieldCheckIcon,
  ClipboardDocumentIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  EyeIcon,
  EyeSlashIcon
} from '@heroicons/react/24/outline';
import securityService from '../../services/securityService';

const TwoFactorSetup = ({ onUpdate }) => {
  const [status, setStatus] = useState(null);
  const [setupData, setSetupData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [verifyCode, setVerifyCode] = useState('');
  const [disableCode, setDisableCode] = useState('');
  const [disablePassword, setDisablePassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [backupCodes, setBackupCodes] = useState(null);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const [step, setStep] = useState('check'); // check, setup, verify, backup, enabled

  useEffect(() => {
    checkStatus();
  }, []);

  const checkStatus = async () => {
    try {
      setLoading(true);
      const data = await securityService.get2FAStatus();
      setStatus(data);
      setStep(data.is_enabled ? 'enabled' : 'setup');
    } catch (err) {
      // If API fails, assume 2FA is not set up
      setStatus({ is_enabled: false });
      setStep('setup');
    } finally {
      setLoading(false);
    }
  };

  const startSetup = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await securityService.get2FASetup();
      setSetupData(data);
      setStep('verify');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to start 2FA setup. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const verifyAndEnable = async () => {
    if (verifyCode.length !== 6) {
      setError('Please enter a valid 6-digit code');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await securityService.enable2FA(verifyCode);
      setBackupCodes(data.backup_codes);
      setSuccess('Two-Factor Authentication has been enabled successfully!');
      setStep('backup');
      if (onUpdate) onUpdate();
    } catch (err) {
      setError(err.response?.data?.error || 'Invalid verification code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const disable2FA = async () => {
    if (disableCode.length !== 6) {
      setError('Please enter a valid 6-digit code');
      return;
    }
    if (!disablePassword) {
      setError('Please enter your password');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      await securityService.disable2FA(disableCode, disablePassword);
      setSuccess('Two-Factor Authentication has been disabled');
      setStep('setup');
      setStatus({ is_enabled: false });
      setDisableCode('');
      setDisablePassword('');
      if (onUpdate) onUpdate();
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to disable 2FA. Check your code and password.');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setSuccess('Copied to clipboard!');
    setTimeout(() => setSuccess(null), 2000);
  };

  const downloadBackupCodes = () => {
    const content = `
╔══════════════════════════════════════════════════════════════╗
║           CRYPTOEXCHANGE 2FA BACKUP CODES                   ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Keep these codes in a safe place. Each code can only be    ║
║  used once to access your account if you lose your          ║
║  authenticator device.                                       ║
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
${backupCodes.map((code, i) => `║  ${i + 1}. ${code}                                            ║`).join('\n')}
║                                                              ║
╠══════════════════════════════════════════════════════════════╣
║  Generated: ${new Date().toISOString()}              ║
║  Account: ToKeNlY                                    ║
╚══════════════════════════════════════════════════════════════╝
    `.trim();

    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'cryptoexchange-2fa-backup-codes.txt';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Loading state
  if (loading && step === 'check') {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-center">
          <div className="animate-spin h-10 w-10 border-3 border-blue-500 border-t-transparent rounded-full mx-auto mb-4" />
          <p className="text-gray-400">Checking 2FA status...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl">
      {/* Error Message */}
      {error && (
        <div className="mb-6 p-4 bg-red-500/10 border border-red-500/30 rounded-xl flex items-center gap-3 text-red-400">
          <ExclamationTriangleIcon className="w-6 h-6 flex-shrink-0" />
          <span>{error}</span>
          <button
            onClick={() => setError(null)}
            className="ml-auto text-red-400 hover:text-red-300"
          >
            ✕
          </button>
        </div>
      )}

      {/* Success Message */}
      {success && (
        <div className="mb-6 p-4 bg-green-500/10 border border-green-500/30 rounded-xl flex items-center gap-3 text-green-400">
          <CheckCircleIcon className="w-6 h-6 flex-shrink-0" />
          <span>{success}</span>
        </div>
      )}

      {/* STEP: Setup - Initial screen to start 2FA setup */}
      {step === 'setup' && (
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 border border-gray-700 shadow-xl">
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-purple-500 to-blue-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-purple-500/20">
              <ShieldCheckIcon className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-3xl font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              Enable Two-Factor Authentication
            </h2>
            <p className="text-gray-400 mt-3 max-w-md mx-auto">
              Add an extra layer of security to your account using an authenticator app like Google Authenticator or Authy
            </p>
          </div>

          {/* Steps */}
          <div className="space-y-4 mb-8">
            <div className="flex items-start gap-4 p-4 bg-gray-800/50 rounded-xl border border-gray-700/50 hover:border-gray-600 transition-colors">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-sm font-bold shadow-lg">
                1
              </div>
              <div>
                <h3 className="font-semibold text-white">Download an authenticator app</h3>
                <p className="text-gray-400 text-sm mt-1">
                  We recommend <span className="text-blue-400">Google Authenticator</span>, <span className="text-blue-400">Authy</span>, or <span className="text-blue-400">Microsoft Authenticator</span>
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 bg-gray-800/50 rounded-xl border border-gray-700/50 hover:border-gray-600 transition-colors">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-sm font-bold shadow-lg">
                2
              </div>
              <div>
                <h3 className="font-semibold text-white">Scan the QR code</h3>
                <p className="text-gray-400 text-sm mt-1">
                  Use your authenticator app to scan the QR code we'll show you in the next step
                </p>
              </div>
            </div>

            <div className="flex items-start gap-4 p-4 bg-gray-800/50 rounded-xl border border-gray-700/50 hover:border-gray-600 transition-colors">
              <div className="w-10 h-10 bg-gradient-to-br from-blue-500 to-blue-600 rounded-xl flex items-center justify-center text-sm font-bold shadow-lg">
                3
              </div>
              <div>
                <h3 className="font-semibold text-white">Enter verification code</h3>
                <p className="text-gray-400 text-sm mt-1">
                  Enter the 6-digit code from your authenticator app to complete setup
                </p>
              </div>
            </div>
          </div>

          <button
            onClick={startSetup}
            disabled={loading}
            className="w-full py-4 bg-gradient-to-r from-purple-500 to-blue-500 text-white font-semibold rounded-xl hover:from-purple-600 hover:to-blue-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-purple-500/25"
          >
            {loading ? (
              <span className="flex items-center justify-center gap-2">
                <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                Loading...
              </span>
            ) : (
              'Start Setup →'
            )}
          </button>
        </div>
      )}

      {/* STEP: Verify - Show QR code and verify */}
      {step === 'verify' && setupData && (
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 border border-gray-700 shadow-xl">
          <h2 className="text-2xl font-bold text-center mb-6">Scan QR Code</h2>

          {/* QR Code */}
          <div className="flex justify-center mb-6">
            <div className="bg-white p-5 rounded-2xl shadow-xl">
              <img
                src={setupData.qr_code}
                alt="2FA QR Code"
                className="w-52 h-52"
              />
            </div>
          </div>

          {/* Manual Entry Option */}
          <div className="mb-8">
            <p className="text-gray-400 text-sm text-center mb-3">
              Can't scan the QR code? Enter this code manually in your app:
            </p>
            <div className="flex items-center gap-2 bg-gray-800 rounded-xl p-4 border border-gray-700">
              <code className="flex-1 text-center font-mono text-base text-yellow-400 break-all select-all">
                {setupData.secret_key}
              </code>
              <button
                onClick={() => copyToClipboard(setupData.secret_key)}
                className="p-2 hover:bg-gray-700 rounded-lg transition-colors"
                title="Copy to clipboard"
              >
                <ClipboardDocumentIcon className="w-5 h-5 text-gray-400 hover:text-white" />
              </button>
            </div>
          </div>

          {/* Verification Code Input */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-300 mb-3">
              Enter the 6-digit code from your authenticator app
            </label>
            <input
              type="text"
              value={verifyCode}
              onChange={(e) => setVerifyCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
              placeholder="000000"
              className="w-full px-6 py-4 bg-gray-800 border-2 border-gray-700 rounded-xl text-center text-3xl font-mono tracking-[0.5em] focus:border-blue-500 focus:outline-none transition-colors"
              maxLength={6}
              autoComplete="off"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4">
            <button
              onClick={() => {
                setStep('setup');
                setVerifyCode('');
                setSetupData(null);
              }}
              className="flex-1 py-4 bg-gray-800 text-white font-semibold rounded-xl hover:bg-gray-700 transition-colors"
            >
              ← Back
            </button>
            <button
              onClick={verifyAndEnable}
              disabled={loading || verifyCode.length !== 6}
              className="flex-1 py-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-xl hover:from-green-600 hover:to-emerald-600 transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-green-500/25"
            >
              {loading ? (
                <span className="flex items-center justify-center gap-2">
                  <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                  Verifying...
                </span>
              ) : (
                'Enable 2FA ✓'
              )}
            </button>
          </div>
        </div>
      )}

      {/* STEP: Backup - Show backup codes */}
      {step === 'backup' && backupCodes && (
        <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 border border-gray-700 shadow-xl">
          <div className="text-center mb-8">
            <div className="w-20 h-20 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg shadow-green-500/20">
              <CheckCircleIcon className="w-10 h-10 text-white" />
            </div>
            <h2 className="text-3xl font-bold text-green-400">2FA Enabled Successfully!</h2>
            <p className="text-gray-400 mt-3">
              Save these backup codes in a secure location
            </p>
          </div>

          {/* Warning */}
          <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 mb-6">
            <div className="flex items-start gap-3">
              <ExclamationTriangleIcon className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-0.5" />
              <div>
                <p className="text-yellow-400 font-semibold">Important - Save These Codes!</p>
                <p className="text-yellow-400/80 text-sm mt-1">
                  These backup codes will only be shown once. Each code can be used once to access your account if you lose your authenticator device. Store them securely!
                </p>
              </div>
            </div>
          </div>

          {/* Backup Codes Grid */}
          <div className="grid grid-cols-2 gap-3 mb-6">
            {backupCodes.map((code, index) => (
              <div
                key={index}
                className="bg-gray-800 p-4 rounded-xl font-mono text-center text-lg border border-gray-700 hover:border-gray-600 transition-colors select-all"
              >
                <span className="text-gray-500 text-sm mr-2">{index + 1}.</span>
                <span className="text-white">{code}</span>
              </div>
            ))}
          </div>

          {/* Action Buttons */}
          <div className="flex gap-4 mb-4">
            <button
              onClick={() => copyToClipboard(backupCodes.join('\n'))}
              className="flex-1 py-4 bg-gray-800 text-white font-semibold rounded-xl hover:bg-gray-700 transition-colors flex items-center justify-center gap-2"
            >
              <ClipboardDocumentIcon className="w-5 h-5" />
              Copy All Codes
            </button>
            <button
              onClick={downloadBackupCodes}
              className="flex-1 py-4 bg-blue-600 text-white font-semibold rounded-xl hover:bg-blue-500 transition-colors"
            >
              📥 Download as File
            </button>
          </div>

          <button
            onClick={() => {
              setStep('enabled');
              setBackupCodes(null);
              checkStatus();
            }}
            className="w-full py-4 bg-gradient-to-r from-green-500 to-emerald-500 text-white font-semibold rounded-xl hover:from-green-600 hover:to-emerald-600 transition-all duration-200 shadow-lg shadow-green-500/25"
          >
            I've Saved My Backup Codes ✓
          </button>
        </div>
      )}

      {/* STEP: Enabled - 2FA is active, show status and disable option */}
      {step === 'enabled' && (
        <div className="space-y-6">
          {/* Status Card */}
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 border border-green-500/30 shadow-xl">
            <div className="flex items-center gap-6">
              <div className="w-16 h-16 bg-gradient-to-br from-green-500 to-emerald-500 rounded-2xl flex items-center justify-center shadow-lg shadow-green-500/20">
                <CheckCircleIcon className="w-8 h-8 text-white" />
              </div>
              <div>
                <h2 className="text-2xl font-bold text-white">Two-Factor Authentication</h2>
                <p className="text-green-400 font-semibold mt-1">✓ Enabled and Active</p>
                <p className="text-gray-400 text-sm mt-2">
                  Your account is protected with an additional layer of security
                </p>
              </div>
            </div>

            {/* Backup Codes Remaining */}
            {status?.backup_codes_remaining !== undefined && (
              <div className="mt-6 p-4 bg-gray-800/50 rounded-xl border border-gray-700">
                <div className="flex items-center justify-between">
                  <span className="text-gray-400">Backup codes remaining</span>
                  <span className={`text-xl font-bold ${
                    status.backup_codes_remaining > 3 ? 'text-green-400' :
                    status.backup_codes_remaining > 0 ? 'text-yellow-400' : 'text-red-400'
                  }`}>
                    {status.backup_codes_remaining} / 10
                  </span>
                </div>
                {status.backup_codes_remaining <= 3 && (
                  <p className="text-yellow-400 text-sm mt-2">
                    ⚠️ You're running low on backup codes. Consider regenerating them.
                  </p>
                )}
              </div>
            )}
          </div>

          {/* Disable 2FA Section */}
          <div className="bg-gradient-to-br from-gray-900 to-gray-800 rounded-2xl p-8 border border-red-500/30 shadow-xl">
            <h3 className="text-xl font-bold text-red-400 mb-2">Disable Two-Factor Authentication</h3>
            <p className="text-gray-400 text-sm mb-6">
              Warning: This will remove the extra security layer from your account. You'll need your current 2FA code and password to disable.
            </p>

            <div className="space-y-4">
              {/* 2FA Code Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Current 2FA Code
                </label>
                <input
                  type="text"
                  value={disableCode}
                  onChange={(e) => setDisableCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  placeholder="000000"
                  className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl font-mono text-lg tracking-widest focus:border-red-500 focus:outline-none transition-colors"
                  maxLength={6}
                />
              </div>

              {/* Password Input */}
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  Account Password
                </label>
                <div className="relative">
                  <input
                    type={showPassword ? 'text' : 'password'}
                    value={disablePassword}
                    onChange={(e) => setDisablePassword(e.target.value)}
                    placeholder="Enter your account password"
                    className="w-full px-4 py-3 bg-gray-800 border border-gray-700 rounded-xl focus:border-red-500 focus:outline-none transition-colors pr-12"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 hover:text-gray-300 transition-colors"
                  >
                    {showPassword ? (
                      <EyeSlashIcon className="w-5 h-5" />
                    ) : (
                      <EyeIcon className="w-5 h-5" />
                    )}
                  </button>
                </div>
              </div>

              {/* Disable Button */}
              <button
                onClick={disable2FA}
                disabled={loading || disableCode.length !== 6 || !disablePassword}
                className="w-full py-4 bg-red-600 text-white font-semibold rounded-xl hover:bg-red-500 transition-colors disabled:opacity-50 disabled:cursor-not-allowed mt-4"
              >
                {loading ? (
                  <span className="flex items-center justify-center gap-2">
                    <div className="animate-spin h-5 w-5 border-2 border-white border-t-transparent rounded-full" />
                    Disabling...
                  </span>
                ) : (
                  '🔓 Disable Two-Factor Authentication'
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TwoFactorSetup;