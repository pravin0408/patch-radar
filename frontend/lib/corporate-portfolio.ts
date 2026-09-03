/**
 * Corporate Asset Portfolio Matrix
 * Real-time vulnerability tracking with CSV export
 * 2026-09-03T18:15:18.632Z
 */

import { Patch, VendorStatus } from "./api";

export interface CorporateAsset {
  asset_id: string;
  asset_name: string;
  vendor: string;
  product: string;
  model: string;
  current_version: string;
  latest_safe_version: string;
  is_vulnerable: boolean;
  cve_count: number;
  severity_level: "CRITICAL" | "HIGH" | "MEDIUM" | "LOW" | "SAFE";
  cves: string[];
  business_unit: string;
  deployment_location: string;
  owner: string;
  last_updated: string;
  status: "OK" | "VULNERABLE" | "DEGRADED" | "END_OF_LIFE";
}

export interface PortfolioSummary {
  total_assets: number;
  total_critical_vulnerabilities: number;
  total_high_vulnerabilities: number;
  total_safe_assets: number;
  compliance_score: number;
  last_scan_time: string;
}

// Sample Corporate Asset Portfolio
export const CORPORATE_ASSETS: CorporateAsset[] = [
  // VMware Assets
  {
    asset_id: "ASSET-VM-001",
    asset_name: "Production vCenter Server",
    vendor: "VMware",
    product: "vCenter Server",
    model: "vCenter Server",
    current_version: "8.0.2",
    latest_safe_version: "8.0.3",
    is_vulnerable: true,
    cve_count: 1,
    severity_level: "CRITICAL",
    cves: ["CVE-2026-35847"],
    business_unit: "Infrastructure",
    deployment_location: "Data Center A",
    owner: "John Smith",
    last_updated: "2026-09-03T18:00:00Z",
    status: "VULNERABLE"
  },
  {
    asset_id: "ASSET-VM-002",
    asset_name: "DR vCenter Server",
    vendor: "VMware",
    product: "vCenter Server",
    model: "vCenter Server",
    current_version: "8.0.3",
    latest_safe_version: "8.0.3",
    is_vulnerable: false,
    cve_count: 0,
    severity_level: "SAFE",
    cves: [],
    business_unit: "Infrastructure",
    deployment_location: "Data Center B",
    owner: "John Smith",
    last_updated: "2026-09-03T18:00:00Z",
    status: "OK"
  },
  {
    asset_id: "ASSET-ESX-001",
    asset_name: "ESXi Cluster Node 1",
    vendor: "VMware",
    product: "ESXi",
    model: "ESXi Hypervisor",
    current_version: "8.0.1",
    latest_safe_version: "8.0.2",
    is_vulnerable: true,
    cve_count: 1,
    severity_level: "HIGH",
    cves: ["CVE-2026-34562"],
    business_unit: "Infrastructure",
    deployment_location: "Data Center A",
    owner: "Jane Doe",
    last_updated: "2026-09-03T18:00:00Z",
    status: "VULNERABLE"
  },
  
  // Cisco Assets
  {
    asset_id: "ASSET-CISCO-001",
    asset_name: "Core Router 1",
    vendor: "Cisco",
    product: "IOS-XE",
    model: "Catalyst 9300",
    current_version: "17.12.03",
    latest_safe_version: "17.12.04",
    is_vulnerable: true,
    cve_count: 1,
    severity_level: "CRITICAL",
    cves: ["CVE-2026-44782"],
    business_unit: "Network Engineering",
    deployment_location: "Data Center A",
    owner: "Bob Johnson",
    last_updated: "2026-09-03T18:00:00Z",
    status: "VULNERABLE"
  },
  {
    asset_id: "ASSET-CISCO-002",
    asset_name: "Distribution Switch 1",
    vendor: "Cisco",
    product: "IOS-XE",
    model: "Catalyst 9400",
    current_version: "17.12.04",
    latest_safe_version: "17.12.04",
    is_vulnerable: false,
    cve_count: 0,
    severity_level: "SAFE",
    cves: [],
    business_unit: "Network Engineering",
    deployment_location: "Data Center B",
    owner: "Bob Johnson",
    last_updated: "2026-09-03T18:00:00Z",
    status: "OK"
  },

  // Palo Alto Assets
  {
    asset_id: "ASSET-PA-001",
    asset_name: "Primary Firewall",
    vendor: "Palo Alto",
    product: "PAN-OS",
    model: "PA-5220",
    current_version: "11.2.2",
    latest_safe_version: "11.2.3",
    is_vulnerable: true,
    cve_count: 1,
    severity_level: "CRITICAL",
    cves: ["CVE-2026-38421"],
    business_unit: "Security Operations",
    deployment_location: "Data Center A",
    owner: "Alice Williams",
    last_updated: "2026-09-03T18:00:00Z",
    status: "VULNERABLE"
  },
  {
    asset_id: "ASSET-PA-002",
    asset_name: "Secondary Firewall",
    vendor: "Palo Alto",
    product: "PAN-OS",
    model: "PA-5220",
    current_version: "11.2.3",
    latest_safe_version: "11.2.3",
    is_vulnerable: false,
    cve_count: 0,
    severity_level: "SAFE",
    cves: [],
    business_unit: "Security Operations",
    deployment_location: "Data Center B",
    owner: "Alice Williams",
    last_updated: "2026-09-03T18:00:00Z",
    status: "OK"
  },

  // NetScaler Assets
  {
    asset_id: "ASSET-NS-001",
    asset_name: "Load Balancer Primary",
    vendor: "NetScaler",
    product: "NetScaler ADC",
    model: "VPX 5000",
    current_version: "14.1.28.40",
    latest_safe_version: "14.1.28.50",
    is_vulnerable: true,
    cve_count: 1,
    severity_level: "CRITICAL",
    cves: ["CVE-2026-40123"],
    business_unit: "Application Delivery",
    deployment_location: "Data Center A",
    owner: "Charlie Brown",
    last_updated: "2026-09-03T18:00:00Z",
    status: "VULNERABLE"
  },

  // F5 Assets
  {
    asset_id: "ASSET-F5-001",
    asset_name: "BIG-IP Load Balancer",
    vendor: "F5",
    product: "BIG-IP",
    model: "BIG-IP 5000s",
    current_version: "17.1.2.0",
    latest_safe_version: "17.1.2.1",
    is_vulnerable: true,
    cve_count: 1,
    severity_level: "HIGH",
    cves: ["CVE-2026-43892"],
    business_unit: "Application Delivery",
    deployment_location: "Data Center B",
    owner: "David Miller",
    last_updated: "2026-09-03T18:00:00Z",
    status: "VULNERABLE"
  },

  // Dell Assets
  {
    asset_id: "ASSET-DELL-001",
    asset_name: "PowerEdge R750 Server 1",
    vendor: "Dell",
    product: "iDRAC9",
    model: "PowerEdge R750",
    current_version: "7.10.39.00",
    latest_safe_version: "7.10.40.00",
    is_vulnerable: true,
    cve_count: 1,
    severity_level: "MEDIUM",
    cves: ["CVE-2026-42187"],
    business_unit: "Infrastructure",
    deployment_location: "Data Center A",
    owner: "Eve Garcia",
    last_updated: "2026-09-03T18:00:00Z",
    status: "VULNERABLE"
  },
  {
    asset_id: "ASSET-DELL-002",
    asset_name: "PowerEdge R750 Server 2",
    vendor: "Dell",
    product: "iDRAC9",
    model: "PowerEdge R750",
    current_version: "7.10.40.00",
    latest_safe_version: "7.10.40.00",
    is_vulnerable: false,
    cve_count: 0,
    severity_level: "SAFE",
    cves: [],
    business_unit: "Infrastructure",
    deployment_location: "Data Center A",
    owner: "Eve Garcia",
    last_updated: "2026-09-03T18:00:00Z",
    status: "OK"
  },

  // HPE Assets
  {
    asset_id: "ASSET-HPE-001",
    asset_name: "ProLiant DL380 Gen11",
    vendor: "HPE",
    product: "iLO 5",
    model: "ProLiant DL380",
    current_version: "2.79.00",
    latest_safe_version: "2.80.00",
    is_vulnerable: true,
    cve_count: 1,
    severity_level: "MEDIUM",
    cves: ["CVE-2026-41098"],
    business_unit: "Infrastructure",
    deployment_location: "Data Center B",
    owner: "Frank Martinez",
    last_updated: "2026-09-03T18:00:00Z",
    status: "VULNERABLE"
  },
];

