"""
Data migration: populate WorkloadNorm and WorkloadNormEntry for
Resolução CONSUP/IFPE nº 8/2020 — §6º, tabela de carga horária docente.

Source: https://portal.ifpe.edu.br/wp-content/uploads/repositoriolegado/portal/
        documentos/resolucao-8-2020-aprova-a-normatizacao-do-trabalho-docente-do-ifpe.pdf

Table format: (work_group, contract_type, class_duration_min, min_classes, max_classes)
contract_type '40h_DE' covers both 40h and DE regimes (same column in the document).
Grupo VI and Grupo V/20h are N/A — no entries created for those combinations.
"""

import datetime
from django.db import migrations


NORM_DATA = {
    "name": "Resolução CONSUP/IFPE nº 8/2020",
    "resolution_number": "8/2020",
    "effective_date": datetime.date(2020, 1, 1),
}

# (group, contract_type, duration_min, min_classes, max_classes)
ENTRIES = [
    # --- 45 min (fator de conversão 0,75) ---
    ("I",   "40h_DE", 45, 14, 24),
    ("I",   "20h",    45, 11, 14),
    ("II",  "40h_DE", 45, 14, 16),
    ("II",  "20h",    45, 11, 14),
    ("III", "40h_DE", 45, 14, 16),
    ("III", "20h",    45, 11, 14),
    ("IV",  "40h_DE", 45, 14, 14),
    ("IV",  "20h",    45, 11, 11),
    ("V",   "40h_DE", 45,  3, 11),
    # --- 50 min (fator de conversão 0,83) ---
    ("I",   "40h_DE", 50, 12, 21),
    ("I",   "20h",    50, 10, 12),
    ("II",  "40h_DE", 50, 12, 15),
    ("II",  "20h",    50, 10, 12),
    ("III", "40h_DE", 50, 12, 15),
    ("III", "20h",    50, 10, 12),
    ("IV",  "40h_DE", 50, 12, 12),
    ("IV",  "20h",    50, 10, 10),
    ("V",   "40h_DE", 50,  3, 10),
    # --- 60 min (fator de conversão 1,0) ---
    ("I",   "40h_DE", 60, 10, 18),
    ("I",   "20h",    60,  8, 10),
    ("II",  "40h_DE", 60, 10, 12),
    ("II",  "20h",    60,  8, 10),
    ("III", "40h_DE", 60, 10, 12),
    ("III", "20h",    60,  8, 10),
    ("IV",  "40h_DE", 60, 10, 10),
    ("IV",  "20h",    60,  8,  8),
    ("V",   "40h_DE", 60,  2,  8),
]


def populate(apps, schema_editor):
    WorkloadNorm = apps.get_model("professors", "WorkloadNorm")
    WorkloadNormEntry = apps.get_model("professors", "WorkloadNormEntry")

    norm = WorkloadNorm.objects.create(
        name=NORM_DATA["name"],
        resolution_number=NORM_DATA["resolution_number"],
        effective_date=NORM_DATA["effective_date"],
        is_active=True,
    )

    for group, contract, duration, min_c, max_c in ENTRIES:
        WorkloadNormEntry.objects.create(
            norm=norm,
            work_group=group,
            contract_type=contract,
            class_duration=duration,
            min_classes=min_c,
            max_classes=max_c,
        )


def depopulate(apps, schema_editor):
    WorkloadNorm = apps.get_model("professors", "WorkloadNorm")
    WorkloadNorm.objects.filter(resolution_number="8/2020").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("professors", "0002_workloadnorm_alter_professor_options_and_more"),
    ]

    operations = [
        migrations.RunPython(populate, depopulate),
    ]
