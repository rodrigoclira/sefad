from django.core.management.base import BaseCommand
from planning.models import SemesterPlan, PlanDiscipline
from courses.models import Course, Discipline


class Command(BaseCommand):
    help = "Add all disciplines from a specific period to a plan"

    def add_arguments(self, parser):
        parser.add_argument("plan_id", type=int, help="ID of the semester plan")
        parser.add_argument("period", type=str, help="Period number (e.g., 1, 2, 3...)")
        parser.add_argument(
            "--classes",
            type=int,
            default=1,
            help="Number of classes for each discipline (default: 1)",
        )

    def handle(self, *args, **options):
        plan_id = options["plan_id"]
        period = options["period"]
        classes_count = options["classes"]

        try:
            plan = SemesterPlan.objects.get(pk=plan_id)
        except SemesterPlan.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"Plan with ID {plan_id} not found"))
            return

        # Get all disciplines from the specified period for this course
        disciplines = Discipline.objects.filter(course=plan.course, period=period)

        if not disciplines.exists():
            self.stdout.write(
                self.style.WARNING(
                    f"No disciplines found for period {period} in course {plan.course.name}"
                )
            )
            return

        added_count = 0
        skipped_count = 0

        for discipline in disciplines:
            _, created = PlanDiscipline.objects.get_or_create(
                plan=plan,
                discipline=discipline,
                defaults={"classes_count": classes_count},
            )

            if created:
                added_count += 1
                self.stdout.write(self.style.SUCCESS(f"  Added: {discipline.name}"))
            else:
                skipped_count += 1
                self.stdout.write(f"  Already exists: {discipline.name}")

        self.stdout.write(
            self.style.SUCCESS(
                f"\nCompleted:\n"
                f"  - {added_count} discipline(s) added\n"
                f"  - {skipped_count} discipline(s) already in plan\n"
                f"  Total credits: {plan.get_total_credits()}\n"
                f"  Total CH Relógio: {plan.get_total_ch_relogio()}h"
            )
        )
