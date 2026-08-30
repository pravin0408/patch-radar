import type { Patch, PatchListResponse, VendorStatus } from "./api";

const DEMO_VENDORS: VendorStatus[] = [
  { id: "dell", display_name: "Dell EMC", status: "OK", last_success_at: new Date().toISOString(), consecutive_failures: 0 },
  { id: "cisco", display_name: "Cisco", status: "OK", last_success_at: new Date(Date.now() - 3600000).toISOString(), consecutive_failures: 0 },
  { id: "netscaler", display_name: "NetScaler", status: "OK", last_success_at: new Date(Date.now() - 3600000).toISOString(), consecutive_failures: 0 },
  { id: "hpe", display_name: "HPE", status: "OK", last_success_at: new Date(Date.now() - 7200000).toISOString(), consecutive_failures: 0 },
  { id: "vmware", display_name: "VMware", status: "OK", last_success_at: new Date(Date.now() - 1000000).toISOString(), consecutive_failures: 0 },
  { id: "paloalto", display_name: "Palo Alto Networks", status: "OK", last_success_at: new Date(Date.now() - 2000000).toISOString(), consecutive_failures: 0 },
  { id: "fortinet", display_name: "Fortinet", status: "OK", last_success_at: new Date(Date.now() - 1500000).toISOString(), consecutive_failures: 0 },
  { id: "f5", display_name: "F5 Networks", status: "OK", last_success_at: new Date(Date.now() - 5000000).toISOString(), consecutive_failures: 0 },
];

const DEMO_PATCHES: Patch[] = [
  {
    vendor: "paloalto",
    model: "PAN-OS GlobalProtect",
    component_type: "Firewall OS",
    version: "11.1.2-h3",
    release_date: "2024-04-12",
    severity: "CRITICAL",
    cves: ["CVE-2024-3400"],
    advisory_url: "https://security.paloaltonetworks.com/CVE-2024-3400",
    download_url: "https://support.paloaltonetworks.com/",
    requires_entitlement: true,
    is_latest: true,
    is_recommended: true,
  },
  {
    vendor: "cisco",
    model: "Catalyst and IOS XE",
    component_type: "Operating System",
    version: "17.12.2",
    release_date: "2023-10-16",
    severity: "CRITICAL",
    cves: ["CVE-2023-20198", "CVE-2023-20273"],
    advisory_url: "https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-iosxe-webui-privesc-j22SaA4z",
    download_url: "https://software.cisco.com/download/home",
    requires_entitlement: true,
    is_latest: false,
    is_recommended: false,
  },
  {
    vendor: "netscaler",
    model: "NetScaler ADC",
    component_type: "Firmware",
    version: "14.1-8.50",
    release_date: "2023-10-10",
    severity: "CRITICAL",
    cves: ["CVE-2023-4966"],
    advisory_url: "https://support.citrix.com/s/article/CTX561482-citrix-netscaler-adc-and-netscaler-gateway-security-bulletin-for-cve20234966-and-cve20234967",
    download_url: null,
    requires_entitlement: false,
    is_latest: false,
    is_recommended: true,
  },
  {
    vendor: "vmware",
    model: "vCenter Server",
    component_type: "Management",
    version: "8.0 U2d",
    release_date: "2024-06-17",
    severity: "CRITICAL",
    cves: ["CVE-2024-37079", "CVE-2024-37080"],
    advisory_url: "https://support.broadcom.com/web/ecx/support-content-notification/-/external/content/SecurityAdvisories/0/24453",
    download_url: null,
    requires_entitlement: true,
    is_latest: true,
    is_recommended: true,
  },
  {
    vendor: "fortinet",
    model: "FortiOS",
    component_type: "Security OS",
    version: "7.4.3",
    release_date: "2024-02-08",
    severity: "CRITICAL",
    cves: ["CVE-2024-21762"],
    advisory_url: "https://www.fortiguard.com/psirt/FG-IR-24-015",
    download_url: null,
    requires_entitlement: true,
    is_latest: true,
    is_recommended: true,
  },
  {
    vendor: "f5",
    model: "BIG-IP",
    component_type: "ADC",
    version: "17.1.1.1",
    release_date: "2023-10-26",
    severity: "CRITICAL",
    cves: ["CVE-2023-46747"],
    advisory_url: "https://my.f5.com/manage/s/article/K000137353",
    download_url: "https://my.f5.com/manage/s/downloads",
    requires_entitlement: true,
    is_latest: false,
    is_recommended: true,
  },
  {
    vendor: "dell",
    model: "PowerEdge / iDRAC9",
    component_type: "Management",
    version: "7.00.00.00",
    release_date: "2023-09-08",
    severity: "HIGH",
    cves: ["CVE-2023-43093"],
    advisory_url: "https://www.dell.com/support/kbdoc/en-us/000216198/dsa-2023-264-dell-idrac9-security-update-for-ssl-tls-vulnerabilities",
    download_url: "https://www.dell.com/support/home/drivers",
    requires_entitlement: false,
    is_latest: true,
    is_recommended: true,
  },
  {
    vendor: "hpe",
    model: "ProLiant / iLO 5",
    component_type: "Management",
    version: "3.04",
    release_date: "2024-06-25",
    severity: "HIGH",
    cves: ["CVE-2024-28213"],
    advisory_url: "https://support.hpe.com/hpesc/public/docDisplay?docId=hpesbmu04664en_us&docLocale=en_US",
    download_url: null,
    requires_entitlement: false,
    is_latest: true,
    is_recommended: true,
  }
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
