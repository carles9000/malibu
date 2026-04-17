# Malibu — Harbour Package Registry

> Repositorio público de paquetes para [HIX/Harbour](https://github.com/harbour/core).  
> Descarga paquetes sin autenticación. Publica los tuyos via Pull Request.

---

## Instalar un paquete

### Descargar el catálogo completo
```bash
curl https://raw.githubusercontent.com/carles9000/malibu/main/packages/index.json
```

### Descargar un paquete concreto
```bash
curl -L https://raw.githubusercontent.com/carles9000/malibu/main/packages/hbmysql/1.0.0/hbmysql.zip -o hbmysql.zip
```

### Ver metadatos de un paquete
```bash
curl https://raw.githubusercontent.com/carles9000/malibu/main/packages/hbmysql/1.0.0/package.json
```

---

## Explorador visual

Puedes explorar el catálogo, filtrar por autor, keywords y fecha, y resolver versiones
en el [Malibu Package Explorer](https://raw.githubusercontent.com/carles9000/malibu/main/explorer.html).

---

## Publicar un paquete

### Requisitos
- Cuenta en GitHub (gratuita)
- El paquete compilado en formato `.zip`
- Nombre en lowercase con guiones: `hb-mysql`, `hbcurl`

### Pasos

1. **Fork** de este repositorio
2. Crea la estructura de carpetas en tu fork:
   ```
   packages/{name}/{version}/
   ```
3. Añade tu `package.json`:
   ```json
   {
     "name":        "hb-mipaquete",
     "version":     "1.0.0",
     "author":      "tu-usuario-github",
     "date":        "2026-04-17",
     "description": "Descripción breve (máx 200 chars)",
     "keywords":    ["keyword1", "keyword2"],
     "deprecated":  false,
     "deprecated_reason": "",
     "yanked":      false
   }
   ```
4. Añade el fichero `{name}.zip` en la misma carpeta
5. Abre un **Pull Request** hacia este repositorio

El sistema validará automáticamente tu paquete. Si pasa la validación,
el mantenedor revisará y aprobará el PR. El índice se actualiza solo tras el merge.

---

## Reglas de publicación

### Nomenclatura

| Campo        | Formato                              | Ejemplo          |
|--------------|--------------------------------------|------------------|
| `name`       | lowercase, letras, números y guiones | `hb-mysql`       |
| `version`    | Semver X.Y.Z obligatorio             | `1.0.0`          |
| `author`     | Tu usuario de GitHub                 | `carles9000`     |
| `keywords`   | Array lowercase, mínimo 1, sin espacios | `["sql","db"]` |
| `description`| Texto libre, máximo 200 caracteres   | `MySQL connector` |

### Inmutabilidad
Las versiones publicadas son **inmutables**. Si hay un bug, publica una versión nueva (`1.0.1`).
Nunca se sobreescribe una versión existente.

### Autoría
- Solo puedes publicar paquetes con tu propio usuario de GitHub como `author`
- Solo puedes publicar nuevas versiones de paquetes que tú mismo creaste
- Solo tú puedes cambiar el estado (`deprecated`, `yanked`) de tus propios paquetes

---

## Actualizar un paquete

Crea una carpeta nueva con el nuevo número de versión. La versión anterior queda intacta:

```
packages/hb-mipaquete/
├── 1.0.0/    ← intacto
│   ├── package.json
│   └── hb-mipaquete.zip
└── 2.0.0/    ← nuevo PR con esto
    ├── package.json
    └── hb-mipaquete.zip
```

---

## Estados de un paquete

| Estado       | Visible en índice | ZIP accesible | Cuándo usar                        |
|--------------|:-----------------:|:-------------:|------------------------------------|
| Normal       | ✅                | ✅            | Estado por defecto                 |
| `deprecated` | ✅ con aviso      | ✅            | Versión antigua, existe una mejor  |
| `yanked`     | ❌                | ✅            | Bug crítico, no recomendado        |

Para solicitar la retirada urgente de un paquete, abre un
[Issue de retirada](../../issues/new?template=yank-request.yml).

---

## Campos generados automáticamente

No rellenes estos campos en tu `package.json` — el sistema los calcula solo:

| Campo        | Lo calcula         |
|--------------|--------------------|
| `url`        | build_index.py     |
| `meta_url`   | build_index.py     |
| `size_bytes` | build_index.py     |
| `sha256`     | build_index.py     |

---

## Estructura del repositorio

```
malibu/
├── packages/
│   ├── index.json                  ← catálogo maestro (auto-generado)
│   └── {name}/{version}/
│       ├── package.json            ← metadatos del paquete
│       └── {name}.zip              ← el paquete
├── .github/
│   ├── scripts/
│   │   ├── build_index.py          ← genera el índice
│   │   └── validate_package.py     ← valida PRs
│   ├── workflows/
│   │   ├── rebuild-index.yml       ← auto-regenera índice en cada push
│   │   └── validate-package.yml    ← valida cada PR automáticamente
│   ├── ISSUE_TEMPLATE/
│   │   └── yank-request.yml        ← plantilla para retirada urgente
│   └── pull_request_template.md    ← guía para colaboradores
└── README.md
```

---

## Licencia

Todos los paquetes publicados en este repositorio se distribuyen bajo licencia **MIT**
salvo que el autor indique explícitamente lo contrario en su `package.json`.

---

## Mantenedor

[@carles9000](https://github.com/carles9000)



