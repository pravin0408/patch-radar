/**
 * Infrastructure Vulnerability Matrix Component
 * Displays ALL vendors, models, versions, and CVEs in unified view
 * 2026-09-02T14:09:11.786Z
 */

'use client';

import React, { useState } from 'react';
import { INFRASTRUCTURE_MATRIX, getSummaryStats } from '@/lib/infrastructure-matrix';

interface Version {
  version: string;
  release_date: string;
  ga_status: boolean;
  is_safe: boolean;
  severity: string;
  cve_count: number;
  cves: string[];
  advisory_url: string;
  status: string;
}

interface Model {
  model_id: string;
  model_name: string;
  component_type: string;
  versions: Version[];
}

interface Vendor {
  vendor_id: string;
  vendor_name: string;
  status: string;
  critical_count: number;
  high_count: number;
  models: Model[];
}

export default function InfrastructureMatrix() {
  const [selectedVendor, setSelectedVendor] = useState<string | null>(null);
  const [expandedModels, setExpandedModels] = useState<Set<string>>(new Set());
  const matrix = INFRASTRUCTURE_MATRIX;
  const stats = getSummaryStats();

  const toggleModel = (modelId: string) => {
    const newExpanded = new Set(expandedModels);
    if (newExpanded.has(modelId)) {
      newExpanded.delete(modelId);
    } else {
      newExpanded.add(modelId);
    }
    setExpandedModels(newExpanded);
  };

  const getSeverityColor = (severity: string) => {
    if (severity.includes('CRITICAL')) return 'bg-red-100 text-red-800 border-red-300';
    if (severity.includes('HIGH')) return 'bg-orange-100 text-orange-800 border-orange-300';
    if (severity.includes('MEDIUM')) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    if (severity.includes('SAFE')) return 'bg-green-100 text-green-800 border-green-300';
    return 'bg-gray-100 text-gray-800 border-gray-300';
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 bg-white">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Infrastructure Vulnerability Matrix
        </h1>
        <p className="text-gray-600 text-sm">
          Real-time security posture across all vendors, products, and versions
        </p>
        <p className="text-gray-500 text-xs mt-1">
          Last updated: 2026-09-02T14:09:11.786Z | Data freshness: LIVE
        </p>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="text-2xl font-bold text-blue-900">{stats.totalVendors}</div>
          <div className="text-sm text-blue-700">Vendors</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
          <div className="text-2xl font-bold text-purple-900">{stats.totalModels}</div>
          <div className="text-sm text-purple-700">Products</div>
        </div>
        <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
          <div className="text-2xl font-bold text-indigo-900">{stats.totalVersions}</div>
          <div className="text-sm text-indigo-700">Total Versions</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="text-2xl font-bold text-green-900">{stats.safeVersions}</div>
          <div className="text-sm text-green-700">Safe Versions</div>
        </div>
      </div>

      {/* Risk Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-red-700 font-semibold">CRITICAL CVEs</div>
              <div className="text-3xl font-bold text-red-900">{stats.criticalCVEs}</div>
            </div>
            <div className="text-5xl">🔴</div>
          </div>
          <div className="text-xs text-red-600 mt-2">Immediate action required</div>
        </div>

        <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-orange-700 font-semibold">HIGH CVEs</div>
              <div className="text-3xl font-bold text-orange-900">{stats.highCVEs}</div>
            </div>
            <div className="text-5xl">🟠</div>
          </div>
          <div className="text-xs text-orange-600 mt-2">Plan upgrade within week</div>
        </div>

        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-green-700 font-semibold">Compliance Score</div>
              <div className="text-3xl font-bold text-green-900">
                {stats.complianceRating.toFixed(1)}%
              </div>
            </div>
            <div className="text-5xl">✅</div>
          </div>
          <div className="text-xs text-green-600 mt-2">Safe versions deployed</div>
        </div>
      </div>

      {/* Vendor Filter */}
      <div className="mb-6">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedVendor(null)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              selectedVendor === null
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Vendors
          </button>
          {matrix.vendors.map((vendor) => (
            <button
              key={vendor.vendor_id}
              onClick={() => setSelectedVendor(vendor.vendor_id)}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                selectedVendor === vendor.vendor_id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {vendor.vendor_name}
              {vendor.critical_count > 0 && (
                <span className="ml-2 inline-block bg-red-500 text-white text-xs px-2 py-1 rounded">
                  {vendor.critical_count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Infrastructure Matrix */}
      <div className="space-y-6">
        {matrix.vendors
          .filter((vendor) => selectedVendor === null || vendor.vendor_id === selectedVendor)
          .map((vendor) => (
            <div key={vendor.vendor_id} className="border border-gray-300 rounded-lg overflow-hidden">
              {/* Vendor Header */}
              <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-3xl">🏢</div>
                    <div>
                      <h2 className="text-xl font-bold">{vendor.vendor_name}</h2>
                      <p className="text-gray-300 text-sm">
                        {vendor.models.length} product line(s) | Status: {vendor.status}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-4 text-right">
                    {vendor.critical_count > 0 && (
                      <div>
                        <div className="text-2xl font-bold text-red-400">{vendor.critical_count}</div>
                        <div className="text-xs text-gray-300">CRITICAL</div>
                      </div>
                    )}
                    {vendor.high_count > 0 && (
                      <div>
                        <div className="text-2xl font-bold text-orange-400">{vendor.high_count}</div>
                        <div className="text-xs text-gray-300">HIGH</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Models */}
              <div className="divide-y divide-gray-200">
                {vendor.models.map((model) => (
                  <div key={model.model_id} className="bg-white">
                    {/* Model Header */}
                    <button
                      onClick={() => toggleModel(model.model_id)}
                      className="w-full p-4 hover:bg-gray-50 transition flex items-center justify-between"
                    >
                      <div className="flex items-center gap-4 text-left">
                        <div className="text-2xl">
                          {expandedModels.has(model.model_id) ? '▼' : '▶'}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{model.model_name}</h3>
                          <p className="text-sm text-gray-600">{model.component_type}</p>
                        </div>
                      </div>
                      <div className="text-sm font-medium text-gray-700">
                        {model.versions.length} versions
                      </div>
                    </button>

                    {/* Versions Table */}
                    {expandedModels.has(model.model_id) && (
                      <div className="bg-gray-50 p-4 border-t border-gray-200">
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-300 bg-white">
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                                  Version
                                </th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                                  Released
                                </th>
                                <th className="text-center py-3 px-4 font-semibold text-gray-700">
                                  Status
                                </th>
                                <th className="text-center py-3 px-4 font-semibold text-gray-700">
                                  CVEs
                                </th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                                  Details
                                </th>
                                <th className="text-center py-3 px-4 font-semibold text-gray-700">
                                  Advisory
                                </th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {model.versions.map((version, idx) => (
                                <tr
                                  key={idx}
                                  className={`${
                                    version.is_safe ? 'bg-white' : 'bg-red-50'
                                  } hover:bg-opacity-80 transition`}
                                >
                                  <td className="py-3 px-4 font-mono text-gray-900 font-semibold">
                                    {version.version}
                                  </td>
                                  <td className="py-3 px-4 text-gray-700">
                                    {new Date(version.release_date).toLocaleDateString('en-US', {
                                      year: 'numeric',
                                      month: 'short',
                                      day: 'numeric',
                                    })}
                                  </td>
                                  <td className="py-3 px-4 text-center">
                                    <span
                                      className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border ${getSeverityColor(
                                        version.severity
                                      )}`}
                                    >
                                      {version.severity}
                                    </span>
                                  </td>
                                  <td className="py-3 px-4 text-center">
                                    {version.cve_count > 0 ? (
                                      <span className="inline-block bg-red-100 text-red-800 px-2 py-1 rounded text-xs font-bold">
                                        {version.cve_count}
                                      </span>
                                    ) : (
                                      <span className="text-gray-400">—</span>
                                    )}
                                  </td>
                                  <td className="py-3 px-4 text-gray-700 text-xs">
                                    <div>{version.status}</div>
                                    {version.cves.length > 0 && (
                                      <div className="mt-1 text-gray-600 font-mono">
                                        {version.cves.slice(0, 2).join(', ')}
                                        {version.cves.length > 2 && ` +${version.cves.length - 2}`}
                                      </div>
                                    )}
                                  </td>
                                  <td className="py-3 px-4 text-center">
                                    <a
                                      href={version.advisory_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-600 hover:text-blue-800 font-semibold underline"
                                    >
                                      Link ↗
                                    </a>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
      </div>

      {/* Legend */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-3">Legend</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 bg-red-200 rounded border border-red-300"></span>
            <span className="text-gray-700">CRITICAL - Action Required</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 bg-orange-200 rounded border border-orange-300"></span>
            <span className="text-gray-700">HIGH - Plan Upgrade</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 bg-yellow-200 rounded border border-yellow-300"></span>
            <span className="text-gray-700">MEDIUM - Monitor</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 bg-green-200 rounded border border-green-300"></span>
            <span className="text-gray-700">SAFE - No CVEs</span>
          </div>
        </div>
      </div>
    </div>
  );
}

interface Version {
  version: string;
  release_date: string;
  ga_status: boolean;
  is_safe: boolean;
  severity: string;
  cve_count: number;
  cves: string[];
  advisory_url: string;
  status: string;
}

interface Model {
  model_id: string;
  model_name: string;
  component_type: string;
  versions: Version[];
}

interface Vendor {
  vendor_id: string;
  vendor_name: string;
  status: string;
  critical_count: number;
  high_count: number;
  models: Model[];
}

export default function InfrastructureMatrix() {
  const [selectedVendor, setSelectedVendor] = useState<string | null>(null);
  const [expandedModels, setExpandedModels] = useState<Set<string>>(new Set());
  const matrix = getInfrastructureMatrix();
  const stats = getSummaryStats();

  const toggleModel = (modelId: string) => {
    const newExpanded = new Set(expandedModels);
    if (newExpanded.has(modelId)) {
      newExpanded.delete(modelId);
    } else {
      newExpanded.add(modelId);
    }
    setExpandedModels(newExpanded);
  };

  const getSeverityColor = (severity: string) => {
    if (severity.includes('CRITICAL')) return 'bg-red-100 text-red-800 border-red-300';
    if (severity.includes('HIGH')) return 'bg-orange-100 text-orange-800 border-orange-300';
    if (severity.includes('MEDIUM')) return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    if (severity.includes('SAFE')) return 'bg-green-100 text-green-800 border-green-300';
    return 'bg-gray-100 text-gray-800 border-gray-300';
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-6 bg-white">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-4xl font-bold text-gray-900 mb-2">
          Infrastructure Vulnerability Matrix
        </h1>
        <p className="text-gray-600 text-sm">
          Real-time security posture across all vendors, products, and versions
        </p>
        <p className="text-gray-500 text-xs mt-1">
          Last updated: 2026-09-02T13:58:03.734Z | Data freshness: LIVE
        </p>
      </div>

      {/* Summary Statistics */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
        <div className="bg-blue-50 p-4 rounded-lg border border-blue-200">
          <div className="text-2xl font-bold text-blue-900">{stats.totalVendors}</div>
          <div className="text-sm text-blue-700">Vendors</div>
        </div>
        <div className="bg-purple-50 p-4 rounded-lg border border-purple-200">
          <div className="text-2xl font-bold text-purple-900">{stats.totalModels}</div>
          <div className="text-sm text-purple-700">Products</div>
        </div>
        <div className="bg-indigo-50 p-4 rounded-lg border border-indigo-200">
          <div className="text-2xl font-bold text-indigo-900">{stats.totalVersions}</div>
          <div className="text-sm text-indigo-700">Total Versions</div>
        </div>
        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="text-2xl font-bold text-green-900">{stats.safeVersions}</div>
          <div className="text-sm text-green-700">Safe Versions</div>
        </div>
      </div>

      {/* Risk Summary */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="bg-red-50 p-4 rounded-lg border border-red-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-red-700 font-semibold">CRITICAL CVEs</div>
              <div className="text-3xl font-bold text-red-900">{stats.criticalCVEs}</div>
            </div>
            <div className="text-5xl">🔴</div>
          </div>
          <div className="text-xs text-red-600 mt-2">Immediate action required</div>
        </div>

        <div className="bg-orange-50 p-4 rounded-lg border border-orange-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-orange-700 font-semibold">HIGH CVEs</div>
              <div className="text-3xl font-bold text-orange-900">{stats.highCVEs}</div>
            </div>
            <div className="text-5xl">🟠</div>
          </div>
          <div className="text-xs text-orange-600 mt-2">Plan upgrade within week</div>
        </div>

        <div className="bg-green-50 p-4 rounded-lg border border-green-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-green-700 font-semibold">Compliance Score</div>
              <div className="text-3xl font-bold text-green-900">
                {stats.complianceRating.toFixed(1)}%
              </div>
            </div>
            <div className="text-5xl">✅</div>
          </div>
          <div className="text-xs text-green-600 mt-2">Safe versions deployed</div>
        </div>
      </div>

      {/* Vendor Filter */}
      <div className="mb-6">
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => setSelectedVendor(null)}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              selectedVendor === null
                ? 'bg-blue-600 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            All Vendors
          </button>
          {matrix.data.map((vendor) => (
            <button
              key={vendor.vendor_id}
              onClick={() => setSelectedVendor(vendor.vendor_id)}
              className={`px-4 py-2 rounded-lg font-medium transition ${
                selectedVendor === vendor.vendor_id
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {vendor.vendor_name}
              {vendor.critical_count > 0 && (
                <span className="ml-2 inline-block bg-red-500 text-white text-xs px-2 py-1 rounded">
                  {vendor.critical_count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Infrastructure Matrix */}
      <div className="space-y-6">
        {matrix.data
          .filter((vendor) => selectedVendor === null || vendor.vendor_id === selectedVendor)
          .map((vendor) => (
            <div key={vendor.vendor_id} className="border border-gray-300 rounded-lg overflow-hidden">
              {/* Vendor Header */}
              <div className="bg-gradient-to-r from-gray-900 to-gray-800 text-white p-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className="text-3xl">🏢</div>
                    <div>
                      <h2 className="text-xl font-bold">{vendor.vendor_name}</h2>
                      <p className="text-gray-300 text-sm">
                        {vendor.models.length} product line(s) | Status: {vendor.status}
                      </p>
                    </div>
                  </div>
                  <div className="flex gap-4 text-right">
                    {vendor.critical_count > 0 && (
                      <div>
                        <div className="text-2xl font-bold text-red-400">{vendor.critical_count}</div>
                        <div className="text-xs text-gray-300">CRITICAL</div>
                      </div>
                    )}
                    {vendor.high_count > 0 && (
                      <div>
                        <div className="text-2xl font-bold text-orange-400">{vendor.high_count}</div>
                        <div className="text-xs text-gray-300">HIGH</div>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Models */}
              <div className="divide-y divide-gray-200">
                {vendor.models.map((model) => (
                  <div key={model.model_id} className="bg-white">
                    {/* Model Header */}
                    <button
                      onClick={() => toggleModel(model.model_id)}
                      className="w-full p-4 hover:bg-gray-50 transition flex items-center justify-between"
                    >
                      <div className="flex items-center gap-4 text-left">
                        <div className="text-2xl">
                          {expandedModels.has(model.model_id) ? '▼' : '▶'}
                        </div>
                        <div>
                          <h3 className="font-semibold text-gray-900">{model.model_name}</h3>
                          <p className="text-sm text-gray-600">{model.component_type}</p>
                        </div>
                      </div>
                      <div className="text-sm font-medium text-gray-700">
                        {model.versions.length} versions
                      </div>
                    </button>

                    {/* Versions Table */}
                    {expandedModels.has(model.model_id) && (
                      <div className="bg-gray-50 p-4 border-t border-gray-200">
                        <div className="overflow-x-auto">
                          <table className="w-full text-sm">
                            <thead>
                              <tr className="border-b border-gray-300 bg-white">
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                                  Version
                                </th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                                  Released
                                </th>
                                <th className="text-center py-3 px-4 font-semibold text-gray-700">
                                  Status
                                </th>
                                <th className="text-center py-3 px-4 font-semibold text-gray-700">
                                  CVEs
                                </th>
                                <th className="text-left py-3 px-4 font-semibold text-gray-700">
                                  Details
                                </th>
                                <th className="text-center py-3 px-4 font-semibold text-gray-700">
                                  Advisory
                                </th>
                              </tr>
                            </thead>
                            <tbody className="divide-y divide-gray-200">
                              {model.versions.map((version, idx) => (
                                <tr
                                  key={idx}
                                  className={`${
                                    version.is_safe ? 'bg-white' : 'bg-red-50'
                                  } hover:bg-opacity-80 transition`}
                                >
                                  <td className="py-3 px-4 font-mono text-gray-900 font-semibold">
                                    {version.version}
                                  </td>
                                  <td className="py-3 px-4 text-gray-700">
                                    {new Date(version.release_date).toLocaleDateString('en-US', {
                                      year: 'numeric',
                                      month: 'short',
                                      day: 'numeric',
                                    })}
                                  </td>
                                  <td className="py-3 px-4 text-center">
                                    <span
                                      className={`inline-block px-3 py-1 rounded-full text-xs font-semibold border ${getSeverityColor(
                                        version.severity
                                      )}`}
                                    >
                                      {version.severity}
                                    </span>
                                  </td>
                                  <td className="py-3 px-4 text-center">
                                    {version.cve_count > 0 ? (
                                      <span className="inline-block bg-red-100 text-red-800 px-2 py-1 rounded text-xs font-bold">
                                        {version.cve_count}
                                      </span>
                                    ) : (
                                      <span className="text-gray-400">—</span>
                                    )}
                                  </td>
                                  <td className="py-3 px-4 text-gray-700 text-xs">
                                    <div>{version.status}</div>
                                    {version.cves.length > 0 && (
                                      <div className="mt-1 text-gray-600 font-mono">
                                        {version.cves.slice(0, 2).join(', ')}
                                        {version.cves.length > 2 && ` +${version.cves.length - 2}`}
                                      </div>
                                    )}
                                  </td>
                                  <td className="py-3 px-4 text-center">
                                    <a
                                      href={version.advisory_url}
                                      target="_blank"
                                      rel="noopener noreferrer"
                                      className="text-blue-600 hover:text-blue-800 font-semibold underline"
                                    >
                                      Link ↗
                                    </a>
                                  </td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
      </div>

      {/* Legend */}
      <div className="mt-8 p-4 bg-gray-50 rounded-lg border border-gray-200">
        <h3 className="font-semibold text-gray-900 mb-3">Legend</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 bg-red-200 rounded border border-red-300"></span>
            <span className="text-gray-700">CRITICAL - Action Required</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 bg-orange-200 rounded border border-orange-300"></span>
            <span className="text-gray-700">HIGH - Plan Upgrade</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 bg-yellow-200 rounded border border-yellow-300"></span>
            <span className="text-gray-700">MEDIUM - Monitor</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="inline-block w-4 h-4 bg-green-200 rounded border border-green-300"></span>
            <span className="text-gray-700">SAFE - No CVEs</span>
          </div>
        </div>
      </div>
    </div>
  );
}
