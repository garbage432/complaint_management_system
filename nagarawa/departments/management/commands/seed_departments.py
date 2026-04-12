from django.core.management.base import BaseCommand
from departments.models import Department


DEPARTMENTS = [
    {'name': 'Water Supply', 'slug': 'water-supply', 'icon': '💧', 'color': '#3B82F6', 'description': 'Water supply, tap water issues, pipe leaks, water quality'},
    {'name': 'Roads & Transport', 'slug': 'roads-transport', 'icon': '🛣️', 'color': '#F59E0B', 'description': 'Road damage, potholes, traffic, public transport'},
    {'name': 'Electricity', 'slug': 'electricity', 'icon': '⚡', 'color': '#EAB308', 'description': 'Power outages, electrical hazards, billing issues'},
    {'name': 'Waste Management', 'slug': 'waste-management', 'icon': '🗑️', 'color': '#10B981', 'description': 'Garbage collection, illegal dumping, sanitation'},
    {'name': 'Health', 'slug': 'health', 'icon': '🏥', 'color': '#EF4444', 'description': 'Public health, hospitals, sanitation, disease outbreaks'},
    {'name': 'Education', 'slug': 'education', 'icon': '🎓', 'color': '#8B5CF6', 'description': 'Schools, teachers, educational facilities'},
    {'name': 'Land & Housing', 'slug': 'land-housing', 'icon': '🏠', 'color': '#6366F1', 'description': 'Land disputes, illegal construction, housing issues'},
    {'name': 'Forest & Environment', 'slug': 'environment', 'icon': '🌿', 'color': '#059669', 'description': 'Environmental pollution, deforestation, wildlife'},
    {'name': 'Police & Security', 'slug': 'police-security', 'icon': '🚔', 'color': '#1E40AF', 'description': 'Public safety, crime, illegal activities'},
    {'name': 'Agriculture', 'slug': 'agriculture', 'icon': '🌾', 'color': '#78350F', 'description': 'Farming support, pesticides, irrigation, subsidies'},
]


class Command(BaseCommand):
    help = 'Seed initial departments'

    def handle(self, *args, **kwargs):
        created = 0
        for dept_data in DEPARTMENTS:
            obj, was_created = Department.objects.get_or_create(
                slug=dept_data['slug'],
                defaults=dept_data
            )
            if was_created:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'  Created: {obj.name}'))
            else:
                self.stdout.write(f'  Exists: {obj.name}')
        self.stdout.write(self.style.SUCCESS(f'\nDone. {created} departments created.'))
