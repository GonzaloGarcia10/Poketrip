# PokeTrip

PokeTrip es una aplicación web de planificación de viajes desarrollada con Django como proyecto final de DAW. La aplicación permite centralizar en un solo sitio la información principal de cada viaje: destino, fechas, itinerario, gastos, documentos, reservas y miembros invitados.

Además de la gestión interna del viaje, el proyecto integra datos externos en tiempo real para enriquecer la experiencia del usuario, como el clima actual, información del país de destino y tipos de cambio de moneda.

## Objetivo del proyecto

El objetivo de PokeTrip es ofrecer una herramienta práctica para organizar viajes de forma clara y colaborativa. En lugar de repartir la información entre notas, correos, documentos y capturas, la aplicación reúne todo en una única plataforma accesible desde distintos dispositivos.

## Funcionalidades principales

- Registro, inicio de sesión y gestión de perfil de usuario.
- Creación y edición de viajes con destino, fechas, presupuesto, moneda y estilo de viaje.
- Generación automática de los días del viaje a partir del rango de fechas.
- Itinerario por días con actividades, transporte, comidas, alojamiento u otros elementos.
- Gestión de gastos por viaje y vista global de control económico.
- Subida y gestión de documentos vinculados a cada viaje.
- Registro de reservas, como vuelos, hoteles o actividades.
- Sistema de invitaciones para compartir viajes con otros usuarios.
- Información del destino obtenida desde APIs públicas.
- Asistente de viaje con IA para sugerencias y apoyo a la planificación.
- Interfaz responsive adaptada a escritorio y móvil.

## Tecnologías utilizadas

### Backend

- Python 3
- Django 4
- Gunicorn como servidor WSGI en producción
- WhiteNoise para servir archivos estáticos en despliegue
- dj-database-url para configurar la base de datos mediante variables de entorno
- python-decouple para gestionar configuración sensible

### Base de datos

- SQLite en desarrollo
- PostgreSQL compatible en producción mediante `DATABASE_URL`

### Frontend

- HTML para las vistas renderizadas por Django
- CSS para el diseño de interfaz y adaptación responsive
- JavaScript para interacciones en cliente y consumo de APIs externas

### Librerías e integraciones adicionales

- Pillow para subida de imágenes, como el avatar de usuario
- OpenAI para funcionalidades de asistencia y generación de contenido
- Open-Meteo para geolocalización y clima actual
- REST Countries para información del país
- Frankfurter para tipos de cambio de moneda

## Arquitectura general

El proyecto sigue una arquitectura monolítica basada en Django. La aplicación está separada en dos apps principales:

- `accounts`: gestiona autenticación, registro, perfil y recuperación de contraseña.
- `trips`: concentra la lógica de negocio relacionada con los viajes.

La entidad central del sistema es `Trip`, y a partir de ella se relacionan el resto de módulos: días del viaje, itinerario, gastos, reservas, documentos, miembros e interacciones con IA.

## Módulos del proyecto

### 1. Gestión de usuarios

Incluye registro, inicio de sesión, cierre de sesión, recuperación de contraseña y edición del perfil. Cada usuario dispone de un perfil extendido con avatar y biografía.

### 2. Gestión de viajes

Cada viaje almacena la información principal de planificación:

- título
- destino
- fecha de inicio y fin
- presupuesto
- moneda
- estilo de viaje

Cuando se crea o edita un viaje, el sistema genera automáticamente sus días para construir el itinerario.

### 3. Itinerario

El itinerario se organiza por días. Cada día puede contener actividades o elementos como transporte, comidas, alojamiento u otras anotaciones relevantes para la planificación.

### 4. Gastos

Los gastos se pueden registrar por categoría y quedan asociados al viaje correspondiente. La aplicación ofrece tanto una vista concreta por viaje como una vista global para revisar todos los gastos del usuario.

### 5. Documentos y reservas

El usuario puede adjuntar documentos relacionados con el viaje, como billetes, justificantes o archivos PDF, y registrar reservas de hotel, vuelo o actividades.

### 6. Colaboración entre usuarios

