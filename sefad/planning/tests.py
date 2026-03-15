from django.test import TestCase, Client
from django.urls import reverse
from django.core.exceptions import ValidationError

from courses.models import Course, Discipline, CourseElectiveSlot
from .models import ClassEntry, ExtraClass, SemesterPlan, PlanDiscipline
from .utils import add_semesters, semester_range, get_projection


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_course(name="ADS", calendar_type=Course.CALENDAR_SEMESTRAL):
    return Course.objects.create(name=name, calendar_type=calendar_type)


def make_discipline(course, name, period, credits=4, ch_relogio=60, is_elective=False):
    return Discipline.objects.create(
        course=course,
        name=name,
        period=period,
        main_area="Computação",
        credits=credits,
        ch_relogio=ch_relogio,
        is_elective=is_elective,
    )


# ===========================================================================
# utils.py
# ===========================================================================

class AddSemestersTest(TestCase):

    def test_add_zero(self):
        self.assertEqual(add_semesters("2026.1", 0), "2026.1")

    def test_add_one_from_first_half(self):
        self.assertEqual(add_semesters("2026.1", 1), "2026.2")

    def test_add_one_from_second_half(self):
        self.assertEqual(add_semesters("2026.2", 1), "2027.1")

    def test_add_two_from_first_half(self):
        self.assertEqual(add_semesters("2026.1", 2), "2027.1")

    def test_add_five_from_first_half(self):
        # 2026.1 + 5 → 2028.2
        self.assertEqual(add_semesters("2026.1", 5), "2028.2")

    def test_ads_full_course_progression(self):
        """A 6-period semestral course starting 2026.1 ends at 2028.2."""
        start = "2026.1"
        expected = ["2026.1", "2026.2", "2027.1", "2027.2", "2028.1", "2028.2"]
        result = [add_semesters(start, i) for i in range(6)]
        self.assertEqual(result, expected)

    def test_year_boundary(self):
        self.assertEqual(add_semesters("2025.2", 1), "2026.1")

    def test_large_offset(self):
        self.assertEqual(add_semesters("2020.1", 10), "2025.1")


class SemesterRangeTest(TestCase):

    def test_single_semester(self):
        self.assertEqual(semester_range("2026.1", "2026.1"), ["2026.1"])

    def test_same_year(self):
        self.assertEqual(semester_range("2026.1", "2026.2"), ["2026.1", "2026.2"])

    def test_two_years(self):
        result = semester_range("2026.1", "2027.2")
        self.assertEqual(result, ["2026.1", "2026.2", "2027.1", "2027.2"])

    def test_empty_when_start_after_end(self):
        self.assertEqual(semester_range("2027.1", "2026.2"), [])

    def test_three_years(self):
        result = semester_range("2026.1", "2028.2")
        self.assertEqual(len(result), 6)
        self.assertEqual(result[0], "2026.1")
        self.assertEqual(result[-1], "2028.2")


# ===========================================================================
# ClassEntry model
# ===========================================================================