export function getPortfolioSummary(): PortfolioSummary {
  const total_assets = CORPORATE_ASSETS.length;
  const total_critical = CORPORATE_ASSETS.filter(a => a.severity_level === "CRITICAL").length;
  const total_high = CORPORATE_ASSETS.filter(a => a.severity_level === "HIGH").length;
  const total_safe = CORPORATE_ASSETS.filter(a => a.severity_level === "SAFE").length;
  const total_vulnerable = CORPORATE_ASSETS.filter(a => a.is_vulnerable).length;
  
  const compliance_score = (total_safe / total_assets) * 100;

  return {
    total_assets,
    total_critical_vulnerabilities: total_critical,
    total_high_vulnerabilities: total_high,
    total_safe_assets: total_safe,
    compliance_score,
    last_scan_time: new Date().toISOString()
  };
}

export function generateCSVData(): string {
  const headers = [
    "Asset ID",
    "Asset Name",
    "Vendor",
    "Product",
    "Current Version",
    "Latest Safe Version",
    "Vulnerable",
    "CVE Count",
    "Severity",
    "CVEs",
    "Business Unit",
    "Location",
    "Owner",
    "Status",
    "Last Updated"
  ];

  const rows = CORPORATE_ASSETS.map(asset => [
    asset.asset_id,
    asset.asset_name,
    asset.vendor,
    asset.product,
    asset.current_version,
    asset.latest_safe_version,
    asset.is_vulnerable ? "YES" : "NO",
    asset.cve_count,
    asset.severity_level,
    asset.cves.join("; "),
    asset.business_unit,
    asset.deployment_location,
    asset.owner,
    asset.status,
    asset.last_updated
  ]);

  const csv = [
    headers.join(","),
    ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(","))
  ].join("\n");

  return csv;
}

