import json, glob, os, hashlib

packages = []
skipped  = []

for path in sorted(glob.glob("packages/*/*/package.json")):
    with open(path, encoding="utf-8") as f:
        try:
            meta = json.load(f)
        except json.JSONDecodeError:
            print(f"ERROR: {path} no es JSON válido, ignorado")
            continue

    parts = path.replace("\\", "/").split("/")
    name, version = parts[1], parts[2]

    if meta.get("yanked", False):
        skipped.append(f"{name} {version} (yanked)")
        continue

    # Calcular size_bytes y sha256 del ZIP automáticamente
    zip_path = f"packages/{name}/{version}/{name}.zip"
    if os.path.exists(zip_path):
        with open(zip_path, "rb") as zf:
            data = zf.read()
            size_bytes = len(data)
            sha256 = hashlib.sha256(data).hexdigest()
    else:
        size_bytes = 0
        sha256 = ""

    packages.append({
        "name":              meta.get("name", name),
        "version":           meta.get("version", version),
        "author":            meta.get("author", ""),
        "date":              meta.get("date", ""),
        "description":       meta.get("description", ""),
        "keywords":          meta.get("keywords", []),
        "url":               f"packages/{name}/{version}/{name}.zip",
        "meta_url":          f"packages/{name}/{version}/package.json",
        "size_bytes":        size_bytes,
        "sha256":            sha256,
        "deprecated":        meta.get("deprecated", False),
        "deprecated_reason": meta.get("deprecated_reason", ""),
        "yanked":            False
    })

packages.sort(key=lambda x: x["date"], reverse=True)

with open("packages/index.json", "w", encoding="utf-8") as f:
    json.dump(packages, f, indent=2, ensure_ascii=False)

print(f"Index rebuilt: {len(packages)} packages")
if skipped:
    print(f"Skipped (yanked): {', '.join(skipped)}")