class ClassEntryModelTest(TestCase):

    def setUp(self):
        self.course = make_course()

    def test_str_without_label(self):
        entry = ClassEntry(course=self.course, start_semester="2026.1")
        self.assertIn("ADS", str(entry))
        self.assertIn("2026.1", str(entry))

    def test_str_with_label(self):
        entry = ClassEntry(course=self.course, start_semester="2026.1", label="Turma A")
        self.assertIn("Turma A", str(entry))

    def test_get_semester_for_period_semestral(self):
        entry = ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        self.assertEqual(entry.get_semester_for_period(1), "2026.1")
        self.assertEqual(entry.get_semester_for_period(2), "2026.2")
        self.assertEqual(entry.get_semester_for_period(3), "2027.1")
        self.assertEqual(entry.get_semester_for_period(6), "2028.2")

    def test_get_semester_for_period_yearly(self):
        yearly_course = make_course("Eng", calendar_type=Course.CALENDAR_YEARLY)
        entry = ClassEntry.objects.create(course=yearly_course, start_semester="2026.1")
        # Yearly: period 1 → offset 0, period 2 → offset 2, period 3 → offset 4
        self.assertEqual(entry.get_semester_for_period(1), "2026.1")
        self.assertEqual(entry.get_semester_for_period(2), "2027.1")
        self.assertEqual(entry.get_semester_for_period(3), "2028.1")

    def test_invalid_semester_format(self):
        entry = ClassEntry(
            course=self.course,
            start_semester="26.1",  # invalid
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_invalid_semester_half(self):
        entry = ClassEntry(
            course=self.course,
            start_semester="2026.3",  # only .1 or .2 are valid
        )
        with self.assertRaises(ValidationError):
            entry.full_clean()

    def test_default_is_active(self):
        entry = ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        self.assertTrue(entry.is_active)

    def test_inactive_entry_created(self):
        entry = ClassEntry.objects.create(
            course=self.course, start_semester="2026.1", is_active=False
        )
        self.assertFalse(entry.is_active)

    def test_ordering(self):
        ClassEntry.objects.create(course=self.course, start_semester="2027.1")
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        semesters = list(ClassEntry.objects.values_list("start_semester", flat=True))
        self.assertEqual(semesters, sorted(semesters))


# ===========================================================================
# ExtraClass model
# ===========================================================================

class ExtraClassModelTest(TestCase):

    def setUp(self):
        self.course = make_course()
        self.disc = make_discipline(self.course, "Algoritmos", "1")

    def test_str_single(self):
        extra = ExtraClass(course=self.course, discipline=self.disc, semester="2026.1", extra_count=1)
        s = str(extra)
        self.assertIn("Algoritmos", s)
        self.assertIn("2026.1", s)
        self.assertNotIn("2x", s)

    def test_str_multiple(self):
        extra = ExtraClass(course=self.course, discipline=self.disc, semester="2026.1", extra_count=2)
        self.assertIn("2x", str(extra))

    def test_unique_together(self):
        ExtraClass.objects.create(
            course=self.course, discipline=self.disc, semester="2026.1", extra_count=1
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            ExtraClass.objects.create(
                course=self.course, discipline=self.disc, semester="2026.1", extra_count=1
            )

    def test_invalid_semester_format(self):
        extra = ExtraClass(
            course=self.course,
            discipline=self.disc,
            semester="invalid",
            extra_count=1,
        )
        with self.assertRaises(ValidationError):
            extra.full_clean()


# ===========================================================================
# get_projection utility
# ===========================================================================

class GetProjectionTest(TestCase):

    def setUp(self):
        self.course = make_course()
        self.d1 = make_discipline(self.course, "Algoritmos", "1", credits=4, ch_relogio=60)
        self.d2 = make_discipline(self.course, "Cálculo", "2", credits=4, ch_relogio=60)
        self.d3 = make_discipline(self.course, "BD", "3", credits=4, ch_relogio=60)
        # Elective — should NOT appear in regular projection
        self.elective = make_discipline(
            self.course, "Tópicos Avançados", "0", is_elective=True
        )

    def test_empty_when_no_entries(self):
        result = get_projection()
        self.assertEqual(result, {})

    def test_single_entry_three_periods(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()

        self.assertIn("2026.1", result)
        self.assertIn("2026.2", result)
        self.assertIn("2027.1", result)

    def test_period_mapping(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()

        # Period 1 → 2026.1
        disc_names_2026_1 = [e["discipline"].name for e in result["2026.1"]["entries"]]
        self.assertIn("Algoritmos", disc_names_2026_1)

        # Period 2 → 2026.2
        disc_names_2026_2 = [e["discipline"].name for e in result["2026.2"]["entries"]]
        self.assertIn("Cálculo", disc_names_2026_2)

        # Period 3 → 2027.1
        disc_names_2027_1 = [e["discipline"].name for e in result["2027.1"]["entries"]]
        self.assertIn("BD", disc_names_2027_1)

    def test_elective_not_in_projection(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        all_disc_names = [
            e["discipline"].name
            for sem_data in result.values()
            for e in sem_data["entries"]
        ]
        self.assertNotIn("Tópicos Avançados", all_disc_names)

    def test_inactive_entry_excluded(self):
        ClassEntry.objects.create(
            course=self.course, start_semester="2026.1", is_active=False
        )
        result = get_projection()
        self.assertEqual(result, {})

    def test_two_entries_same_semester_discipline(self):
        """Two class entries that both have period-1 disciplines in 2026.1."""
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        entry = next(
            e for e in result["2026.1"]["entries"] if e["discipline"].name == "Algoritmos"
        )
        self.assertEqual(entry["regular_count"], 2)
        self.assertEqual(entry["count"], 2)

    def test_overlapping_entries(self):
        """Entry A starts 2026.1, entry B starts 2026.2. In 2026.2 both contribute."""
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        ClassEntry.objects.create(course=self.course, start_semester="2026.2")
        result = get_projection()

        # 2026.2: entry A contributes Cálculo (period 2), entry B contributes Algoritmos (period 1)
        disc_names = [e["discipline"].name for e in result["2026.2"]["entries"]]
        self.assertIn("Algoritmos", disc_names)
        self.assertIn("Cálculo", disc_names)

    def test_extra_class_added(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        ExtraClass.objects.create(
            course=self.course, discipline=self.d1, semester="2026.1", extra_count=1
        )
        result = get_projection()
        entry = next(
            e for e in result["2026.1"]["entries"] if e["discipline"].name == "Algoritmos"
        )
        self.assertEqual(entry["regular_count"], 1)
        self.assertEqual(entry["extra_count"], 1)
        self.assertEqual(entry["count"], 2)

    def test_extra_class_only_no_entry(self):
        """Extra class appears even without a matching ClassEntry."""
        ExtraClass.objects.create(
            course=self.course, discipline=self.d1, semester="2026.1", extra_count=2
        )
        result = get_projection()
        self.assertIn("2026.1", result)
        entry = result["2026.1"]["entries"][0]
        self.assertEqual(entry["discipline"].name, "Algoritmos")
        self.assertEqual(entry["extra_count"], 2)
        self.assertEqual(entry["regular_count"], 0)

    def test_totals_calculated_correctly(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        sem = result["2026.1"]
        # Only d1 (credits=4, ch_relogio=60) in 2026.1, count=1
        self.assertEqual(sem["total_credits"], 4)
        self.assertEqual(sem["total_ch"], 60)
        self.assertEqual(sem["total_classes"], 1)

    def test_filter_by_course(self):
        other_course = make_course("Other")
        make_discipline(other_course, "Math", "1")
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        ClassEntry.objects.create(course=other_course, start_semester="2026.1")

        result = get_projection(course_filter=self.course)
        all_courses = {
            e["discipline"].course_id
            for sem_data in result.values()
            for e in sem_data["entries"]
        }
        self.assertEqual(all_courses, {self.course.pk})

    def test_filter_by_start_semester(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection(start_semester="2026.2")
        self.assertNotIn("2026.1", result)
        self.assertIn("2026.2", result)

    def test_filter_by_end_semester(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection(end_semester="2026.1")
        self.assertIn("2026.1", result)
        self.assertNotIn("2026.2", result)

    def test_semesters_are_sorted(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        keys = list(result.keys())
        self.assertEqual(keys, sorted(keys))


# ===========================================================================
# CourseElectiveSlot + projeção de optativas
# ===========================================================================

class CourseElectiveSlotModelTest(TestCase):

    def setUp(self):
        self.course = make_course()

    def test_str(self):
        slot = CourseElectiveSlot(course=self.course, period="5", count=2, credits=4, ch_relogio=60)
        self.assertIn("ADS", str(slot))
        self.assertIn("5", str(slot))
        self.assertIn("2", str(slot))

    def test_unique_together(self):
        CourseElectiveSlot.objects.create(course=self.course, period="5", count=2)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            CourseElectiveSlot.objects.create(course=self.course, period="5", count=1)

    def test_ordering(self):
        CourseElectiveSlot.objects.create(course=self.course, period="6", count=2)
        CourseElectiveSlot.objects.create(course=self.course, period="5", count=2)
        periods = list(CourseElectiveSlot.objects.values_list("period", flat=True))
        self.assertEqual(periods, ["5", "6"])


class ElectiveSlotsProjectionTest(TestCase):
    """Tests for elective slots integration in get_projection."""

    def setUp(self):
        self.course = make_course()
        # Regular disciplines for periods 1-6
        for p in range(1, 7):
            make_discipline(self.course, f"Disc {p}", str(p), credits=4, ch_relogio=60)
        # Elective slots for periods 5 and 6
        CourseElectiveSlot.objects.create(
            course=self.course, period="5", count=2, credits=4, ch_relogio=60
        )
        CourseElectiveSlot.objects.create(
            course=self.course, period="6", count=2, credits=4, ch_relogio=60
        )

    def test_elective_slots_appear_in_projection(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        # Period 5 → 2028.1; period 6 → 2028.2
        self.assertIn("2028.1", result)
        self.assertIn("2028.2", result)
        self.assertEqual(len(result["2028.1"]["elective_slots"]), 1)
        self.assertEqual(len(result["2028.2"]["elective_slots"]), 1)

    def test_elective_slot_count_correct(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        slot = result["2028.1"]["elective_slots"][0]
        # 1 entry × 2 electives per period = 2
        self.assertEqual(slot["count"], 2)

    def test_elective_slot_two_entries_doubles_count(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        slot = result["2028.1"]["elective_slots"][0]
        # 2 entries × 2 electives = 4
        self.assertEqual(slot["count"], 4)

    def test_elective_totals_included_in_semester_totals(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        sem = result["2028.1"]
        # Regular disc 5: 4 credits, 60h
        # Elective slot: 2 × 4 credits = 8 credits, 2 × 60h = 120h
        self.assertEqual(sem["total_credits"], 4 + 8)
        self.assertEqual(sem["total_ch"], 60 + 120)

    def test_elective_slot_ch_and_credits_values(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        slot = result["2028.1"]["elective_slots"][0]
        self.assertEqual(slot["credits_per"], 4)
        self.assertEqual(slot["ch_per"], 60)
        self.assertEqual(slot["credits_total"], 2 * 4)
        self.assertEqual(slot["ch_total"], 2 * 60)

    def test_elective_slot_source_entries_populated(self):
        entry = ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        slot = result["2028.1"]["elective_slots"][0]
        self.assertIn(entry, slot["source_entries"])

    def test_no_elective_slots_when_no_config(self):
        CourseElectiveSlot.objects.all().delete()
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        result = get_projection()
        for sem_data in result.values():
            self.assertEqual(sem_data["elective_slots"], [])

    def test_elective_slots_filtered_by_semester_range(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        # Period 5 → 2028.1; period 6 → 2028.2. Filter end to 2027.2 → no electives.
        result = get_projection(end_semester="2027.2")
        self.assertNotIn("2028.1", result)
        self.assertNotIn("2028.2", result)

    def test_elective_slots_filtered_by_course(self):
        other_course = make_course("Other")
        for p in range(1, 4):
            make_discipline(other_course, f"Other Disc {p}", str(p))
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        ClassEntry.objects.create(course=other_course, start_semester="2026.1")
        result = get_projection(course_filter=self.course)
        # other_course has no elective slots → no elective leakage
        all_slot_periods = [
            s["period"]
            for sem_data in result.values()
            for s in sem_data["elective_slots"]
        ]
        self.assertIn("5", all_slot_periods)
        # Verify source entries all belong to self.course
        for sem_data in result.values():
            for s in sem_data["elective_slots"]:
                for src in s["source_entries"]:
                    self.assertEqual(src.course, self.course)

    def test_overlapping_entries_different_periods(self):
        """Entry A (2026.1) reaches period 5 in 2028.1; Entry B (2026.2) reaches period 5 in 2028.2."""
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        ClassEntry.objects.create(course=self.course, start_semester="2026.2")
        result = get_projection()
        # 2028.1: only entry A has period 5
        slot_2028_1 = result["2028.1"]["elective_slots"][0]
        self.assertEqual(slot_2028_1["count"], 2)
        # 2028.2: entry A (period 6) + entry B (period 5) → 2 + 2 = 4 elective slots
        total_elective_classes_2028_2 = sum(
            s["count"] for s in result["2028.2"]["elective_slots"]
        )
        self.assertEqual(total_elective_classes_2028_2, 4)


# ===========================================================================
# SemesterPlan + PlanDiscipline (existing models)
# ===========================================================================

class SemesterPlanModelTest(TestCase):

    def setUp(self):
        self.course = make_course()
        self.plan = SemesterPlan.objects.create(
            name="Plano 2026.1",
            semester="2026.1",
            course=self.course,
        )
        self.d1 = make_discipline(self.course, "Algoritmos", "1", credits=4, ch_relogio=60)
        self.d2 = make_discipline(self.course, "Cálculo", "2", credits=6, ch_relogio=90)

    def test_str(self):
        self.assertIn("Plano 2026.1", str(self.plan))

    def test_totals_empty_plan(self):
        self.assertEqual(self.plan.get_total_credits(), 0)
        self.assertEqual(self.plan.get_total_ch_relogio(), 0)
        self.assertEqual(self.plan.get_disciplines_count(), 0)
        self.assertEqual(self.plan.get_unique_disciplines_count(), 0)

    def test_totals_with_disciplines(self):
        PlanDiscipline.objects.create(plan=self.plan, discipline=self.d1, classes_count=1)
        PlanDiscipline.objects.create(plan=self.plan, discipline=self.d2, classes_count=2)
        self.assertEqual(self.plan.get_total_credits(), 4 * 1 + 6 * 2)
        self.assertEqual(self.plan.get_total_ch_relogio(), 60 * 1 + 90 * 2)
        self.assertEqual(self.plan.get_disciplines_count(), 3)
        self.assertEqual(self.plan.get_unique_disciplines_count(), 2)

    def test_plan_discipline_str_single(self):
        item = PlanDiscipline.objects.create(
            plan=self.plan, discipline=self.d1, classes_count=1
        )
        self.assertEqual(str(item), "Algoritmos")

    def test_plan_discipline_str_multiple(self):
        item = PlanDiscipline.objects.create(
            plan=self.plan, discipline=self.d1, classes_count=3
        )
        self.assertIn("3x", str(item))

    def test_plan_discipline_auto_assigns_period(self):
        item = PlanDiscipline.objects.create(plan=self.plan, discipline=self.d1)
        self.assertEqual(item.assigned_period, self.d1.period)

    def test_plan_discipline_unique_together(self):
        PlanDiscipline.objects.create(plan=self.plan, discipline=self.d1)
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            PlanDiscipline.objects.create(plan=self.plan, discipline=self.d1)


# ===========================================================================
# Views
# ===========================================================================

class ProjectionViewTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.course = make_course()
        make_discipline(self.course, "Algoritmos", "1")
        make_discipline(self.course, "Cálculo", "2")

    def test_projection_empty(self):
        response = self.client.get(reverse("planning:projection"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["has_entries"])

    def test_projection_with_entry(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        response = self.client.get(reverse("planning:projection"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["has_entries"])
        self.assertIn("2026.1", response.context["projection"])

    def test_projection_filter_by_course(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        url = reverse("planning:projection") + f"?course={self.course.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_projection_filter_semester_range(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        url = reverse("planning:projection") + "?from_semester=2026.1&to_semester=2026.2"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        proj = response.context["projection"]
        self.assertNotIn("2027.1", proj)


class ClassEntryViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.course = make_course()

    def test_list_empty(self):
        response = self.client.get(reverse("planning:entry_list"))
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["entries"], [])

    def test_list_with_entries(self):
        ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        response = self.client.get(reverse("planning:entry_list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["entries"]), 1)

    def test_create_view_get(self):
        response = self.client.get(reverse("planning:entry_create"))
        self.assertEqual(response.status_code, 200)

    def test_create_valid(self):
        response = self.client.post(reverse("planning:entry_create"), {
            "course": self.course.pk,
            "start_semester": "2026.1",
            "label": "",
            "is_active": "on",
            "notes": "",
        })
        self.assertRedirects(response, reverse("planning:entry_list"))
        self.assertEqual(ClassEntry.objects.count(), 1)

    def test_create_invalid_semester(self):
        response = self.client.post(reverse("planning:entry_create"), {
            "course": self.course.pk,
            "start_semester": "26.1",
            "label": "",
            "notes": "",
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(ClassEntry.objects.count(), 0)

    def test_edit_view_get(self):
        entry = ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        response = self.client.get(reverse("planning:entry_edit", args=[entry.pk]))
        self.assertEqual(response.status_code, 200)

    def test_edit_valid(self):
        entry = ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        response = self.client.post(reverse("planning:entry_edit", args=[entry.pk]), {
            "course": self.course.pk,
            "start_semester": "2026.2",
            "label": "Turma B",
            "is_active": "on",
            "notes": "",
        })
        self.assertRedirects(response, reverse("planning:entry_list"))
        entry.refresh_from_db()
        self.assertEqual(entry.start_semester, "2026.2")
        self.assertEqual(entry.label, "Turma B")

    def test_delete_view_get(self):
        entry = ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        response = self.client.get(reverse("planning:entry_delete", args=[entry.pk]))
        self.assertEqual(response.status_code, 200)

    def test_delete_valid(self):
        entry = ClassEntry.objects.create(course=self.course, start_semester="2026.1")
        response = self.client.post(reverse("planning:entry_delete", args=[entry.pk]))
        self.assertRedirects(response, reverse("planning:entry_list"))
        self.assertEqual(ClassEntry.objects.count(), 0)


class ExtraClassViewsTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.course = make_course()
        self.disc = make_discipline(self.course, "Algoritmos", "1")

    def test_list_empty(self):
        response = self.client.get(reverse("planning:extra_list"))
        self.assertEqual(response.status_code, 200)
        self.assertQuerySetEqual(response.context["extras"], [])

    def test_list_with_extras(self):
        ExtraClass.objects.create(
            course=self.course, discipline=self.disc, semester="2026.1", extra_count=1
        )
        response = self.client.get(reverse("planning:extra_list"))
        self.assertEqual(len(response.context["extras"]), 1)

    def test_create_view_get(self):
        response = self.client.get(reverse("planning:extra_create"))
        self.assertEqual(response.status_code, 200)

    def test_create_valid(self):
        response = self.client.post(reverse("planning:extra_create"), {
            "course": self.course.pk,
            "discipline": self.disc.pk,
            "semester": "2026.1",
            "extra_count": 1,
            "notes": "",
        })
        self.assertRedirects(response, reverse("planning:extra_list"))
        self.assertEqual(ExtraClass.objects.count(), 1)

    def test_delete_extra(self):
        extra = ExtraClass.objects.create(
            course=self.course, discipline=self.disc, semester="2026.1", extra_count=1
        )
        response = self.client.post(reverse("planning:extra_delete", args=[extra.pk]))
        self.assertRedirects(response, reverse("planning:extra_list"))
        self.assertEqual(ExtraClass.objects.count(), 0)


class DisciplinesByCourseAjaxTest(TestCase):

    def setUp(self):
        self.client = Client()
        self.course = make_course()
        self.d1 = make_discipline(self.course, "Algoritmos", "1")
        self.d2 = make_discipline(self.course, "BD", "3")

    def test_no_course_id_returns_empty(self):
        response = self.client.get(reverse("planning:disciplines_by_course"))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["disciplines"], [])

    def test_returns_disciplines_for_course(self):
        url = reverse("planning:disciplines_by_course") + f"?course_id={self.course.pk}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        names = [d["name"] for d in data["disciplines"]]
        self.assertIn("Algoritmos", names)
        self.assertIn("BD", names)

    def test_invalid_course_id_returns_empty(self):
        url = reverse("planning:disciplines_by_course") + "?course_id=99999"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["disciplines"], [])
