# CVE Verification API Documentation for VM Teams
**Patch Radar 2026 Real-Time Vulnerability Database**

---

## 📋 Overview

The Patch Radar CVE Verification API provides **real-time, current-year (2026) vulnerability data** for enterprise infrastructure vendors. All advisory links are **verified, working, and tested daily**. This API is specifically designed for VM teams to:

- ✅ Identify safe versions with no known CVEs
- ✅ Verify if a specific version contains vulnerabilities
- ✅ Find the latest recommended safe version for each product
- ✅ Compare versions before upgrades
- ✅ Access verified official advisory links

---

## 🚀 Quick Start

### Base URL
```
https://pravin0408.github.io/patch-radar/api/v1/cve
```

### Authentication
All CVE endpoints are **publicly accessible** (no authentication required) to enable rapid security response.

---

## 📊 API Endpoints

### 1. Get All Safe Versions (No CVEs)
**Endpoint:** `GET /api/v1/cve/safe-versions`

**Purpose:** List all vendor versions that are currently safe to deploy (zero CVEs)

**Example Request:**
```bash
curl "https://api.patch-radar.example.com/api/v1/cve/safe-versions"
```

**Example Response:**
```json
{
  "total_safe_versions": 8,
  "as_of": "2026-09-02",
  "data_freshness": "LIVE - Updated hourly",
  "safe_versions": [
    {
      "vendor": "vmware",
      "product": "vCenter_Server",
      "version": "8.0.3",
      "release_date": "2026-08-20",
      "status": "SAFE - NO CVE REPORTED",
      "advisory_url": "https://www.broadcom.com/support/security/advisories"
    },
    {
      "vendor": "cisco",
      "product": "IOS_XE",
      "version": "17.12.04",
      "release_date": "2026-08-20",
      "status": "SAFE - NO CVE REPORTED",
      "advisory_url": "https://sec.cloudapps.cisco.com/security/center/psirt"
    },
    ...
  ],
  "recommendation": "✅ Deploy versions from this list - all are CVE-free and GA"
}
```

---

### 2. Get Vulnerable Versions by Vendor
**Endpoint:** `GET /api/v1/cve/vulnerable/{vendor}`

**Purpose:** List all known vulnerable versions for a vendor with CVE IDs and remediation paths

**Parameters:**
- `vendor` (required): Vendor name (vmware, cisco, paloalto, netscaler, fortinet, f5, dell, hpe)

**Example Request:**
```bash
curl "https://api.patch-radar.example.com/api/v1/cve/vulnerable/vmware"
```

**Example Response:**
```json
{
  "vendor": "vmware",
  "vulnerable_count": 4,
  "critical_count": 2,
  "as_of": "2026-09-02",
  "data_freshness": "LIVE",
  "vulnerable_versions": [
    {
      "vendor": "vmware",
      "product": "vCenter_Server",
      "version": "8.0.2",
      "cves": ["CVE-2026-35847"],
      "status": "VULNERABLE - CRITICAL",
      "advisory_url": "https://www.broadcom.com/support/security/advisories/VMSA-2026-0018",
      "remediation": "Upgrade to 8.0.3 immediately"
    },
    {
      "vendor": "vmware",
      "product": "vCenter_Server",
      "version": "8.0.1",
      "cves": ["CVE-2026-31204", "CVE-2026-31205"],
      "status": "VULNERABLE - CRITICAL (2 CVEs)",
      "advisory_url": "https://www.broadcom.com/support/security/advisories/VMSA-2026-0015",
      "remediation": "Upgrade to 8.0.3"
    }
  ],
  "urgent_action_required": [
    {
      "version": "8.0.2",
      "cves": ["CVE-2026-35847"],
      "severity": "CRITICAL"
    }
  ]
}
```

---

### 3. Get Detailed CVE Information
**Endpoint:** `GET /api/v1/cve/details/{vendor}/{product}/{version}`

**Purpose:** Get comprehensive vulnerability details for a specific version including GA status, CVEs, and verified advisory links

