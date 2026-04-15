# PokeTrip

Aplicación web de planificación de viajes desarrollada con Django. Permite organizar itinerarios día a día, controlar gastos, gestionar documentos y reservas, y compartir viajes con otros usuarios con diferentes roles.

## Características

- Planificación de viajes con itinerario por días y actividades
- Control de gastos por categoría con resumen de presupuesto
- Gestión de documentos y reservas por viaje
- Sistema de invitaciones con roles (Owner / Editor / Viewer)
- Generación de itinerario con IA
- Diseño responsive (móvil y escritorio)

## Tecnologías

- **Backend:** Python, Django
- **Base de datos:** SQLite (desarrollo) 
- **Frontend:** HTML, CSS, JavaScript
- **Despliegue:** Gunicorn + WhiteNoise

## Instalación

```bash
git clone https://github.com/tu-usuario/poketrip.git
cd poketrip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

## Estructura del proyecto

```
poketrip/          # Configuración del proyecto
accounts/          # Autenticación y perfiles de usuario
trips/             # Viajes, itinerario, gastos, documentos y reservas
templates/         # Templates HTML
static/            # CSS y archivos estáticos
```

## Autor

Gonzalo — Proyecto Final de Grado Superior DAW

