from django.db import models


class Professor(models.Model):
    """
    Represents a professor in the campus.
    This model will be expanded with more fields in the future.
    """

    name = models.CharField(
        max_length=200,
        verbose_name="Professor Name",
        help_text="Full name of the professor",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Professor"
        verbose_name_plural = "Professors"

    def __str__(self):
        return self.name