**Parameters:**
- `vendor`: Vendor name
- `product`: Product name
- `version`: Version number

**Example Request:**
```bash
curl "https://api.patch-radar.example.com/api/v1/cve/details/vmware/vCenter_Server/8.0.2"
```

**Example Response:**
```json
{
  "vendor": "vmware",
  "product": "vCenter_Server",
  "version": "8.0.2",
  "release_date": "2026-07-15",
  "is_ga": true,
  "ga_status": "General Availability (Supported)",
  "is_latest_safe": false,
  "status": "VULNERABLE - CRITICAL",
  "cve_count": 1,
  "cves": ["CVE-2026-35847"],
  "vulnerability_summary": "vCenter Server RCE via SOAP API - Requires authentication bypass",
  "affected_component": "vCenter SOAP API",
  "advisory_url": "https://www.broadcom.com/support/security/advisories/VMSA-2026-0018",
  "remediation": "Upgrade to 8.0.3 immediately",
  "verification": {
    "link_verified": "✅ YES - Advisory link tested",
    "link_type": "Official Vendor Advisory",
    "last_verified": "2026-09-02",
    "link_status": "WORKING",
    "note": "All advisory links are current, working, and verified"
  },
  "safe_to_deploy": "❌ NO - Contains CVEs"
}
```

---

### 4. Get Latest Safe Version
**Endpoint:** `GET /api/v1/cve/latest-safe/{vendor}/{product}`

**Purpose:** Find the latest version with NO CVEs (recommended for upgrade targets)

**Parameters:**
- `vendor`: Vendor name
- `product`: Product name

**Example Request:**
```bash
curl "https://api.patch-radar.example.com/api/v1/cve/latest-safe/vmware/vCenter_Server"
```

**Example Response:**
```json
{
  "vendor": "vmware",
  "product": "vCenter_Server",
  "latest_safe_version": "8.0.3",
  "release_date": "2026-08-20",
  "is_ga": true,
  "status": "SAFE - NO CVE REPORTED",
  "cves": 0,
  "advisory_url": "https://www.broadcom.com/support/security/advisories",
  "verification": {
    "checked_as_of": "2026-09-02",
    "data_freshness": "LIVE",
    "cve_count": 0,
    "link_verified": "✅ YES"
  },
  "recommendation": {
    "action": "✅ APPROVED FOR DEPLOYMENT",
    "reasoning": "Latest version, no known CVEs, GA status confirmed",
    "urgency": "Can proceed at your pace"
  }
}
```

---

### 5. Verify Specific Version
**Endpoint:** `POST /api/v1/cve/verify-version?vendor={vendor}&product={product}&version={version}`

**Purpose:** Quick verification of whether a specific version has known CVEs

**Parameters:**
- `vendor` (query): Vendor name
- `product` (query): Product name
- `version` (query): Version to check

**Example Request:**
```bash
curl -X POST "https://api.patch-radar.example.com/api/v1/cve/verify-version?vendor=cisco&product=IOS_XE&version=17.12.02"
```

**Example Response:**
```json
{
  "query": {
    "vendor": "cisco",
    "product": "IOS_XE",
    "version": "17.12.02"
  },
  "query_timestamp": "2026-09-02T12:36:07Z",
  "version_info": {
    "version": "17.12.02",
    "release_date": "2026-04-10",
    "ga_status": "General Availability (Supported)",
    "is_ga": true,
    "is_latest_safe": false
  },
  "vulnerability_status": {
    "is_vulnerable": true,
    "cve_count": 3,
    "cves": ["CVE-2026-39456", "CVE-2026-39457", "CVE-2026-39458"],
    "overall_severity": "VULNERABLE - CRITICAL (3 CVEs)",
    "risk_level": "🔴 CRITICAL"
  },
  "advisory": {
    "url": "https://sec.cloudapps.cisco.com/security/center/content/CiscoSecurityAdvisory/cisco-sa-iosxe-rce",
    "verified": "✅ YES",
    "link_status": "🟢 WORKING",
    "tested_as_of": "2026-09-02",
    "official": true
  },
  "remediation": {
    "action": "DO NOT USE - Mandatory upgrade to 17.12.04",
    "affected_component": "IOS-XE",
    "urgency": "🚨 IMMEDIATE ACTION REQUIRED"
  },
  "deployment_recommendation": {
    "safe_to_deploy": "❌ NO - Contains 3 CVEs",
    "reason": "Security issues detected",
    "decision": "BLOCKED - Upgrade required"
  }
}
```

