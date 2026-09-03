/**
 * Corporate Asset Portfolio Matrix Dashboard
 * Real-time vulnerability tracking with CSV export
 * 2026-09-03T18:16:10.623Z
 */

'use client';

import React, { useState } from 'react';
import { CORPORATE_ASSETS, getPortfolioSummary, generateCSVData, generateCVETrackerCSV, getVulnerableAssets } from '@/lib/corporate-portfolio';

interface CorporateAsset {
  asset_id: string;
  asset_name: string;
  vendor: string;
  product: string;
  current_version: string;
  latest_safe_version: string;
  is_vulnerable: boolean;
  cve_count: number;
  severity_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SAFE";
  cves: string[];
  business_unit: string;
  deployment_location: string;
  owner: string;
  status: "OK" | "VULNERABLE" | "DEGRADED" | "END_OF_LIFE";
}

export default function CorporatePortfolioMatrix() {
  const [filterSeverity, setFilterSeverity] = useState<string | null>(null);
  const [filterVendor, setFilterVendor] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');

  const portfolio = getPortfolioSummary();
  const vulnerable_assets = getVulnerableAssets();

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return 'bg-red-900 text-red-200 border-red-700';
      case 'HIGH': return 'bg-orange-900 text-orange-200 border-orange-700';
      case 'MEDIUM': return 'bg-yellow-900 text-yellow-200 border-yellow-700';
      case 'LOW': return 'bg-blue-900 text-blue-200 border-blue-700';
      case 'SAFE': return 'bg-green-900 text-green-200 border-green-700';
      default: return 'bg-gray-900 text-gray-200 border-gray-700';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL': return '🔴';
      case 'HIGH': return '🟠';
      case 'MEDIUM': return '🟡';
      case 'LOW': return '🔵';
      case 'SAFE': return '🟢';
      default: return '⚪';
    }
  };

  const filteredAssets = CORPORATE_ASSETS.filter(asset => {
    const matchesSeverity = !filterSeverity || asset.severity_level === filterSeverity;
    const matchesVendor = !filterVendor || asset.vendor === filterVendor;
    const matchesStatus = !filterStatus || asset.status === filterStatus;
    const matchesSearch = !searchTerm || 
      asset.asset_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      asset.asset_id.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesSeverity && matchesVendor && matchesStatus && matchesSearch;
  });

  const handleExportPortfolio = () => {
    const csv = generateCSVData();
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `patch-radar-portfolio-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const handleExportCVEs = () => {
    const csv = generateCVETrackerCSV();
    const blob = new Blob([csv], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `patch-radar-cve-tracker-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
  };

  const uniqueVendors = [...new Set(CORPORATE_ASSETS.map(a => a.vendor))];

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-gray-900 to-gray-950 text-gray-200">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-900/50 backdrop-blur">
        <div className="max-w-7xl mx-auto px-6 py-8">
          <div className="flex items-center justify-between gap-4 mb-6">
            <div>
              <h1 className="text-4xl font-bold text-white flex items-center gap-3 mb-2">
                <span className="text-2xl">📊</span>
                Corporate Asset Portfolio Matrix
              </h1>
              <p className="text-gray-400 text-sm">Real-time vulnerability tracking across all infrastructure assets</p>
            </div>
            <div className="text-right text-xs text-gray-500">
              Last updated: {new Date().toLocaleString()}
            </div>
          </div>

          {/* Quick Stats */}
          <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-6">
            <div className="bg-gray-800/50 border border-gray-700 rounded-lg p-4">
              <div className="text-3xl font-bold text-white">{portfolio.total_assets}</div>
              <div className="text-xs text-gray-400 mt-1">Total Assets</div>
            </div>
            <div className="bg-red-950/50 border border-red-900 rounded-lg p-4">
              <div className="text-3xl font-bold text-red-400">{portfolio.total_critical_vulnerabilities}</div>
              <div className="text-xs text-red-400 mt-1">CRITICAL</div>
            </div>
            <div className="bg-orange-950/50 border border-orange-900 rounded-lg p-4">
              <div className="text-3xl font-bold text-orange-400">{portfolio.total_high_vulnerabilities}</div>
              <div className="text-xs text-orange-400 mt-1">HIGH</div>
            </div>
            <div className="bg-green-950/50 border border-green-900 rounded-lg p-4">
              <div className="text-3xl font-bold text-green-400">{portfolio.total_safe_assets}</div>
              <div className="text-xs text-green-400 mt-1">SAFE</div>
            </div>
            <div className="bg-blue-950/50 border border-blue-900 rounded-lg p-4">
              <div className="text-3xl font-bold text-blue-400">{portfolio.compliance_score.toFixed(1)}%</div>
              <div className="text-xs text-blue-400 mt-1">Compliance</div>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Controls & Exports */}
        <div className="bg-gray-800/30 border border-gray-700 rounded-lg p-6 mb-6">
          <div className="flex flex-col gap-4">
            {/* Search & Filters */}
            <div className="flex flex-col md:flex-row gap-3">
              <div className="flex-1">
                <input
                  type="text"
                  placeholder="Search assets by name or ID..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded text-white placeholder-gray-500 focus:outline-none focus:border-blue-500"
                />
              </div>
              
              <select
                value={filterVendor || ''}
                onChange={(e) => setFilterVendor(e.target.value || null)}
                className="px-4 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">All Vendors</option>
                {uniqueVendors.map(v => (
                  <option key={v} value={v}>{v}</option>
                ))}
              </select>

              <select
                value={filterSeverity || ''}
                onChange={(e) => setFilterSeverity(e.target.value || null)}
                className="px-4 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">All Severity</option>
                <option value="CRITICAL">CRITICAL</option>
                <option value="HIGH">HIGH</option>
                <option value="MEDIUM">MEDIUM</option>
                <option value="LOW">LOW</option>
                <option value="SAFE">SAFE</option>
              </select>

              <select
                value={filterStatus || ''}
                onChange={(e) => setFilterStatus(e.target.value || null)}
                className="px-4 py-2 bg-gray-900 border border-gray-700 rounded text-white focus:outline-none focus:border-blue-500"
              >
                <option value="">All Status</option>
                <option value="OK">OK</option>
                <option value="VULNERABLE">VULNERABLE</option>
                <option value="DEGRADED">DEGRADED</option>
              </select>
            </div>

            {/* Export Buttons */}
            <div className="flex gap-3 flex-wrap">
              <button
                onClick={handleExportPortfolio}
                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded font-medium transition"
              >
                <span>📥</span> Export Portfolio (CSV)
              </button>
              <button
                onClick={handleExportCVEs}
                className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded font-medium transition"
              >
                <span>📥</span> Export CVE Tracker (CSV)
              </button>
              <button
                onClick={() => {
                  setFilterSeverity(null);
                  setFilterVendor(null);
                  setFilterStatus(null);
                  setSearchTerm('');
                }}
                className="flex items-center gap-2 px-4 py-2 bg-gray-700 hover:bg-gray-600 text-white rounded font-medium transition"
              >
                <span>🔄</span> Reset Filters
              </button>
            </div>

            <div className="text-xs text-gray-400">
              Showing {filteredAssets.length} of {CORPORATE_ASSETS.length} assets
            </div>
          </div>
        </div>

        {/* Vulnerable Assets Alert */}
        {vulnerable_assets.length > 0 && (
          <div className="bg-red-950/30 border border-red-900 rounded-lg p-4 mb-6">
            <div className="flex items-start gap-3">
              <span className="text-2xl">⚠️</span>
              <div className="flex-1">
                <h3 className="font-bold text-red-400 mb-2">{vulnerable_assets.length} Assets Require Immediate Attention</h3>
                <div className="flex flex-wrap gap-2">
                  {vulnerable_assets.slice(0, 5).map(asset => (
                    <span key={asset.asset_id} className="text-xs bg-red-900 px-2 py-1 rounded">
                      {asset.asset_name}: {asset.cve_count} CVE{asset.cve_count > 1 ? 's' : ''}
                    </span>
                  ))}
                  {vulnerable_assets.length > 5 && (
                    <span className="text-xs bg-red-900 px-2 py-1 rounded">+{vulnerable_assets.length - 5} more</span>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Asset Matrix Table */}
        <div className="bg-gray-800/30 border border-gray-700 rounded-lg overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="bg-gray-900/80 border-b border-gray-700">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-300">Asset</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-300">Vendor</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-300">Current</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-300">Latest Safe</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-300">Status</th>
                  <th className="px-4 py-3 text-center text-xs font-semibold text-gray-300">CVEs</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-300">Unit</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-gray-300">Owner</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-700">
                {filteredAssets.map((asset) => (
                  <tr key={asset.asset_id} className="hover:bg-gray-700/20 transition">
                    <td className="px-4 py-3 text-sm">
                      <div className="font-mono text-gray-300">{asset.asset_id}</div>
                      <div className="text-xs text-gray-500">{asset.asset_name}</div>
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-300">{asset.vendor}</td>
                    <td className="px-4 py-3 text-sm font-mono text-gray-300">{asset.current_version}</td>
                    <td className="px-4 py-3 text-sm font-mono text-green-400">{asset.latest_safe_version}</td>
                    <td className="px-4 py-3 text-center">
                      <span className={`inline-block px-2 py-1 rounded text-xs font-bold border ${getSeverityColor(asset.severity_level)}`}>
                        {getSeverityIcon(asset.severity_level)} {asset.severity_level}
                      </span>
                    </td>
                    <td className="px-4 py-3 text-center">
                      {asset.cve_count > 0 ? (
                        <span className="inline-block px-2 py-1 rounded text-xs font-bold bg-red-900 text-red-200">
                          {asset.cve_count}
                        </span>
                      ) : (
                        <span className="text-gray-500">—</span>
                      )}
                    </td>
                    <td className="px-4 py-3 text-sm text-gray-400">{asset.business_unit}</td>
                    <td className="px-4 py-3 text-sm text-gray-400">{asset.owner}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* CVE Details Section */}
        {filteredAssets.some(a => a.cves.length > 0) && (
          <div className="mt-8">
            <h2 className="text-2xl font-bold text-white mb-4 flex items-center gap-2">
              <span>🔍</span> CVE Details
            </h2>
            <div className="space-y-3">
              {filteredAssets
                .filter(a => a.cves.length > 0)
                .map(asset => (
                  <div key={asset.asset_id} className="bg-gray-800/30 border border-gray-700 rounded-lg p-4">
                    <div className="flex items-start justify-between mb-2">
                      <div>
                        <h3 className="font-bold text-white">{asset.asset_name}</h3>
                        <p className="text-sm text-gray-400">{asset.vendor} • {asset.current_version} → {asset.latest_safe_version}</p>
                      </div>
                      <span className={`inline-block px-2 py-1 rounded text-xs font-bold border ${getSeverityColor(asset.severity_level)}`}>
                        {asset.severity_level}
                      </span>
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {asset.cves.map(cve => (
                        <span key={cve} className="text-xs bg-red-900 text-red-200 px-2 py-1 rounded font-mono">
                          {cve}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="border-t border-gray-800 bg-gray-900/50 backdrop-blur mt-12">
        <div className="max-w-7xl mx-auto px-6 py-6 text-center text-sm text-gray-500">
          Patch Radar • Corporate Asset Portfolio Matrix • Data as of {new Date().toISOString().split('T')[0]}
        </div>
      </div>
    </div>
  );
}
