# GTV Agenda en GitHub

Este repositorio genera `agenda.json` directamente desde GitHub Actions y publica una web admin estática para manejar los partidos manuales.

## Qué incluye

- `scripts/build_agenda.py`: genera `agenda.json` con el mismo formato usado por tu app.
- `.github/workflows/build-agenda.yml`: ejecuta el generador cada día a las 03:07 en `America/Santiago` y también manualmente.
- `data/manual_sofa.json`: reemplaza la hoja manual.
- `admin/`: mini web para agregar, editar y eliminar partidos manuales con:
  - link de SofaScore
  - link de stream
  - escudo local URL
  - escudo visita URL
  - activo sí/no

## Formato final de agenda.json

```json
{
  "timezone": "America/Santiago",
  "duracion_partido_min": 150,
  "partidos": [
    {
      "competencia": "primera",
      "inicio": "2026-03-25T18:00:00-03:00",
      "local": { "nombre": "U. de Chile", "logo": "escudos/primera/universidaddechile.png" },
      "visita": { "nombre": "U. La Calera", "logo": "escudos/primera/unionlacalera.png" },
      "link": "https://is.gd/uchvsulc0325",
      "sofaId": "15658622"
    }
  ]
}
```

## Cómo subirlo

1. Crea un repositorio en GitHub.
2. Sube este contenido a la rama `main`.
3. Ve a **Settings → Pages** y publica desde `main` / root.
4. Entra a `https://TU-USUARIO.github.io/TU-REPO/admin/`.
5. En la web admin completa:
   - owner
   - repo
   - branch
   - ruta `data/manual_sofa.json`
   - tu fine-grained PAT con permiso `Contents: write`
6. Guarda conexión, prueba conexión y luego guarda tus partidos manuales.
7. En **Actions** puedes lanzar el workflow manualmente o esperar el horario diario.

## Notas

- La web admin guarda el token en `localStorage` del navegador que uses.
- Si quieres, puedes dejar `data/config.json` con owner y repo ya completados.
- El workflow hace commit solo si `agenda.json` cambia.
- Los escudos manuales ganan prioridad sobre los escudos automáticos.
- Si el `link` del stream queda vacío, el generador intenta crear el is.gd automático a partir de `nameCode`.