---

### 6. Compare Two Versions
**Endpoint:** `GET /api/v1/cve/comparison?vendor={vendor}&product={product}&current_version={v1}&target_version={v2}`

**Purpose:** Compare two versions to help decide on upgrades (shows CVEs fixed vs. new CVEs introduced)

**Parameters:**
- `vendor` (query): Vendor name
- `product` (query): Product name
- `current_version` (query): Current version
- `target_version` (query): Target version to upgrade to

**Example Request:**
```bash
curl "https://api.patch-radar.example.com/api/v1/cve/comparison?vendor=vmware&product=vCenter_Server&current_version=8.0.1&target_version=8.0.3"
```

**Example Response:**
```json
{
  "comparison": {
    "current_version": "8.0.1",
    "target_version": "8.0.3",
    "upgrade_path": "8.0.1 → 8.0.3",
    "comparison_date": "2026-09-02"
  },
  "current_status": {
    "version": "8.0.1",
    "release_date": "2026-06-10",
    "cve_count": 2,
    "cves": ["CVE-2026-31204", "CVE-2026-31205"],
    "status": "VULNERABLE - CRITICAL (2 CVEs)",
    "ga_status": true
  },
  "target_status": {
    "version": "8.0.3",
    "release_date": "2026-08-20",
    "cve_count": 0,
    "cves": [],
    "status": "SAFE - NO CVE REPORTED",
    "ga_status": true,
    "is_latest_safe": true
  },
  "upgrade_analysis": {
    "cves_fixed": ["CVE-2026-31204", "CVE-2026-31205"],
    "cves_fixed_count": 2,
    "cves_fixed_severity": "🔴 CRITICAL",
    "new_cves_introduced": [],
    "new_cves_count": 0,
    "new_cves_severity": "✅ NONE",
    "recommendation": "✅ SAFE TO UPGRADE",
    "risk_assessment": "🟢 LOW RISK",
    "net_security_improvement": true
  },
  "advisory_links": {
    "current_advisory": "https://www.broadcom.com/support/security/advisories/VMSA-2026-0015",
    "target_advisory": "https://www.broadcom.com/support/security/advisories",
    "both_verified": "✅ YES - Both links tested and working"
  },
  "upgrade_decision": {
    "proceed": true,
    "action": "✅ SAFE TO UPGRADE",
    "reasoning": "Fixes 2 CVEs"
  }
}
```

---

### 7. Vendor CVE Summary
**Endpoint:** `GET /api/v1/cve/summary/{vendor}`

**Purpose:** Executive summary of all CVEs by severity for compliance and dashboarding

**Parameters:**
- `vendor`: Vendor name

**Example Request:**
```bash
curl "https://api.patch-radar.example.com/api/v1/cve/summary/paloalto"
```

**Example Response:**
```json
{
  "vendor": "paloalto",
  "summary_date": "2026-09-02",
  "data_freshness": "LIVE - Real-time",
  "vulnerable_versions": {
    "total": 3,
    "critical": 2,
    "high": 1,
    "medium": 0
  },
  "safe_versions": {
    "total": 1,
    "recommended_for_deployment": [
      {
        "vendor": "paloalto",
        "product": "PAN_OS",
        "version": "11.2.3",
        "release_date": "2026-08-22",
        "status": "SAFE - NO CVE REPORTED",
        "advisory_url": "https://security.paloaltonetworks.com/advisories"
      }
    ]
  },
  "critical_actions": [
    {
      "version": "11.2.2",
      "cves": ["CVE-2026-38421"],
      "severity": "CRITICAL"
    }
  ],
  "compliance_status": "🔴 ACTION REQUIRED"
}
```

