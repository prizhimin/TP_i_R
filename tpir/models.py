from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.cache import cache
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError
from commondata.models import Department
from django.db.models import Prefetch
import os


def tpir_files_directory_path(instance, filename):
    """Генерирует путь для сохранения прикрепленных файлов"""
    return f'tpir_files/{instance.tpir.id}/{filename}'


class TpirFacility(models.Model):
    """Модель объекта/сооружения"""
    name = models.CharField(max_length=100, verbose_name="Название объекта")
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name="Филиал")
    is_active = models.BooleanField(default=True, verbose_name="Активен")

    class Meta:
        ordering = ['name']
        verbose_name = 'Объект'
        verbose_name_plural = 'Объекты'
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'department'],
                name='tpir_unique_facility_name_in_department',
                violation_error_message="Объект с таким названием уже существует в этом филиале"
            )
        ]

    def __str__(self):
        return f"{self.name} ({self.department})"

    @classmethod
    def bulk_update_status(cls, facility_ids, is_active):
        """Массовое обновление статуса объектов"""
        return cls.objects.filter(id__in=facility_ids).update(is_active=is_active)

    def save(self, *args, **kwargs):
        cache.delete(f'tpir_facility_{self.id}_reports')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        cache.delete(f'tpir_facility_{self.id}_reports')
        super().delete(*args, **kwargs)


class Tpir(models.Model):
    """Основная модель отчетов ТПИР"""

    DANGER_CATEGORY = [
        ('none', 'Нет'),
        ('low', 'Низкая'),
        ('medium', 'Средняя'),
        ('high', 'Высокая'),
    ]

    TYPE_TPIR = [
        ('none', ''),
        ('PIR', 'ПИР'),
        ('SMR', 'СМР'),
        ('PIRSMR', 'ПИР/СМР'),
    ]

    # Связи с другими моделями
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='tpir_created_reports',
        verbose_name="Создатель отчёта"
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.CASCADE,
        verbose_name="Филиал"
    )
    facility = models.ForeignKey(
        TpirFacility,
        on_delete=models.CASCADE,
        verbose_name="Объект"
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='tpir_updated_reports',
        verbose_name="Кто изменил"
    )

    # Основные поля
    directive_number = models.CharField(
        verbose_name="№ предписания",
        max_length=100,
        default='',
        db_index=True
    )
    directive_date = models.DateField(verbose_name="Дата выдачи предписания")
    directive_end_date = models.DateField(verbose_name="Срок устранения нарушений")
    danger = models.CharField(
        verbose_name='Категория опасности',
        max_length=10,
        choices=DANGER_CATEGORY,
        default='none'
    )
    type_tpir = models.CharField(
        verbose_name="Вид",
        max_length=10,
        choices=TYPE_TPIR,
        default='none'
    )
    remedial_action = models.CharField(
        verbose_name="Наименование мероприятия",
        max_length=250,
        default=''
    )
    directive_executive = models.CharField(
        verbose_name="Орган исполнительной власти",
        max_length=250,
        default=''
    )
    existing_shortcomings = models.CharField(
        verbose_name="Имеющиеся недостатки",
        max_length=1800,
        default='',
        blank=True
    )
    created_at = models.DateTimeField(default=timezone.now, verbose_name="Время создания")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Время изменения")

    class Meta:
        verbose_name = 'Отчёт ТПИР'
        verbose_name_plural = 'Отчёты ТПИР'
        ordering = ['-directive_date', 'facility']
        indexes = [
            models.Index(fields=['directive_number']),
            models.Index(fields=['directive_date', 'directive_end_date']),
        ]

    def __str__(self):
        return f"{self.department.name} - {self.facility} [#{self.directive_number}]"

    @classmethod
    def get_queryset_with_optimizations(cls):
        """Оптимизированный QuerySet для уменьшения количества запросов"""
        return cls.objects.select_related(
            'department',
            'facility',
            'created_by',
            'updated_by'
        ).prefetch_related(
            Prefetch(
                'attached_files',
                queryset=TpirAttachedFile.objects.only('id', 'file', 'uploaded_at')
            ),
            Prefetch(
                'finance_records',
                queryset=TpirFinance.objects.only('id', 'year', 'amount')
            )
        )

    def clean(self):
        """Валидация дат"""
        if self.directive_end_date and self.directive_date:
            if self.directive_end_date < self.directive_date:
                raise ValidationError({
                    'directive_end_date': "Срок устранения не может быть раньше даты предписания"
                })
        super().clean()

    def has_attachments(self):
        """Проверка наличия вложений с кэшированием"""
        cache_key = f'tpir_{self.id}_has_attachments'
        has_attachments = cache.get(cache_key)

        if has_attachments is None:
            if hasattr(self, '_prefetched_objects_cache') and 'attached_files' in self._prefetched_objects_cache:
                has_attachments = bool(self._prefetched_objects_cache['attached_files'])
            else:
                has_attachments = self.attached_files.exists()
            cache.set(cache_key, has_attachments)

        return has_attachments

    def get_finance_years(self):
        """Получение лет с финансовыми данными с кэшированием"""
        cache_key = f'tpir_{self.id}_finance_years'
        years = cache.get(cache_key)

        if years is None:
            if hasattr(self, '_prefetched_objects_cache') and 'finance_records' in self._prefetched_objects_cache:
                years = tuple(r.year for r in self._prefetched_objects_cache['finance_records'])
            else:
                years = tuple(self.finance_records.only('year').values_list('year', flat=True).order_by('year'))
            cache.set(cache_key, years)

        return years

    def save(self, *args, **kwargs):
        """Очистка кэша при сохранении"""
        cache_keys = [
            f'tpir_{self.id}_has_attachments',
            f'tpir_{self.id}_finance_years',
            f'tpir_facility_{self.facility_id}_reports'
        ]
        cache.delete_many([k for k in cache_keys if k])
        super().save(*args, **kwargs)


