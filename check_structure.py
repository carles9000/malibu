import os, json, re, glob, sys

OK    = "  OK  "
WARN  = "  WARN"
ERROR = "  ERR "

results = []
errors  = 0
warns   = 0

def ok(msg):
    results.append(f"{OK} {msg}")

def warn(msg):
    global warns
    warns += 1
    results.append(f"{WARN} {msg}")

def error(msg):
    global errors
    errors += 1
    results.append(f"{ERROR} {msg}")

def section(title):
    results.append(f"\n-- {title} --")

NAME_RE = re.compile(r"^[a-z][a-z0-9-]+$")
VER_RE  = re.compile(r"^\d+\.\d+\.\d+$")
KW_RE   = re.compile(r"^[a-z][a-z0-9-]*$")

section("1. Ficheros obligatorios del sistema")

REQUIRED_FILES = [
    ".github/scripts/build_index.py",
    ".github/scripts/validate_package.py",
    ".github/workflows/rebuild-index.yml",
    ".github/workflows/validate-package.yml",
    ".github/pull_request_template.md",
    ".github/ISSUE_TEMPLATE/yank-request.yml",
    "packages/index.json",
    "README.md",
]

for f in REQUIRED_FILES:
    if os.path.exists(f):
        ok(f)
    else:
        error(f"Falta: {f}")

section("2. Ficheros incorrectos en .github/workflows/")

if os.path.exists(".github/workflows"):
    for f in os.listdir(".github/workflows"):
        path = f".github/workflows/{f}"
        if not f.endswith(".yml") and not f.endswith(".yaml"):
            warn(f"Fichero no-yml en workflows: {path}")
            continue
        with open(path) as fh:
            content_wf = fh.read()
        if "jobs:" not in content_wf and "on:" not in content_wf:
            error(f"Parece Issue Template, no workflow: {path}")
        else:
            ok(f"Workflow valido: {path}")

section("3. Estructura de paquetes")

package_dirs = sorted(glob.glob("packages/*/*/"))
if not package_dirs:
    warn("No hay paquetes en packages/")
else:
    ok(f"Se encontraron {len(package_dirs)} carpeta(s) de version")

for pkg_dir in package_dirs:
    parts = pkg_dir.replace("\\", "/").rstrip("/").split("/")
    name, version = parts[1], parts[2]

    pjson = os.path.join(pkg_dir, "package.json")
    if not os.path.exists(pjson):
        error(f"Falta package.json en {pkg_dir}")
        continue

    zip_path = os.path.join(pkg_dir, name + ".zip")
    if not os.path.exists(zip_path):
        warn(f"Falta {name}.zip en {pkg_dir}")

    with open(pjson, encoding="utf-8") as f:
        try:
            meta = json.load(f)
        except json.JSONDecodeError as e:
            error(f"{pjson}: JSON invalido - {e}")
            continue

    pkg_errors = []

    pname = meta.get("name", "")
    if not pname:
        pkg_errors.append("falta 'name'")
    elif not NAME_RE.match(pname):
        pkg_errors.append(f"name invalido: '{pname}'")
    elif pname != name:
        pkg_errors.append(f"name '{pname}' no coincide con directorio '{name}'")

    pver = meta.get("version", "")
    if not pver:
        pkg_errors.append("falta 'version'")
    elif not VER_RE.match(pver):
        pkg_errors.append(f"version invalida: '{pver}' (debe ser X.Y.Z)")
    elif pver != version:
        pkg_errors.append(f"version '{pver}' no coincide con directorio '{version}'")

    if not meta.get("description"):
        pkg_errors.append("falta 'description'")
    elif len(meta["description"]) > 200:
        pkg_errors.append(f"description supera 200 chars")

    if not meta.get("author"):
        pkg_errors.append("falta 'author'")

    if not meta.get("date"):
        pkg_errors.append("falta 'date'")

    kws = meta.get("keywords", [])
    if not isinstance(kws, list) or len(kws) == 0:
        pkg_errors.append("keywords debe ser array con al menos 1 entrada")
    else:
        for kw in kws:
            if not KW_RE.match(str(kw)):
                pkg_errors.append(f"keyword invalida: '{kw}'")

    yanked     = meta.get("yanked", False)
    deprecated = meta.get("deprecated", False)

    if pkg_errors:
        for e in pkg_errors:
            error(f"{name} v{version}: {e}")
    else:
        status = " [YANKED]" if yanked else " [DEPRECATED]" if deprecated else ""
        ok(f"{name} v{version}{status}")

section("4. Validacion de packages/index.json")

if os.path.exists("packages/index.json"):
    with open("packages/index.json", encoding="utf-8") as f:
        try:
            index = json.load(f)
            ok(f"index.json valido con {len(index)} entradas")
            yanked_count     = sum(1 for e in index if e.get("yanked"))
            deprecated_count = sum(1 for e in index if e.get("deprecated") and not e.get("yanked"))
            active_count     = len(index) - yanked_count - deprecated_count
            ok(f"Activos: {active_count} | Deprecated: {deprecated_count} | Yanked: {yanked_count}")
        except json.JSONDecodeError as e:
            error(f"index.json no es JSON valido: {e}")
else:
    error("Falta packages/index.json")

section("5. Contenido de workflows")

WORKFLOW_CHECKS = {
    ".github/workflows/rebuild-index.yml": [
        ("build_index.py",           "Llama a build_index.py"),
        ("workflow_dispatch",        "Tiene trigger manual"),
        ("packages/**/package.json", "Tiene path filter correcto"),
        ("[skip ci]",                "Evita bucle infinito con [skip ci]"),
    ],
    ".github/workflows/validate-package.yml": [
        ("validate_package.py", "Llama a validate_package.py"),
        ("pull_request",        "Tiene trigger pull_request"),
        ("GITHUB_ACTOR",        "Inyecta GITHUB_ACTOR"),
    ],
}

for wf_path, checks in WORKFLOW_CHECKS.items():
    if os.path.exists(wf_path):
        with open(wf_path, encoding="utf-8") as f:
            wf_content = f.read()
        for needle, desc in checks:
            if needle in wf_content:
                ok(f"{wf_path}: {desc}")
            else:
                warn(f"{wf_path}: NO encontrado '{needle}' - {desc}")
    else:
        error(f"Falta {wf_path}")

results.append(f"\n{'='*55}")
if errors == 0 and warns == 0:
    results.append("TODO OK - estructura del repositorio correcta")
elif errors == 0:
    results.append(f"AVISOS: {warns} warning(s) - revisa los WARN")
else:
    results.append(f"ERRORES: {errors} error(es), {warns} aviso(s)")
results.append("="*55)

print("\n".join(results))
sys.exit(1 if errors > 0 else 0)