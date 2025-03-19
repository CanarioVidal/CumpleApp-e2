from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.base import ConflictingIdError
from pytz import timezone
from app.email_utils import enviar_correos_recordatorio, enviar_correos_cumpleaños
import logging

# Configurar logs para tareas
logging.basicConfig(
    filename='email_logs.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Definir la zona horaria de Uruguay (-03:55)
TZ_URUGUAY = timezone('America/Montevideo')

# Variable global para almacenar el scheduler y evitar múltiples instancias
scheduler = None  

def iniciar_tareas(app):
    """Inicializa las tareas programadas con APScheduler en la zona horaria correcta evitando duplicados."""
    global scheduler  # Usar la variable global para evitar reiniciar el scheduler cada vez que se llama esta función

    try:
        # Si el scheduler ya está corriendo, no volver a iniciarlo
        if scheduler and scheduler.running:
            logging.info("🔹 El scheduler ya está en ejecución. No se agregarán tareas nuevamente.")
            return

        # Crear el scheduler si aún no existe
        if not scheduler:
            scheduler = BackgroundScheduler(timezone=TZ_URUGUAY)

        def tarea_recordatorio():
            """Ejecuta la función de envío de recordatorios en el contexto de Flask."""
            with app.app_context():
                enviar_correos_recordatorio()

        def tarea_cumpleaños():
            """Ejecuta la función de envío de saludos en el contexto de Flask."""
            with app.app_context():
                enviar_correos_cumpleaños()

        # Obtener los IDs de tareas ya existentes
        jobs = {job.id for job in scheduler.get_jobs()}

        # Solo agregar las tareas si no existen previamente
        if 'recordatorios_diarios' not in jobs:
            scheduler.add_job(
                tarea_recordatorio,
                'cron',
                hour=19, minute=55,
                id='recordatorios_diarios',
                replace_existing=False  # Cambiado a False para evitar reemplazo
            )
            logging.info("✅ Tarea 'recordatorios_diarios' programada.")

        if 'saludos_diarios' not in jobs:
            scheduler.add_job(
                tarea_cumpleaños,
                'cron',
                hour=19, minute=55,
                id='saludos_diarios',
                replace_existing=False  # Cambiado a False para evitar reemplazo
            )
            logging.info("✅ Tarea 'saludos_diarios' programada.")

        # Iniciar el scheduler solo si no está ya en ejecución
        if not scheduler.running:
            scheduler.start()
            logging.info("🚀 Scheduler iniciado.")

        # Imprimir próximas ejecuciones en los logs
        for job in scheduler.get_jobs():
            logging.info(f"Tarea programada: {job.id} - Siguiente ejecución: {job.next_run_time}")

    except ConflictingIdError as e:
        logging.warning(f'⚠️ Intento de duplicar tareas programadas: {str(e)}')

    except Exception as e:
        logging.error(f'❌ Error al iniciar tareas programadas: {str(e)}')
