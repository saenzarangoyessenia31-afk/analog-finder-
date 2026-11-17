"""Analog Finder - NASA Space Apps Challenge 2026
Reto: Identify Earth Locations that Analog the Permanent Moon Base Locations and Mars.
Catalogo colaborativo de lugares de la Tierra parecidos a la Luna o Marte.
"""
import os
import sqlite3
from functools import wraps

from flask import (Flask, abort, flash, g, redirect, render_template, request,
                   session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'INVESTIGADOR' CHECK (rol IN ('ADMIN','INVESTIGADOR')),
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS sitios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    pais TEXT NOT NULL,
    tipo_terreno TEXT NOT NULL,
    analogo_de TEXT NOT NULL CHECK (analogo_de IN ('Luna','Marte')),
    temperatura_media REAL,
    descripcion TEXT NOT NULL,
    estado TEXT NOT NULL DEFAULT 'PENDIENTE' CHECK (estado IN ('PENDIENTE','APROBADO')),
    creado_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""

TIPOS_TERRENO = ["Desierto", "Cráter", "Volcánico", "Polar", "Cueva", "Árido"]
CUERPOS = ["Luna", "Marte"]

DEMO_SITIOS = [
    ("Desierto de Atacama", "Chile", "Desierto", "Marte", 17.0,
     "Ejemplo de demostración: uno de los desiertos más áridos, usado como referencia para probar equipos."),
    ("Cráter Haughton", "Canadá", "Cráter", "Marte", -16.0,
     "Ejemplo de demostración: cráter de impacto en la isla Devon, referencia para entrenamiento de misiones."),
    ("Campos de lava de Lanzarote", "España", "Volcánico", "Luna", 21.0,
     "Ejemplo de demostración: terreno volcánico con basalto, útil para probar movilidad de vehículos."),
]


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "clave-de-desarrollo-cambiar"),
        DATABASE=os.environ.get("DATABASE_PATH", os.path.join(app.root_path, "analogos.db")),
        SEED_DEMO=True,
        ADMIN_EMAIL=os.environ.get("ADMIN_EMAIL", "admin@analogos.local"),
        ADMIN_PASSWORD=os.environ.get("ADMIN_PASSWORD", "Admin12345"),
    )
    if test_config:
        app.config.update(test_config)

    # ---------- Base de datos ----------
    def get_db():
        if "db" not in g:
            g.db = sqlite3.connect(app.config["DATABASE"])
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
        return g.db

    @app.teardown_appcontext
    def close_db(_exc):
        db = g.pop("db", None)
        if db is not None:
            db.close()

    def init_db():
        db = get_db()
        db.executescript(SCHEMA)
        admin = db.execute("SELECT id FROM usuarios WHERE email = ?",
                           (app.config["ADMIN_EMAIL"],)).fetchone()
        if admin is None:
            db.execute(
                "INSERT INTO usuarios (nombre, email, password_hash, rol) VALUES (?,?,?,'ADMIN')",
                ("Administrador", app.config["ADMIN_EMAIL"],
                 generate_password_hash(app.config["ADMIN_PASSWORD"])))
            admin_id = db.execute("SELECT id FROM usuarios WHERE email = ?",
                                  (app.config["ADMIN_EMAIL"],)).fetchone()["id"]
            if app.config["SEED_DEMO"]:
                for s in DEMO_SITIOS:
                    db.execute(
                        "INSERT INTO sitios (nombre,pais,tipo_terreno,analogo_de,temperatura_media,"
                        "descripcion,estado,creado_por) VALUES (?,?,?,?,?,?, 'APROBADO', ?)",
                        (*s, admin_id))
        db.commit()

    with app.app_context():
        init_db()

    # ---------- Sesion y permisos ----------
    @app.before_request
    def cargar_usuario():
        uid = session.get("user_id")
        g.user = None
        if uid is not None:
            g.user = get_db().execute("SELECT * FROM usuarios WHERE id = ?", (uid,)).fetchone()
            if g.user is None:
                session.clear()

    def login_required(vista):
        @wraps(vista)
        def envoltura(*a, **kw):
            if g.user is None:
                flash("Debes iniciar sesión para continuar.", "error")
                return redirect(url_for("login"))
            return vista(*a, **kw)
        return envoltura

    def admin_required(vista):
        @wraps(vista)
        @login_required
        def envoltura(*a, **kw):
            if g.user["rol"] != "ADMIN":
                abort(403)
            return vista(*a, **kw)
        return envoltura

    # ---------- Utilidades ----------
    def validar_sitio(form):
        datos = {
            "nombre": form.get("nombre", "").strip(),
            "pais": form.get("pais", "").strip(),
            "tipo_terreno": form.get("tipo_terreno", "").strip(),
            "analogo_de": form.get("analogo_de", "").strip(),
            "temperatura_media": form.get("temperatura_media", "").strip(),
            "descripcion": form.get("descripcion", "").strip(),
        }
        errores = []
        for campo in ("nombre", "pais", "descripcion"):
            if not datos[campo]:
                errores.append(f"El campo {campo} es obligatorio.")
        if datos["tipo_terreno"] not in TIPOS_TERRENO:
            errores.append("Selecciona un tipo de terreno válido.")
        if datos["analogo_de"] not in CUERPOS:
            errores.append("Selecciona Luna o Marte.")
        temp = None
        if datos["temperatura_media"]:
            try:
                temp = float(datos["temperatura_media"])
            except ValueError:
                errores.append("La temperatura debe ser un número.")
        datos["temperatura_media"] = temp
        return datos, errores

    def obtener_sitio(sitio_id):
        sitio = get_db().execute(
            "SELECT s.*, u.nombre AS autor FROM sitios s JOIN usuarios u ON u.id = s.creado_por "
            "WHERE s.id = ?", (sitio_id,)).fetchone()
        if sitio is None:
            abort(404)
        return sitio

    def puede_gestionar(sitio):
        return g.user is not None and (g.user["rol"] == "ADMIN" or g.user["id"] == sitio["creado_por"])

    # ---------- Publico ----------
    @app.route("/")
    def index():
        q = request.args.get("q", "").strip()
        cuerpo = request.args.get("cuerpo", "").strip()
        sql = ("SELECT s.*, u.nombre AS autor FROM sitios s JOIN usuarios u ON u.id = s.creado_por "
               "WHERE s.estado = 'APROBADO'")
        params = []
        if q:
            sql += " AND (s.nombre LIKE ? OR s.pais LIKE ? OR s.descripcion LIKE ?)"
            params += [f"%{q}%"] * 3
        if cuerpo in CUERPOS:
            sql += " AND s.analogo_de = ?"
            params.append(cuerpo)
        sql += " ORDER BY s.nombre"
        sitios = get_db().execute(sql, params).fetchall()
        return render_template("index.html", sitios=sitios, q=q, cuerpo=cuerpo, cuerpos=CUERPOS)

    @app.route("/sitios/<int:sitio_id>")
    def detalle(sitio_id):
        sitio = obtener_sitio(sitio_id)
        if sitio["estado"] != "APROBADO" and not puede_gestionar(sitio):
            abort(404)
        return render_template("detalle.html", sitio=sitio, puede=puede_gestionar(sitio))

    # ---------- Usuarios ----------
    @app.route("/registro", methods=["GET", "POST"])
    def registro():
        if request.method == "POST":
            nombre = request.form.get("nombre", "").strip()
            email = request.form.get("email", "").strip().lower()
            clave = request.form.get("password", "")
            error = None
            if not nombre or not email or "@" not in email:
                error = "Completa nombre y un correo válido."
            elif len(clave) < 6:
                error = "La contraseña debe tener al menos 6 caracteres."
            elif get_db().execute("SELECT 1 FROM usuarios WHERE email = ?", (email,)).fetchone():
                error = "Ese correo ya está registrado."
            if error:
                flash(error, "error")
            else:
                db = get_db()
                db.execute("INSERT INTO usuarios (nombre,email,password_hash,rol) VALUES (?,?,?,'INVESTIGADOR')",
                           (nombre, email, generate_password_hash(clave)))
                db.commit()
                flash("Registro exitoso. Ya puedes iniciar sesión.", "ok")
                return redirect(url_for("login"))
        return render_template("registro.html")

    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form.get("email", "").strip().lower()
            clave = request.form.get("password", "")
            usuario = get_db().execute("SELECT * FROM usuarios WHERE email = ?", (email,)).fetchone()
            if usuario is None or not check_password_hash(usuario["password_hash"], clave):
                flash("Correo o contraseña incorrectos.", "error")
            else:
                session.clear()
                session["user_id"] = usuario["id"]
                flash(f"Bienvenido, {usuario['nombre']}.", "ok")
                return redirect(url_for("panel"))
        return render_template("login.html")

    @app.route("/logout", methods=["POST"])
    def logout():
        session.clear()
        flash("Sesión cerrada.", "ok")
        return redirect(url_for("index"))

    # ---------- Panel y CRUD ----------
    @app.route("/panel")
    @login_required
    def panel():
        db = get_db()
        if g.user["rol"] == "ADMIN":
            total = db.execute("SELECT COUNT(*) c FROM sitios").fetchone()["c"]
            pendientes = db.execute("SELECT COUNT(*) c FROM sitios WHERE estado='PENDIENTE'").fetchone()["c"]
            usuarios = db.execute("SELECT COUNT(*) c FROM usuarios").fetchone()["c"]
        else:
            total = db.execute("SELECT COUNT(*) c FROM sitios WHERE creado_por=?", (g.user["id"],)).fetchone()["c"]
            pendientes = db.execute("SELECT COUNT(*) c FROM sitios WHERE creado_por=? AND estado='PENDIENTE'",
                                    (g.user["id"],)).fetchone()["c"]
            usuarios = None
        return render_template("panel.html", total=total, pendientes=pendientes, usuarios=usuarios)

    @app.route("/mis-sitios")
    @login_required
    def mis_sitios():
        db = get_db()
        if g.user["rol"] == "ADMIN":
            filas = db.execute("SELECT s.*, u.nombre AS autor FROM sitios s JOIN usuarios u "
                               "ON u.id = s.creado_por ORDER BY s.id DESC").fetchall()
        else:
            filas = db.execute("SELECT s.*, u.nombre AS autor FROM sitios s JOIN usuarios u "
                               "ON u.id = s.creado_por WHERE s.creado_por = ? ORDER BY s.id DESC",
                               (g.user["id"],)).fetchall()
        return render_template("mis_sitios.html", sitios=filas)

    @app.route("/sitios/nuevo", methods=["GET", "POST"])
    @login_required
    def crear():
        if request.method == "POST":
            datos, errores = validar_sitio(request.form)
            if errores:
                for e in errores:
                    flash(e, "error")
                return render_template("form_sitio.html", sitio=request.form, tipos=TIPOS_TERRENO,
                                       cuerpos=CUERPOS, titulo="Nuevo sitio")
            estado = "APROBADO" if g.user["rol"] == "ADMIN" else "PENDIENTE"
            db = get_db()
            db.execute(
                "INSERT INTO sitios (nombre,pais,tipo_terreno,analogo_de,temperatura_media,descripcion,"
                "estado,creado_por) VALUES (?,?,?,?,?,?,?,?)",
                (datos["nombre"], datos["pais"], datos["tipo_terreno"], datos["analogo_de"],
                 datos["temperatura_media"], datos["descripcion"], estado, g.user["id"]))
            db.commit()
            flash("Sitio creado." + (" Queda pendiente de aprobación." if estado == "PENDIENTE" else ""), "ok")
            return redirect(url_for("mis_sitios"))
        return render_template("form_sitio.html", sitio={}, tipos=TIPOS_TERRENO, cuerpos=CUERPOS,
                               titulo="Nuevo sitio")

    @app.route("/sitios/<int:sitio_id>/editar", methods=["GET", "POST"])
    @login_required
    def editar(sitio_id):
        sitio = obtener_sitio(sitio_id)
        if not puede_gestionar(sitio):
            abort(403)
        if request.method == "POST":
            datos, errores = validar_sitio(request.form)
            if errores:
                for e in errores:
                    flash(e, "error")
                return render_template("form_sitio.html", sitio=request.form, tipos=TIPOS_TERRENO,
                                       cuerpos=CUERPOS, titulo="Editar sitio")
            estado = sitio["estado"] if g.user["rol"] == "ADMIN" else "PENDIENTE"
            db = get_db()
            db.execute(
                "UPDATE sitios SET nombre=?, pais=?, tipo_terreno=?, analogo_de=?, temperatura_media=?, "
                "descripcion=?, estado=? WHERE id=?",
                (datos["nombre"], datos["pais"], datos["tipo_terreno"], datos["analogo_de"],
                 datos["temperatura_media"], datos["descripcion"], estado, sitio_id))
            db.commit()
            flash("Sitio actualizado.", "ok")
            return redirect(url_for("mis_sitios"))
        return render_template("form_sitio.html", sitio=sitio, tipos=TIPOS_TERRENO, cuerpos=CUERPOS,
                               titulo="Editar sitio")

    @app.route("/sitios/<int:sitio_id>/eliminar", methods=["POST"])
    @login_required
    def eliminar(sitio_id):
        sitio = obtener_sitio(sitio_id)
        if not puede_gestionar(sitio):
            abort(403)
        db = get_db()
        db.execute("DELETE FROM sitios WHERE id = ?", (sitio_id,))
        db.commit()
        flash("Sitio eliminado.", "ok")
        return redirect(url_for("mis_sitios"))

    # ---------- Administracion ----------
    @app.route("/admin/sitios/<int:sitio_id>/aprobar", methods=["POST"])
    @admin_required
    def aprobar(sitio_id):
        obtener_sitio(sitio_id)
        db = get_db()
        db.execute("UPDATE sitios SET estado='APROBADO' WHERE id = ?", (sitio_id,))
        db.commit()
        flash("Sitio aprobado.", "ok")
        return redirect(url_for("mis_sitios"))

    @app.route("/admin/usuarios")
    @admin_required
    def admin_usuarios():
        usuarios = get_db().execute("SELECT id,nombre,email,rol,creado_en FROM usuarios ORDER BY id").fetchall()
        return render_template("admin_usuarios.html", usuarios=usuarios)

    @app.route("/admin/usuarios/<int:uid>/eliminar", methods=["POST"])
    @admin_required
    def eliminar_usuario(uid):
        if uid == g.user["id"]:
            flash("No puedes eliminar tu propia cuenta.", "error")
        else:
            db = get_db()
            db.execute("DELETE FROM usuarios WHERE id = ?", (uid,))
            db.commit()
            flash("Usuario eliminado.", "ok")
        return redirect(url_for("admin_usuarios"))

    # ---------- Errores ----------
    @app.errorhandler(403)
    def prohibido(_e):
        return render_template("error.html", codigo=403, mensaje="No tienes permiso para ver esta página."), 403

    @app.errorhandler(404)
    def no_encontrado(_e):
        return render_template("error.html", codigo=404, mensaje="La página no existe."), 404

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
