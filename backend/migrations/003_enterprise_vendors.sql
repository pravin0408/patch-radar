-- Phase 3: Add additional enterprise infrastructure vendors

INSERT INTO vendors (id, display_name, advisory_portal_url) VALUES
    ('vmware', 'VMware (Broadcom)', 'https://www.vmware.com/security/advisories.html'),
    ('paloalto', 'Palo Alto Networks', 'https://security.paloaltonetworks.com/'),
    ('fortinet', 'Fortinet', 'https://www.fortiguard.com/psirt'),
    ('f5', 'F5 Networks', 'https://my.f5.com/manage/s/article/K4602')
ON CONFLICT (id) DO NOTHING;
