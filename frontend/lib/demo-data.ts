import type { Patch, PatchListResponse, VendorStatus } from "./api";

const DEMO_VENDORS: VendorStatus[] = [
  { id: "dell", display_name: "Dell EMC", status: "OK", last_success_at: new Date().toISOString(), consecutive_failures: 0 },
  { id: "cisco", display_name: "Cisco", status: "OK", last_success_at: new Date(Date.now() - 3600000).toISOString(), consecutive_failures: 0 },
  { id: "netscaler", display_name: "NetScaler", status: "DEGRADED", last_success_at: new Date(Date.now() - 86400000).toISOString(), consecutive_failures: 3 },
  { id: "hpe", display_name: "HPE", status: "OK", last_success_at: new Date(Date.now() - 7200000).toISOString(), consecutive_failures: 0 },
];

const DEMO_PATCHES: Patch[] = [
  {
    vendor: "cisco",
    model: "Catalyst 9300",
    component_type: "IOS-XE",
    version: "17.12.03",
    release_date: "2026-06-15",
    severity: "CRITICAL",
    cves: ["CVE-2026-20150", "CVE-2026-20151"],
    advisory_url: "https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-iosxe-vuln-2026",
    download_url: "https://software.cisco.com/download/home",
    requires_entitlement: true,
    is_latest: true,
    is_recommended: true,
  },
  {
    vendor: "dell",
    model: "PowerEdge R750",
    component_type: "BIOS",
    version: "1.14.2",
    release_date: "2026-05-10",
    severity: "HIGH",
    cves: ["CVE-2026-1070"],
    advisory_url: "https://www.dell.com/support/security",
    download_url: "https://www.dell.com/support/home/drivers",
    requires_entitlement: false,
    is_latest: true,
    is_recommended: true,
  },
  {
    vendor: "netscaler",
    model: "NetScaler ADC",
    component_type: "Firmware",
    version: "14.1-34.42",
    release_date: "2026-04-20",
    severity: "CRITICAL",
    cves: ["CVE-2026-4432"],
    advisory_url: "https://support.citrix.com/article/CTX123456",
    download_url: null,
    requires_entitlement: false,
    is_latest: true,
    is_recommended: false,
  },
  {
    vendor: "hpe",
    model: "ProLiant DL380 Gen11",
    component_type: "iLO 6",
    version: "1.62",
    release_date: "2026-05-01",
    severity: "MEDIUM",
    cves: [],
    advisory_url: "https://support.hpe.com/hpesc/public/km/securityBulletins",
    download_url: null,
    requires_entitlement: false,
    is_latest: true,
    is_recommended: true,
  },
  {
    vendor: "dell",
    model: "PowerEdge R650",
    component_type: "iDRAC9",
    version: "7.00.00.00",
    release_date: "2026-03-15",
    severity: "LOW",
    cves: [],
    advisory_url: "https://www.dell.com/support/security",
    download_url: null,
    requires_entitlement: false,
    is_latest: true,
    is_recommended: false,
  },
];

export async function fetchDemoPatches(filters: Record<string, any>): Promise<PatchListResponse> {
  // Simulate network delay
  await new Promise((resolve) => setTimeout(resolve, 600));

  let filtered = [...DEMO_PATCHES];
  
  if (filters.vendor) {
    filtered = filtered.filter(p => p.vendor === filters.vendor);
  }
  if (filters.severity) {
    filtered = filtered.filter(p => p.severity === filters.severity);
  }
  if (filters.model) {
    const search = filters.model.toLowerCase();
    filtered = filtered.filter(p => p.model.toLowerCase().includes(search) || p.component_type.toLowerCase().includes(search));
  }

  const offset = Number(filters.offset) || 0;
  const limit = Number(filters.limit) || 50;

  return {
    count: filtered.length,
    total: filtered.length,
    limit,
    offset,
    results: filtered.slice(offset, offset + limit),
  };
}

export async function fetchDemoVendorStatus(): Promise<VendorStatus[]> {
  await new Promise((resolve) => setTimeout(resolve, 400));
  return DEMO_VENDORS;
}
