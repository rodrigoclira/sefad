import csv
import os
from django.core.management.base import BaseCommand
from courses.models import Course, Discipline


class Command(BaseCommand):
    help = "Import course data from CSV file"

    def add_arguments(self, parser):
        parser.add_argument("csv_file", type=str, help="Path to the CSV file to import")
        parser.add_argument(
            "--clear", action="store_true", help="Clear existing data before importing"
        )

    def infer_main_area(self, discipline_name):
        """
        Infer the main area from discipline name.
        Returns 'computação' for CS-related disciplines, 'other' otherwise.
        """
        discipline_lower = discipline_name.lower()

        # CS-related keywords
        cs_keywords = [
            "programação",
            "software",
            "sistemas",
            "algoritmo",
            "dados",
            "computador",
            "informática",
            "web",
            "mobile",
            "redes",
            "banco de dados",
            "inteligência artificial",
            "ia",
            "machine learning",
            "arquitetura",
            "engenharia de software",
            "teste",
            "teste de software",
            "segurança",
            "desenvolvimento",
            "java",
            "python",
            "tecnologia",
            "tic",
            "eletrônica",
            "embarcado",
            "operacional",
            "distribuído",
            "ciência dos dados",
            "mineração",
            "jogos",
            "ergonomia de software",
        ]

        for keyword in cs_keywords:
            if keyword in discipline_lower:
                return "computação"

        return "other"

    def handle(self, *args, **options):
        csv_file = options["csv_file"]

        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f"File not found: {csv_file}"))
            return

        if options["clear"]:
            self.stdout.write(self.style.WARNING("Clearing existing data..."))
            Discipline.objects.all().delete()
            Course.objects.all().delete()
            self.stdout.write(self.style.SUCCESS("Data cleared."))

        # Read CSV and collect course information
        courses_data = {}
        disciplines_data = []

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                course_name = row["nome_curso"]
                grade_year = row["ano_perfil"]
                course_key = f"{course_name}_{grade_year}"

                if course_key not in courses_data:
                    courses_data[course_key] = {
                        "name": course_name,
                        "grade_year": grade_year,
                    }

                disciplines_data.append(row)

        # Create courses
        self.stdout.write("Creating courses...")
        courses = {}
        for course_key, course_data in courses_data.items():
            course, created = Course.objects.get_or_create(
                name=course_data["name"],
                grade_year=course_data["grade_year"],
                defaults={
                    "calendar_type": Course.CALENDAR_SEMESTRAL,
                },
            )
            courses[course_key] = course
            if created:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"  Created course: {course.name} ({course.grade_year})"
                    )
                )
            else:
                self.stdout.write(
                    f"  Course already exists: {course.name} ({course.grade_year})"
                )

        # Create disciplines
        self.stdout.write("Creating disciplines...")
        created_count = 0
        updated_count = 0

        for row in disciplines_data:
            course_key = f"{row['nome_curso']}_{row['ano_perfil']}"
            course = courses[course_key]

            discipline_name = row["disciplina"]
            period = row["modulo"]
            credits = int(row["creditos"]) if row["creditos"] else 0
            ch_aula = int(row["ch_aula"]) if row["ch_aula"] else 0
            ch_relogio = int(row["ch_relogio"]) if row["ch_relogio"] else 0
            pre_requisito = row["pre_requisito"].strip() if row["pre_requisito"] else ""
            co_requisito = row["co_requisito"].strip() if row["co_requisito"] else ""

            # Infer main area
            main_area = self.infer_main_area(discipline_name)

            discipline, created = Discipline.objects.update_or_create(
                course=course,
                name=discipline_name,
                period=period,
                defaults={
                    "main_area": main_area,
                    "credits": credits,
                    "ch_aula": ch_aula,
                    "ch_relogio": ch_relogio,
                    "pre_requisito": pre_requisito,
                    "co_requisito": co_requisito,
                },
            )

            if created:
                created_count += 1
            else:
                updated_count += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\nImport completed:\n"
                f"  - {len(courses)} course(s)\n"
                f"  - {created_count} discipline(s) created\n"
                f"  - {updated_count} discipline(s) updated"
            )
        )
