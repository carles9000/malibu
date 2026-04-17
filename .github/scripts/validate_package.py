import json, glob, sys, re, os, subprocess

REQUIRED = ["name", "version", "description", "keywords"]
NAME_RE   = re.compile(r"^[a-z][a-z0-9-]+$")
VER_RE    = re.compile(r"^\d+\.\d+\.\d+$")
KW_RE     = re.compile(r"^[a-z][a-z0-9-]*$")

errors  = []
checked = 0

# Usuario GitHub que abre el PR (inyectado por el workflow)
pr_author = os.environ.get("GITHUB_ACTOR", "").strip()

if not pr_author:
    print("AVISO: GITHUB_ACTOR no definido, omitiendo comprobaciones de autoria")

def get_main_meta(path):
    result = subprocess.run(
        ["git", "show", f"origin/main:{path}"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        try:
            return json.loads(result.stdout)
        except Exception:
            return None
    return None

for path in sorted(glob.glob("packages/*/*/package.json")):
    parts = path.replace("\\", "/").split("/")
    name_dir, ver_dir = parts[1], parts[2]

    with open(path, encoding="utf-8") as f:
        try:
            meta = json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{path}: JSON invalido - {e}")
            continue

    checked += 1
    main_meta = get_main_meta(path)

    # ── Version ya existente en main ─────────────────────────────────
    if main_meta is not None:
        STATUS_FIELDS = {"yanked", "deprecated", "deprecated_reason"}

        current  = {k: v for k, v in meta.items()      if k not in STATUS_FIELDS}
        original = {k: v for k, v in main_meta.items() if k not in STATUS_FIELDS}

        if current != original:
            errors.append(
                f"{path}: version ya publicada e inmutable. "
                f"Solo se permite cambiar 'yanked', 'deprecated' y 'deprecated_reason'. "
                f"Para corregir el paquete publica una version nueva."
            )
            continue

        original_author = main_meta.get("author", "")
        if pr_author and original_author and pr_author != original_author:
            errors.append(
                f"{path}: solo el autor original ('{original_author}') puede cambiar "
                f"el estado de este paquete. PR abierto por '{pr_author}'."
            )
            continue

        print(f"  INFO {path}: cambio de estado por autor '{pr_author}' - permitido")
        continue

    # ── Paquete nuevo - validaciones completas ────────────────────────
    for field in REQUIRED:
        if not meta.get(field):
            errors.append(f"{path}: campo obligatorio ausente o vacio: '{field}'")

    name = meta.get("name", "")
    if name and not NAME_RE.match(name):
        errors.append(
            f"{path}: 'name' debe ser lowercase, letras, numeros y guiones "
            f"(ej: hb-mysql). Valor: '{name}'"
        )

    if name and name != name_dir:
        errors.append(
            f"{path}: 'name' ('{name}') no coincide con el directorio ('{name_dir}')"
        )

    version = meta.get("version", "")
    if version and not VER_RE.match(version):
        errors.append(
            f"{path}: 'version' debe seguir formato X.Y.Z (ej: 1.0.0). Valor: '{version}'"
        )

    if version and version != ver_dir:
        errors.append(
            f"{path}: 'version' ('{version}') no coincide con el directorio ('{ver_dir}')"
        )

    keywords = meta.get("keywords", [])
    if not isinstance(keywords, list):
        errors.append(f"{path}: 'keywords' debe ser un array")
    elif len(keywords) == 0:
        errors.append(f"{path}: 'keywords' debe tener al menos una entrada")
    else:
        for kw in keywords:
            if not isinstance(kw, str):
                errors.append(f"{path}: keyword '{kw}' debe ser texto")
            elif not KW_RE.match(kw):
                errors.append(
                    f"{path}: keyword '{kw}' debe ser lowercase, "
                    f"solo letras, numeros y guiones, sin espacios"
                )
            elif len(kw) > 30:
                errors.append(f"{path}: keyword '{kw}' supera los 30 caracteres")

    desc = meta.get("description", "")
    if desc and len(desc) > 200:
        errors.append(
            f"{path}: 'description' supera los 200 caracteres ({len(desc)})"
        )

    existing_versions = glob.glob(f"packages/{name_dir}/*/package.json")
    for ev_path in existing_versions:
        ev_main = get_main_meta(ev_path)
        if ev_main:
            ev_author = ev_main.get("author", "")
            if pr_author and ev_author and ev_author != pr_author:
                errors.append(
                    f"{path}: el paquete '{name_dir}' ya existe y pertenece "
                    f"a '{ev_author}'. No puedes publicar versiones de paquetes ajenos."
                )
                break

    zip_path = f"packages/{name_dir}/{ver_dir}/{name_dir}.zip"
    if not os.path.exists(zip_path):
        errors.append(
            f"{path}: falta el fichero ZIP esperado en '{zip_path}'"
        )

print(f"Validados: {checked} package.json")

if errors:
    print(f"\\n{len(errors)} error(es) encontrado(s):")
    for e in errors:
        print(f"  ERR {e}")
    sys.exit(1)
else:
    print("OK - Todos los package.json son validos")