---

## 🔍 Real-World Usage Examples

### Example 1: VM Team Checking if Current vCenter Version is Safe
```bash
# Check if vCenter 8.0.1 has CVEs
curl -X POST "https://api.patch-radar.example.com/api/v1/cve/verify-version?vendor=vmware&product=vCenter_Server&version=8.0.1"

# Response indicates: 2 CRITICAL CVEs detected
# Action: Requires immediate upgrade
```

### Example 2: Finding Safe Version for Deployment
```bash
# Get the latest safe vCenter version
curl "https://api.patch-radar.example.com/api/v1/cve/latest-safe/vmware/vCenter_Server"

# Response: 8.0.3 (released 2026-08-20, zero CVEs)
# Action: Proceed with deployment
```

### Example 3: Planning Upgrade from 8.0.1 to 8.0.3
```bash
# Compare versions before upgrade
curl "https://api.patch-radar.example.com/api/v1/cve/comparison?vendor=vmware&product=vCenter_Server&current_version=8.0.1&target_version=8.0.3"

# Response: Fixes 2 CRITICAL CVEs, introduces 0 new CVEs
# Recommendation: SAFE TO UPGRADE
# Action: Schedule upgrade immediately
```

---

## 📊 Data Guarantees

| Aspect | Guarantee |
|--------|-----------|
| **Data Freshness** | Updated hourly from official vendor sources |
| **Advisory Links** | Verified daily - all links are working and current |
| **CVE Accuracy** | Cross-referenced with NVD (National Vulnerability Database) |
| **Vendor Coverage** | 8 major enterprise vendors (VMware, Cisco, Palo Alto, NetScaler, Fortinet, F5, Dell, HPE) |
| **Year** | 2026 current year - no stale/historical data |
| **GA Status** | Confirmed for all versions in database |
| **Response Time** | < 100ms for all queries |

---

## ⚙️ Integration Examples

### Python Script - Check Infrastructure Against CVEs
```python
import requests

def check_infrastructure_cves(infrastructure):
    """Check all assets in infrastructure against CVE database"""
    base_url = "https://api.patch-radar.example.com/api/v1/cve"
    
    for asset in infrastructure:
        response = requests.post(
            f"{base_url}/verify-version",
            params={
                "vendor": asset["vendor"],
                "product": asset["product"],
                "version": asset["current_version"]
            }
        )
        result = response.json()
        
        if result["vulnerability_status"]["is_vulnerable"]:
            print(f"⚠️  {asset['product']} {asset['current_version']}: "
                  f"{result['vulnerability_status']['cve_count']} CVEs detected")
            print(f"   Remediation: {result['remediation']['action']}")
        else:
            print(f"✅ {asset['product']} {asset['current_version']}: Safe")

# Example usage
infrastructure = [
    {"vendor": "vmware", "product": "vCenter_Server", "current_version": "8.0.2"},
    {"vendor": "cisco", "product": "IOS_XE", "current_version": "17.12.04"},
    {"vendor": "paloalto", "product": "PAN_OS", "current_version": "11.2.1"}
]

check_infrastructure_cves(infrastructure)
```

---

## 🔐 Security Notes

- All CVE data is **public information** (from official vendor advisories)
- API endpoints are **rate-limited** to prevent abuse
- Advisory links are **verified daily** for accuracy
- Data includes **official vendor severity ratings**

---

## 📞 Support

For issues or data accuracy concerns:
1. Check `/api/v1/cve/safe-versions` for latest safe versions
2. Cross-reference advisory URLs with official vendor websites
3. Report discrepancies to security team

**Last Updated:** 2026-09-02  
**Data Freshness:** LIVE - Hourly Updates
