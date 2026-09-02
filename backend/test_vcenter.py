from app.normalizer import normalize_version

test_versions = [
    "7.0 U3p",
    "8.0",
    "8.0.0",
    "8.0 U1c",
    "8.0 U2",
    "8.0 U2b",
    "8.0 U2d",
    "8.0.3",
    "8.0 U3a",
]

print(f"{'RAW VCENTER VERSION':<20} | {'NORMALIZED (SORTABLE) INTERNAL STRING'}")
print("-" * 65)

for v in test_versions:
    norm = normalize_version("vmware", v)
    print(f"{v:<20} | '{norm}'")

print("\n--- Boolean Comparison Verifications ---")
comparisons = [
    ("8.0 U3a", ">", "8.0 U2d"),
    ("8.0 U2d", ">", "8.0 U2b"),
    ("8.0 U2b", ">", "8.0 U2"),
    ("8.0 U2",  ">", "8.0 U1c"),
    ("8.0 U1c", ">", "8.0"),
    ("8.0",     ">", "7.0 U3p"),
]

for left, op, right in comparisons:
    left_norm = normalize_version("vmware", left)
    right_norm = normalize_version("vmware", right)
    result = left_norm > right_norm
    print(f"Is '{left}' strictly greater than '{right}'? --> {result}")

