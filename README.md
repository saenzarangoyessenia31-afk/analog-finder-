# 🌖 Analog Finder

Aplicación web en **Python Flask + SQLite** creada para el trabajo final del curso, tomando como referencia el reto del **NASA Space Apps Challenge 2026**:
*Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars*.

## Problema
Antes de enviar equipos o astronautas a la Luna o a Marte, las agencias necesitan lugares de la Tierra con condiciones parecidas (desiertos, cráteres, terreno volcánico, zonas polares, cuevas) para probar tecnología y entrenar.

## Solución
Un catálogo colaborativo: los investigadores registran lugares análogos, un administrador los revisa y aprueba, y cualquier persona puede consultar y buscar el catálogo público.

## Módulos
- **Catálogo público**: búsqueda por texto y filtro Luna/Marte.
- **Usuarios**: registro, inicio y cierre de sesión (contraseñas con hash).
- **Roles**: `INVESTIGADOR` (gestiona solo sus sitios; quedan *pendientes*) y `ADMIN` (gestiona todo, aprueba sitios y administra usuarios).
- **CRUD de sitios** sobre SQLite: crear, listar, ver, editar, eliminar.
- **Panel** con estadísticas.

## Ejecutar en local
```bash
python -m venv venv
venv\Scripts\activate          # Windows  (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
python app.py
```
Abrir http://127.0.0.1:5000

Administrador inicial: `admin@analogos.local` / `Admin12345` (cámbialo con las variables `ADMIN_EMAIL` y `ADMIN_PASSWORD`).

## Pruebas automatizadas
```bash
python -m pytest -v
```

## Despliegue en Render
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Variables: `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`

> En el plan gratuito de Render el disco es temporal: la base SQLite se reinicia al redesplegar o reiniciar, y los datos de ejemplo se vuelven a crear.

## Enlaces
- Repositorio: _(pegar aquí)_
- Aplicación en Render: _(pegar aquí)_
