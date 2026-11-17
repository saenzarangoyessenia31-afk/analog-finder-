# Lo que debes hacer tú (con tu computadora y tus cuentas)

## 1. Probar en local
1. Instala Python 3.11+ y VS Code. Descomprime el proyecto y ábrelo en VS Code.
2. En la terminal de VS Code:
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   python app.py
3. Abre http://127.0.0.1:5000

## 2. Capturas para el PDF (guárdalas con estos nombres)
 01_catalogo.png            Página principal con los 3 sitios de ejemplo
 02_registro.png            Formulario de registro
 03_login.png               Formulario de login
 04_panel_investigador.png  Panel tras entrar como investigador (rol visible arriba)
 05_crear_sitio.png         Formulario de nuevo sitio
 06_lista_pendiente.png     Lista "Mis sitios" con el sitio en PENDIENTE
 07_editar_sitio.png        Edición de un sitio
 08_eliminar.png            Mensaje "Sitio eliminado"
 09_admin_aprobar.png       Admin aprobando un sitio
 10_admin_usuarios.png      Gestión de usuarios (solo admin)
 11_error_403.png           Investigador entrando a /admin/usuarios
 12_logout.png              Mensaje "Sesión cerrada"
 13_pruebas.png             Terminal con: python -m pytest -v  (18 passed)
 14_github.png              Tu repositorio en GitHub
 15_render_deploy.png       Panel de Render con "Live"
 16_app_render_catalogo.png App abierta en la URL de Render
 17_app_render_login.png    Login/panel funcionando en Render
 18_certificado.png         Constancia de NASA Space Apps (cuando la tengas)

## 3. GitHub
   git init
   git add .
   git commit -m "Analog Finder - trabajo final"
   git branch -M main
   git remote add origin https://github.com/TU_USUARIO/analog-finder.git
   git push -u origin main
(Antes crea el repositorio vacío "analog-finder" en github.com, público.)

## 4. Render
1. render.com > New > Web Service > conecta tu repositorio.
2. Runtime: Python 3. Build: pip install -r requirements.txt. Start: gunicorn app:app. Plan: Free.
3. Environment: SECRET_KEY (texto largo aleatorio), ADMIN_EMAIL, ADMIN_PASSWORD (una clave propia).
4. Deploy. La primera carga puede tardar ~1 minuto.

## 5. PDF final
Índice sugerido: 1 Reto y solución · 2 Capturas de la app · 3 Usuarios y roles · 4 CRUD ·
5 Pruebas · 6 Enlace GitHub · 7 Enlace Render y capturas · 8 Certificado NASA Space Apps.
