from django.db import models


class WorkloadNorm(models.Model):
    """
    Represents a teaching workload normalization document (e.g., Resolução CONSUP/IFPE nº 8/2020).
    Stores the min/max weekly class limits per work group, contract type, and class duration.
    """

    name = models.CharField(
        max_length=200,
        verbose_name="Nome",
        help_text='Nome do documento (ex: "Resolução CONSUP/IFPE nº 8/2020")',
    )
    resolution_number = models.CharField(
        max_length=50,
        verbose_name="Número da Resolução",
        help_text='Número identificador (ex: "8/2020")',
    )
    effective_date = models.DateField(
        verbose_name="Data de Vigência",
    )
    is_active = models.BooleanField(
        default=False,
        verbose_name="Ativa",
        help_text="Somente uma normatização deve estar ativa por vez",
    )
    notes = models.TextField(blank=True, verbose_name="Observações")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-effective_date"]
        verbose_name = "Normatização Docente"
        verbose_name_plural = "Normatizações Docentes"

    def __str__(self):
        active = " [ATIVA]" if self.is_active else ""
        return f"{self.name}{active}"

    def save(self, *args, **kwargs):
        """Ensure only one active norm at a time."""
        if self.is_active:
            WorkloadNorm.objects.exclude(pk=self.pk).filter(is_active=True).update(is_active=False)
        super().save(*args, **kwargs)


class WorkloadNormEntry(models.Model):
    """
    A single row of the workload table from a normalization document.
    Defines min/max weekly classes for a work group, contract type, and class duration.
    """

    CONTRACT_40H_DE = "40h_DE"
    CONTRACT_20H = "20h"
    CONTRACT_CHOICES = [
        (CONTRACT_40H_DE, "40h / DE"),
        (CONTRACT_20H, "20h"),
    ]

    CLASS_DURATION_45 = 45
    CLASS_DURATION_50 = 50
    CLASS_DURATION_60 = 60
    CLASS_DURATION_CHOICES = [
        (CLASS_DURATION_45, "45 min"),
        (CLASS_DURATION_50, "50 min"),
        (CLASS_DURATION_60, "60 min"),
    ]

    GROUP_CHOICES = [
        ("I",   "Grupo I"),
        ("II",  "Grupo II"),
        ("III", "Grupo III"),
        ("IV",  "Grupo IV"),
        ("V",   "Grupo V"),
        ("VI",  "Grupo VI"),
    ]

    norm = models.ForeignKey(
        WorkloadNorm,
        on_delete=models.CASCADE,
        related_name="entries",
        verbose_name="Normatização",
    )
    work_group = models.CharField(
        max_length=5,
        choices=GROUP_CHOICES,
        verbose_name="Grupo",
    )
    contract_type = models.CharField(
        max_length=10,
        choices=CONTRACT_CHOICES,
        verbose_name="Regime",
    )
    class_duration = models.IntegerField(
        choices=CLASS_DURATION_CHOICES,
        verbose_name="Tempo de Aula (min)",
    )
    min_classes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Mín. Aulas/Semana",
        help_text="Nulo = N/A para esta combinação",
    )
    max_classes = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="Máx. Aulas/Semana",
    )

    class Meta:
        ordering = ["work_group", "contract_type", "class_duration"]
        unique_together = ["norm", "work_group", "contract_type", "class_duration"]
        verbose_name = "Entrada de Normatização"
        verbose_name_plural = "Entradas de Normatização"

    def __str__(self):
        limits = (
            f"{self.min_classes}–{self.max_classes}"
            if self.min_classes is not None
            else "N/A"
        )
        return f"Grupo {self.work_group} · {self.get_contract_type_display()} · {self.class_duration}min → {limits} aulas/sem"


class Professor(models.Model):
    """
    Represents a professor in the campus.
    """

    GROUP_CHOICES = [
        ("I",   "Grupo I"),
        ("II",  "Grupo II"),
        ("III", "Grupo III"),
        ("IV",  "Grupo IV"),
        ("V",   "Grupo V"),
        ("VI",  "Grupo VI"),
    ]

    CONTRACT_DE = "DE"
    CONTRACT_40H = "40h"
    CONTRACT_20H = "20h"
    CONTRACT_CHOICES = [
        (CONTRACT_DE,  "DE — Dedicação Exclusiva"),
        (CONTRACT_40H, "40h"),
        (CONTRACT_20H, "20h"),
    ]

    name = models.CharField(
        max_length=200,
        verbose_name="Nome",
        help_text="Nome completo do professor",
    )
    work_group = models.CharField(
        max_length=5,
        choices=GROUP_CHOICES,
        blank=True,
        verbose_name="Grupo de Trabalho",
        help_text="Grupo docente conforme normatização do IFPE",
    )
    contract_type = models.CharField(
        max_length=5,
        choices=CONTRACT_CHOICES,
        blank=True,
        verbose_name="Regime de Trabalho",
        help_text="Formato do vínculo contratual",
    )
    is_on_leave = models.BooleanField(
        default=False,
        verbose_name="Afastado",
        help_text="Professor afastado não entra no cômputo da soma total de esforço",
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name="Disponível para distribuição",
        help_text="Desmarque para professores que saíram do curso. O histórico de aulas é preservado.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Professor"
        verbose_name_plural = "Professores"

    def __str__(self):
        return self.name

    def get_workload_limits(self, class_duration=45, norm=None):
        """
        Return (min_classes, max_classes) per week for this professor according
        to the active workload norm (or the given norm).
        Returns (None, None) if not applicable or data is missing.
        """
        if not self.work_group or not self.contract_type:
            return None, None

        if norm is None:
            norm = WorkloadNorm.objects.filter(is_active=True).first()
        if norm is None:
            return None, None

        # DE and 40h share the same column in the IFPE table
        lookup_type = (
            WorkloadNormEntry.CONTRACT_20H
            if self.contract_type == self.CONTRACT_20H
            else WorkloadNormEntry.CONTRACT_40H_DE
        )

        entry = norm.entries.filter(
            work_group=self.work_group,
            contract_type=lookup_type,
            class_duration=class_duration,
        ).first()

        if entry:
            return entry.min_classes, entry.max_classes
        return None, None
