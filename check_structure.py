import os, json, re, glob, sys

OK    = "  OK  "
WARN  = "  WARN"
ERROR = "  ERR "

results = []
errors  = 0
warns   = 0

def ok(msg):
    results.append(OK + " " + msg)

def warn(msg):
    global warns
    warns += 1
    results.append(WARN + " " + msg)

def error(msg):
    global errors
    errors += 1
    results.append(ERROR + " " + msg)

def section(title):
    results.append("")
    results.append("-- " + title + " --")

def parse_pkg_dir(pkg_dir):
    # os.path.normpath + split por sep funciona en Windows y Linux
    normalized = os.path.normpath(pkg_dir)
    parts = normalized.split(os.sep)
    try:
        idx = parts.index("packages")
        return parts[idx + 1], parts[idx + 2]
    except (ValueError, IndexError):
        return None, None

NAME_RE = re.compile(r"^[a-z][a-z0-9-]+$")
VER_RE  = re.compile(r"^[0-9]+[.][0-9]+[.][0-9]+$")
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
        error("Falta: " + f)

section("2. Ficheros incorrectos en .github/workflows/")

wf_dir = os.path.join(".github", "workflows")
if os.path.exists(wf_dir):
    for f in os.listdir(wf_dir):
        path = os.path.join(wf_dir, f)
        if not f.endswith(".yml") and not f.endswith(".yaml"):
            warn("Fichero no-yml en workflows: " + path)
            continue
        with open(path, encoding="utf-8") as fh:
            content_wf = fh.read()
        if "jobs:" not in content_wf and "on:" not in content_wf:
            error("Parece Issue Template, no workflow: " + path)
        else:
            ok("Workflow valido: " + f)

section("3. Estructura de paquetes")

pattern  = os.path.join("packages", "*", "*", "")
pkg_dirs = sorted(glob.glob(pattern))

if not pkg_dirs:
    warn("No hay paquetes en packages/")
else:
    ok("Se encontraron " + str(len(pkg_dirs)) + " carpeta(s) de version")

for pkg_dir in pkg_dirs:
    name, version = parse_pkg_dir(pkg_dir)

    if not name or not version:
        warn("No se pudo parsear: " + pkg_dir)
        continue

    pjson = os.path.join(pkg_dir, "package.json")
    if not os.path.exists(pjson):
        error("Falta package.json en " + pkg_dir)
        continue

    zip_path = os.path.join(pkg_dir, name + ".zip")
    if not os.path.exists(zip_path):
        warn("Falta " + name + ".zip en " + pkg_dir)

    with open(pjson, encoding="utf-8") as f:
        try:
            meta = json.load(f)
        except json.JSONDecodeError as e:
            error(pjson + ": JSON invalido - " + str(e))
            continue

    pkg_errors = []

    pname = meta.get("name", "")
    if not pname:
        pkg_errors.append("falta 'name'")
    elif not NAME_RE.match(pname):
        pkg_errors.append("name invalido: '" + pname + "' (lowercase letras/nums/guiones)")
    elif pname != name:
        pkg_errors.append("name '" + pname + "' no coincide con directorio '" + name + "'")

    pver = meta.get("version", "")
    if not pver:
        pkg_errors.append("falta 'version'")
    elif not VER_RE.match(pver):
        pkg_errors.append("version invalida: '" + pver + "' (debe ser X.Y.Z)")
    elif pver != version:
        pkg_errors.append("version '" + pver + "' no coincide con directorio '" + version + "'")

    if not meta.get("description"):
        pkg_errors.append("falta 'description'")
    elif len(meta["description"]) > 200:
        pkg_errors.append("description supera 200 chars")

    kws = meta.get("keywords", [])
    if not isinstance(kws, list) or len(kws) == 0:
        pkg_errors.append("keywords debe ser array con al menos 1 entrada")
    else:
        for kw in kws:
            if not KW_RE.match(str(kw)):
                pkg_errors.append("keyword invalida: '" + str(kw) + "'")

    yanked     = meta.get("yanked", False)
    deprecated = meta.get("deprecated", False)

    if pkg_errors:
        for e in pkg_errors:
            error(name + " v" + version + ": " + e)
    else:
        status = " [YANKED]" if yanked else " [DEPRECATED]" if deprecated else ""
        ok(name + " v" + version + status)

section("4. Validacion de packages/index.json")

idx_path = os.path.join("packages", "index.json")
if os.path.exists(idx_path):
    with open(idx_path, encoding="utf-8") as f:
        try:
            index = json.load(f)
            ok("index.json valido con " + str(len(index)) + " entradas")
            yanked_count     = sum(1 for e in index if e.get("yanked"))
            deprecated_count = sum(1 for e in index if e.get("deprecated") and not e.get("yanked"))
            active_count     = len(index) - yanked_count - deprecated_count
            ok("Activos: " + str(active_count) + " | Deprecated: " + str(deprecated_count) + " | Yanked: " + str(yanked_count))
        except json.JSONDecodeError as e:
            error("index.json no es JSON valido: " + str(e))
else:
    error("Falta packages/index.json")

section("5. Contenido de workflows")

WORKFLOW_CHECKS = {
    os.path.join(".github","workflows","rebuild-index.yml"): [
        ("build_index.py",           "Llama a build_index.py"),
        ("workflow_dispatch",        "Tiene trigger manual"),
        ("packages/**/package.json", "Tiene path filter correcto"),
        ("[skip ci]",                "Evita bucle infinito con [skip ci]"),
        ("GITHUB_ACTOR",             "Inyecta GITHUB_ACTOR"),
    ],
    os.path.join(".github","workflows","validate-package.yml"): [
        ("validate_package.py", "Llama a validate_package.py"),
        ("pull_request",        "Tiene trigger pull_request"),
        ("GITHUB_ACTOR",        "Inyecta GITHUB_ACTOR"),
    ],
}

for wf_path, checks in WORKFLOW_CHECKS.items():
    fname = os.path.basename(wf_path)
    if os.path.exists(wf_path):
        with open(wf_path, encoding="utf-8") as f:
            wf_content = f.read()
        for needle, desc in checks:
            if needle in wf_content:
                ok(fname + ": " + desc)
            else:
                warn(fname + ": NO encontrado '" + needle + "' - " + desc)
    else:
        error("Falta " + wf_path)

results.append("")
results.append("=" * 55)
if errors == 0 and warns == 0:
    results.append("TODO OK - estructura del repositorio correcta")
elif errors == 0:
    results.append("AVISOS: " + str(warns) + " warning(s) - revisa los WARN")
else:
    results.append("ERRORES: " + str(errors) + " error(es), " + str(warns) + " aviso(s)")
results.append("=" * 55)

print(os.linesep.join(results))
sys.exit(1 if errors > 0 else 0)