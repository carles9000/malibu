import json, glob, sys, re, os
from datetime import date

REQUIRED = ["name", "version", "description", "keywords"]
NAME_RE   = re.compile(r"^[a-z][a-z0-9-]+$")
VER_RE    = re.compile(r"^\d+\.\d+\.\d+$")
KW_RE     = re.compile(r"^[a-z][a-z0-9-]*$")

errors  = []
checked = 0

for path in sorted(glob.glob("packages/*/*/package.json")):
    parts = path.replace("\\", "/").split("/")
    name_dir, ver_dir = parts[1], parts[2]

    with open(path, encoding="utf-8") as f:
        try:
            meta = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{path}: JSON inválido — {e}")
            continue

    checked += 1

    # Campos obligatorios presentes y no vacíos
    for field in REQUIRED:
        if not meta.get(field):
            errors.append(f"{path}: campo obligatorio ausente o vacío: '{field}'")

    # name: formato lowercase con guiones
    name = meta.get("name", "")
    if name and not NAME_RE.match(name):
        errors.append(f"{path}: 'name' debe ser lowercase, solo letras, números y guiones (ej: hb-mysql). Valor: '{name}'")

    # name debe coincidir con el nombre del directorio
    if name and name != name_dir:
        errors.append(f"{path}: 'name' ('{name}') no coincide con el directorio ('{name_dir}')")

    # version: formato semver X.Y.Z
    version = meta.get("version", "")
    if version and not VER_RE.match(version):
        errors.append(f"{path}: 'version' debe seguir formato X.Y.Z (ej: 1.0.0). Valor: '{version}'")

    # version debe coincidir con el directorio
    if version and version != ver_dir:
        errors.append(f"{path}: 'version' ('{version}') no coincide con el directorio ('{ver_dir}')")

    # keywords: array de palabras lowercase
    keywords = meta.get("keywords", [])
    if not isinstance(keywords, list):
        errors.append(f"{path}: 'keywords' debe ser un array")
    elif len(keywords) == 0:
        errors.append(f"{path}: 'keywords' debe tener al menos una entrada")
    else:
        for kw in keywords:
            if not isinstance(kw, str):
                errors.append(f"{path}: keyword '{kw}' debe ser una cadena de texto")
            elif not KW_RE.match(kw):
                errors.append(f"{path}: keyword '{kw}' debe ser lowercase, solo letras, números y guiones, sin espacios")
            elif len(kw) > 30:
                errors.append(f"{path}: keyword '{kw}' supera los 30 caracteres")

    # description: longitud razonable
    desc = meta.get("description", "")
    if desc and len(desc) > 200:
        errors.append(f"{path}: 'description' supera los 200 caracteres ({len(desc)})")

    # Verificar que existe el ZIP
    zip_path = f"packages/{name_dir}/{ver_dir}/{name_dir}.zip"
    if not os.path.exists(zip_path):
        errors.append(f"{path}: falta el fichero ZIP esperado en '{zip_path}'")

print(f"Validados: {checked} package.json")

if errors:
    print(f"\n✗ {len(errors)} error(es) encontrado(s):")
    for e in errors:
        print(f"  ✗ {e}")
    sys.exit(1)
else:
    print("✓ Todos los package.json son válidos")
