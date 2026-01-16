from django.core.management.base import BaseCommand
from professors.models import Professor


class Command(BaseCommand):
    help = "Add initial professors to the database"

    def handle(self, *args, **options):
        professors_list = [
            "Rodrigo Lira",
            "Rosângela Maria",
            "Ivanildo Jose",
            "Rodrigo Rocha",
            "Flávio Oliveira",
            "Anderson Queiroz",
            "Antônio Neto",
            "Bruno Cartaxo",
            "Paulo Roger",
            "Wilbert Satana",
            "Marconi Carvalho",
            "David Alain",
            "Mércio Andrade",
            "Mário Melo",
        ]

        created_count = 0
        existing_count = 0

        for name in professors_list:
            professor, created = Professor.objects.get_or_create(name=name)
            if created:
                created_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Created: {name}"))
            else:
                existing_count += 1
                self.stdout.write(f"  Already exists: {name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted:\n"
                f"  - {created_count} professor(s) created\n"
                f"  - {existing_count} professor(s) already existed"
            )
        )