Los viajes pueden compartirse mediante invitaciones. El propietario genera un enlace asociado a un token, y el usuario invitado puede aceptar la invitación y formar parte del viaje.

### 7. Integración de APIs externas

La aplicación enriquece la pantalla de detalle del viaje con información obtenida en tiempo real desde servicios externos:

- Open-Meteo: geocodificación del destino y clima actual.
- REST Countries: capital, idiomas, moneda, bandera, región y población.
- Frankfurter: conversión de moneda a partir de la divisa del viaje.

### 8. Asistente con IA

PokeTrip incorpora un asistente basado en OpenAI que puede responder preguntas generales sobre viajes y, en determinados contextos, sugerir actividades para el itinerario del usuario.

## Requisitos mínimos

- Python 3.11 recomendado
- Entorno virtual de Python
- Dependencias del archivo `requirements.txt`

## Instalación en local

```bash
git clone https://github.com/tu-usuario/poketrip.git
cd poketrip
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Variables de entorno

El proyecto utiliza variables de entorno para separar la configuración del código. Las principales son:

- `SECRET_KEY`
- `DEBUG`
- `ALLOWED_HOSTS`
- `CSRF_TRUSTED_ORIGINS`
- `DATABASE_URL`
- `OPENAI_API_KEY`

Ejemplo orientativo:

```env
SECRET_KEY=tu_clave_secreta
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=
DATABASE_URL=sqlite:///db.sqlite3
OPENAI_API_KEY=
```

## Ejecución del proyecto

Aplicar migraciones:

```bash
python manage.py migrate
```

Crear un superusuario:

```bash
python manage.py createsuperuser
```

Iniciar en desarrollo:

```bash
python manage.py runserver
```

La aplicación estará disponible en:

```text
http://127.0.0.1:8000/
```

## Ejecución con Docker Compose

El proyecto también puede levantarse mediante Docker Compose usando el archivo `.env` del proyecto.

Iniciar el entorno local:

```bash
docker compose up --build
```

O en segundo plano:

```bash
docker compose up -d --build
```

Con este arranque se levanta por defecto el servicio `web`, que ejecuta Django con Gunicorn y publica la aplicación en el puerto `8000`.

La aplicación estará disponible en:

```text
http://127.0.0.1:8000/
```

Si se quiere levantar también Nginx como proxy inverso para un escenario más cercano a producción, puede usarse el perfil `production`:

```bash
docker compose --profile production up --build
```

En ese caso, además del archivo `.env`, deben existir los certificados y rutas configuradas para HTTPS en `nginx.conf`.

## Despliegue

El proyecto está preparado para ejecutarse en producción con Gunicorn como servidor de aplicación. Los archivos estáticos se sirven mediante WhiteNoise y también existe configuración adicional para contenedores Docker.

Archivos relevantes del despliegue:

- `Procfile`: arranque del proyecto en producción.
- `Dockerfile`: imagen de la aplicación.
- `docker-compose.yml`: orquestación de servicios.
- `nginx.conf`: configuración de proxy inverso cuando se usa Nginx en contenedores.

## Estructura del proyecto

```text
poketrip/          Configuración principal del proyecto Django
accounts/          Autenticación, registro y perfil de usuario
trips/             Viajes, itinerario, gastos, reservas, documentos e IA
templates/         Plantillas HTML compartidas
static/            Archivos estáticos globales
media/             Archivos subidos por los usuarios
```

## Documentación funcional resumida

El flujo habitual de uso de la aplicación es el siguiente:

1. El usuario crea una cuenta o inicia sesión.
2. Accede al dashboard con un resumen de sus viajes.
3. Crea un viaje indicando destino, fechas y datos generales.
4. El sistema genera automáticamente los días del viaje.
5. El usuario completa el itinerario, añade gastos, documentos y reservas.
6. Si lo desea, invita a otros usuarios a colaborar.
7. La aplicación muestra información del destino en tiempo real y ofrece ayuda mediante IA.

## Autor

Gonzalo  
Proyecto Final de Grado Superior DAW