export function generateCVETrackerCSV(): string {
  const headers = [
    "CVE ID",
    "Asset ID",
    "Asset Name",
    "Vendor",
    "Product",
    "Current Version",
    "Recommended Version",
    "Severity",
    "Business Unit",
    "Owner",
    "Detection Date",
    "Status"
  ];

  const rows: string[][] = [];
  
  CORPORATE_ASSETS.forEach(asset => {
    if (asset.cves.length > 0) {
      asset.cves.forEach(cve => {
        rows.push([
          cve,
          asset.asset_id,
          asset.asset_name,
          asset.vendor,
          asset.product,
          asset.current_version,
          asset.latest_safe_version,
          asset.severity_level,
          asset.business_unit,
          asset.owner,
          asset.last_updated,
          asset.status
        ]);
      });
    }
  });

  const csv = [
    headers.join(","),
    ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(","))
  ].join("\n");

  return csv;
}

export function getAssetsByBusinessUnit(): Record<string, CorporateAsset[]> {
  const grouped: Record<string, CorporateAsset[]> = {};
  
  CORPORATE_ASSETS.forEach(asset => {
    if (!grouped[asset.business_unit]) {
      grouped[asset.business_unit] = [];
    }
    grouped[asset.business_unit].push(asset);
  });

  return grouped;
}

export function getAssetsBySeverity(): Record<string, CorporateAsset[]> {
  const grouped: Record<string, CorporateAsset[]> = {};
  
  CORPORATE_ASSETS.forEach(asset => {
    if (!grouped[asset.severity_level]) {
      grouped[asset.severity_level] = [];
    }
    grouped[asset.severity_level].push(asset);
  });

  return grouped;
}

export function getVulnerableAssets(): CorporateAsset[] {
  return CORPORATE_ASSETS.filter(a => a.is_vulnerable).sort((a, b) => {
    const severityOrder = { "CRITICAL": 0, "HIGH": 1, "MEDIUM": 2, "LOW": 3, "SAFE": 4 };
    return severityOrder[a.severity_level] - severityOrder[b.severity_level];
  });
}
