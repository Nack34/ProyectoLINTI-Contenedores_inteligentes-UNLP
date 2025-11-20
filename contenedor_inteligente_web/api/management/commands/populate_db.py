# en api/management/commands/populate_db.py

import random
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.db import transaction

# Importá tus modelos
from api.models import Residuo, TipoResiduo, Estacion

class Command(BaseCommand):
    help = 'Puebla la base de datos con datos de ejemplo para testeo.'

    @transaction.atomic  # Usamos una transacción para que todo se ejecute o nada
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Limpiando la base de datos...'))
        
        # Opcional: Limpiar datos antiguos para no duplicar
        Residuo.objects.all().delete()
        Estacion.objects.all().delete()
        User.objects.filter(is_superuser=False).delete()
        # No borramos TipoResiduo porque son datos fijos

        self.stdout.write(self.style.SUCCESS('Creando datos de ejemplo...'))

        # --- 1. Crear Tipos de Residuo (usamos get_or_create) ---
        tipos_con_puntos = [
            ('Carton', 10),
            ('Vidrio', 15),
            ('Metal', 20),
            ('Papel', 10),
            ('Plastico', 15),
            ('Basura', 0)
        ]
        
        tipos_objetos = {}
        for nombre, puntos in tipos_con_puntos:
            # get_or_create evita crear duplicados si ya existen
            tipo, created = TipoResiduo.objects.get_or_create(
                nombre=nombre,
                defaults={'puntos': puntos}
            )
            tipos_objetos[nombre] = tipo
            if created:
                self.stdout.write(f'  - Creado TipoResiduo: {nombre}')

        # --- 2. Crear Estaciones de Ejemplo ---
        estacion1, _ = Estacion.objects.get_or_create(
            nombre='Estación Informática',
            latitud=-34.9130,
            longitud=-57.9495
        )
        estacion2, _ = Estacion.objects.get_or_create(
            nombre='Estación Bellas Artes',
            latitud=-34.9150,
            longitud=-57.9510
        )
        self.stdout.write(f'  - Creadas 2 estaciones de ejemplo.')

        # --- 3. Crear Usuarios de Ejemplo ---
        user1, _ = User.objects.get_or_create(username='usuario_prueba_1')
        user1.set_password('pass123')
        user1.save()

        user2, _ = User.objects.get_or_create(username='usuario_prueba_2')
        user2.set_password('pass123')
        user2.save()
        self.stdout.write(f'  - Creados 2 usuarios de ejemplo.')
        
        # Lista de usuarios y tipos para elegir al azar
        usuarios = [user1, user2]
        tipos_lista = list(tipos_objetos.values())

        # --- 4. Crear Residuos de Ejemplo ---
        residuos_a_crear = []
        for _ in range(100): # Creamos 100 residuos de ejemplo
            residuo = Residuo(
                user=random.choice(usuarios),
                tipo_residuo=random.choice(tipos_lista),
                fecha_carga=datetime.now() - timedelta(days=random.randint(0, 30))
            )
            residuos_a_crear.append(residuo)
        
        # bulk_create es mucho más rápido que .create() en un loop
        Residuo.objects.bulk_create(residuos_a_crear)
        self.stdout.write(f'  - Creados 100 residuos de ejemplo.')

        self.stdout.write(self.style.SUCCESS('¡Base de datos poblada exitosamente! ✅'))