class TpirAttachedFile(models.Model):
    """Модель прикрепленных файлов"""
    tpir = models.ForeignKey(
        Tpir,
        related_name='attached_files',
        on_delete=models.CASCADE,
        db_index=True
    )
    file = models.FileField(
        upload_to=tpir_files_directory_path,
        max_length=255
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return os.path.basename(self.file.name)

    @classmethod
    def bulk_create_for_report(cls, report, files_data):
        """Массовое создание файлов для отчета"""
        files = [cls(tpir=report, file=file_data['file']) for file_data in files_data]
        return cls.objects.bulk_create(files)

    def save(self, *args, **kwargs):
        cache.delete(f'tpir_{self.tpir_id}_has_attachments')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        cache.delete(f'tpir_{self.tpir_id}_has_attachments')
        super().delete(*args, **kwargs)


class TpirFinance(models.Model):
    """Финансовая информация по отчетам"""
    report = models.ForeignKey(
        Tpir,
        on_delete=models.CASCADE,
        related_name='finance_records',
        verbose_name="Отчёт ТПИР"
    )
    year = models.PositiveSmallIntegerField(
        verbose_name="Год",
        validators=[
            MinValueValidator(2025),
            MaxValueValidator(2100)
        ]
    )
    amount = models.DecimalField(
        verbose_name="Сумма",
        max_digits=12,
        decimal_places=1,
        default=0,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        verbose_name = "Финансовая запись ТПИР"
        verbose_name_plural = "Финансовые записи ТПИР"
        ordering = ['-year', 'report']
        constraints = [
            models.UniqueConstraint(
                fields=['report', 'year'],
                name='unique_finance_per_year'
            )
        ]

    def __str__(self):
        return f"{self.report} - {self.year}: {self.amount:.1f}"

    @classmethod
    def bulk_update_amounts(cls, updates):
        """Массовое обновление финансовых данных"""
        records = cls.objects.in_bulk(updates.keys())
        for record_id, amount in updates.items():
            if record_id in records:
                records[record_id].amount = amount
        return cls.objects.bulk_update(records.values(), ['amount'])

    def save(self, *args, **kwargs):
        cache.delete(f'tpir_{self.report_id}_finance_years')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        cache.delete(f'tpir_{self.report_id}_finance_years')
        super().delete(*args, **kwargs)


class TpirUserDepartment(models.Model):
    """Привязка пользователей к филиалам"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    department = models.ManyToManyField(Department)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['user'],
                name='unique_tpir_user_department'
            )
        ]

    def __str__(self):
        return f"{self.user.username}'s departments"

    @classmethod
    def bulk_update_user_departments(cls, user, department_ids):
        """Массовое обновление привязки пользователя к филиалам"""
        instance, _ = cls.objects.get_or_create(user=user)
        instance.department.set(department_ids)
        instance.save()

    def save(self, *args, **kwargs):
        if self.pk:
            old_dept_ids = set(self.department.values_list('id', flat=True))
            super().save(*args, **kwargs)
            new_dept_ids = set(self.department.values_list('id', flat=True))

            if removed_dept_ids := old_dept_ids - new_dept_ids:
                cache.delete_many([
                    f'tpir_access_u{self.user_id}_t{tpir_id}'
                    for tpir_id in Tpir.objects.filter(
                        department_id__in=removed_dept_ids
                    ).values_list('id', flat=True)
                ])
        else:
            super().save(*args, **kwargs)