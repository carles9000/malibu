import json, glob, os

packages = []

for path in sorted(glob.glob("packages/*/*/package.json")):
    with open(path, encoding="utf-8") as f:
        try:
            meta = json.load(f)
        except json.JSONDecodeError:
            print(f"ERROR: {path} no es JSON válido, ignorado")
            continue

    parts = path.replace("\\", "/").split("/")
    name, version = parts[1], parts[2]

    packages.append({
        "name":        meta.get("name", name),
        "version":     meta.get("version", version),
        "author":      meta.get("author", ""),
        "date":        meta.get("date", ""),
        "description": meta.get("description", ""),
        "keywords":    meta.get("keywords", []),
        "license":     meta.get("license", ""),
        "harbour_min": meta.get("harbour_min", ""),
        "url":         f"packages/{name}/{version}/{name}.zip",
        "meta_url":    f"packages/{name}/{version}/package.json",
        "size_bytes":  meta.get("size_bytes", 0),
        "sha256":      meta.get("sha256", "")
    })

packages.sort(key=lambda x: x["date"], reverse=True)

with open("packages/index.json", "w", encoding="utf-8") as f:
    json.dump(packages, f, indent=2, ensure_ascii=False)

print(f"Index rebuilt: {len(packages)} packages")
