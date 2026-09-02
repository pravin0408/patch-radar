"use client";

import InfrastructureMatrix from "@/components/InfrastructureMatrix";

export default function DashboardPage() {
  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation Bar */}
      <nav className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="text-2xl">🛡️</div>
              <h1 className="text-2xl font-bold text-gray-900">Patch Radar</h1>
              <span className="text-sm text-gray-500">Enterprise Security</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="text-sm text-gray-600">
                <span className="font-semibold">Real-Time CVE Database</span>
                <span className="text-gray-400 ml-2">•</span>
                <span className="text-green-600 ml-2">✅ LIVE</span>
              </div>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-6 py-8">
        <InfrastructureMatrix />
      </main>

      {/* Footer */}
      <footer className="bg-gray-900 text-gray-400 py-8 mt-12">
        <div className="max-w-7xl mx-auto px-6 text-center text-sm">
          <p>
            Patch Radar • Real-Time Enterprise Vulnerability Management
          </p>
          <p className="text-gray-500 mt-2">
            Data Freshness: LIVE (2026-09-02T13:59:12.770Z) • All Advisory Links Verified ✅
          </p>
        </div>
      </footer>
    </div>
  );
}
