from collections import defaultdict


def add_semesters(semester_str, n):
    """Add n semesters to a semester string of the form 'YYYY.H' (H=1 or 2)."""
    year, half = map(int, semester_str.split('.'))
    total_halves = (year * 2 + half - 1) + n
    new_year = total_halves // 2
    new_half = total_halves % 2 + 1
    return f"{new_year}.{new_half}"


def semester_range(start, end):
    """Return ordered list of semester strings from start to end (inclusive)."""
    result = []
    current = start
    while current <= end:
        result.append(current)
        year, half = map(int, current.split('.'))
        if half == 1:
            current = f"{year}.2"
        else:
            current = f"{year + 1}.1"
    return result


def get_projection(course_filter=None, start_semester=None, end_semester=None, main_area=None):
    """
    Build a projection of academic workload across semesters.

    Returns a dict keyed by semester string. Each value is a dict:
      {
        'entries': [
            {
              'discipline': <Discipline>,
              'count': <int>,
              'regular_count': <int>,
              'extra_count': <int>,
              'source_entries': [<ClassEntry>, ...],
              'credits_total': <int>,
              'ch_total': <int>,
            },
            ...
        ],
        'elective_slots': [
            {
              'period': <str>,
              'slot': <CourseElectiveSlot>,
              'count': <int>,
              'credits_per': <int>,
              'ch_per': <int>,
              'credits_total': <int>,
              'ch_total': <int>,
              'source_entries': [<ClassEntry>, ...],
            },
            ...
        ],
        'total_credits': <int>,
        'total_ch': <int>,
        'total_classes': <int>,
      }
    """
    from .models import ClassEntry, ExtraClass
    from courses.models import Discipline

    semester_data = defaultdict(lambda: defaultdict(lambda: {
        'discipline': None,
        'regular_count': 0,
        'extra_count': 0,
        'source_entries': [],
    }))

    # key: (semester, course_pk, period) -> elective aggregation
    elective_data = defaultdict(lambda: {
        'slot': None,
        'count': 0,
        'source_entries': [],
    })

    # --- Regular entries from ClassEntry ---
    entries_qs = ClassEntry.objects.filter(is_active=True).select_related('course')
    if course_filter:
        entries_qs = entries_qs.filter(course=course_filter)

    for entry in entries_qs:
        disciplines_qs = (
            Discipline.objects
            .filter(course=entry.course, is_elective=False)
            .exclude(period='0')
            .select_related('course')
            .order_by('period', 'name')
        )
        if main_area:
            disciplines_qs = disciplines_qs.filter(main_area=main_area)
        disciplines = disciplines_qs
        for disc in disciplines:
            period_num = int(disc.period)
            target_sem = entry.get_semester_for_period(period_num)
            if start_semester and target_sem < start_semester:
                continue
            if end_semester and target_sem > end_semester:
                continue
            row = semester_data[target_sem][disc.pk]
            row['discipline'] = disc
            row['regular_count'] += 1
            row['source_entries'].append(entry)

        # --- Elective slots configured for this course ---
        for slot in entry.course.elective_slots.all():
            period_num = int(slot.period)
            target_sem = entry.get_semester_for_period(period_num)
            if start_semester and target_sem < start_semester:
                continue
            if end_semester and target_sem > end_semester:
                continue
            key = (target_sem, entry.course.pk, slot.period)
            elective_data[key]['slot'] = slot
            elective_data[key]['count'] += slot.count
            elective_data[key]['source_entries'].append(entry)

    # --- Extra classes ---
    extras_qs = ExtraClass.objects.all().select_related('discipline', 'course')
    if course_filter:
        extras_qs = extras_qs.filter(course=course_filter)

    for extra in extras_qs:
        sem = extra.semester
        if start_semester and sem < start_semester:
            continue
        if end_semester and sem > end_semester:
            continue
        row = semester_data[sem][extra.discipline.pk]
        if row['discipline'] is None:
            row['discipline'] = extra.discipline
        row['extra_count'] += extra.extra_count

    # Collect all semesters (regular + elective)
    all_semesters = set(semester_data.keys()) | {k[0] for k in elective_data.keys()}

    result = {}
    for sem in sorted(all_semesters):
        entries = []
        total_credits = 0
        total_ch = 0
        total_classes = 0

        for disc_data in semester_data[sem].values():
            disc = disc_data['discipline']
            if disc is None:
                continue
            count = disc_data['regular_count'] + disc_data['extra_count']
            entries.append({
                'discipline': disc,
                'count': count,
                'regular_count': disc_data['regular_count'],
                'extra_count': disc_data['extra_count'],
                'source_entries': disc_data['source_entries'],
                'credits_total': disc.credits * count,
                'ch_total': disc.ch_relogio * count,
            })
            total_credits += disc.credits * count
            total_ch += disc.ch_relogio * count
            total_classes += count

        # Build elective_slots list for this semester
        elective_slots = []
        for (e_sem, _course_pk, period), edata in sorted(
            elective_data.items(), key=lambda x: x[0][2]
        ):
            if e_sem != sem:
                continue
            slot = edata['slot']
            count = edata['count']
            credits_total = slot.credits * count
            ch_total = slot.ch_relogio * count
            elective_slots.append({
                'period': period,
                'slot': slot,
                'count': count,
                'credits_per': slot.credits,
                'ch_per': slot.ch_relogio,
                'credits_total': credits_total,
                'ch_total': ch_total,
                'source_entries': edata['source_entries'],
            })
            total_credits += credits_total
            total_ch += ch_total
            total_classes += count

        result[sem] = {
            'entries': entries,
            'elective_slots': elective_slots,
            'total_credits': total_credits,
            'total_ch': total_ch,
            'total_classes': total_classes,
        }
    return result
