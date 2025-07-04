import os
import zipfile
from contextlib import contextmanager
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db import IntegrityError
from django.http import FileResponse, JsonResponse
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

from commondata.forms import DateForm
from .forms import TpirAttachedFileForm, TpirForm
from .models import Tpir, TpirUserDepartment, TpirFacility, TpirFinance, TpirAttachedFile


def get_date_for_report():
    return timezone.now().strftime('%d.%m.%Y')


@login_required
def load_facilities(request):
    department_id = request.GET.get('department_id')
    if not department_id:
        return JsonResponse({'error': 'Department ID is required'}, status=400)

    facilities = TpirFacility.objects.filter(
        department_id=department_id,
        is_active=True
    ).order_by('name')

    return JsonResponse({
        'facilities': render_to_string(
            'tpir/facility_options.html',
            {'items': facilities}
        )
    })


@csrf_exempt
@login_required
def add_facility(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        department_id = request.POST.get('department_id')

        if not name or not department_id:
            return JsonResponse({'error': 'Необходимо указать название и филиал'}, status=400)

        try:
            facility = TpirFacility.objects.create(
                name=name,
                department_id=department_id
            )
            facilities = TpirFacility.objects.filter(
                department_id=department_id,
                is_active=True
            ).order_by('name')

            return JsonResponse({
                'success': True,
                'facility_id': facility.id,
                'facilities': render_to_string(
                    'tpir/facility_options.html',
                    {'items': facilities}
                ),
                'selected_facility_id': facility.id
            })
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
    return JsonResponse({'error': 'Invalid request'}, status=400)


@login_required
def tpir_list(request):
    """Список отчетов ТПИР, доступных пользователю"""
    # Получаем текущего пользователя
    user = request.user

    # Получаем филиалы, доступные пользователю
    user_departments = TpirUserDepartment.objects.filter(user=user).values_list('department__id', flat=True)

    # Фильтруем отчеты по доступным филиалам
    tpir_queryset = Tpir.objects.select_related('department', 'facility', 'created_by').filter(
        department__id__in=user_departments
    ).order_by('-directive_date', 'facility__name')

    # Если форма была отправлена методом POST, обрабатываем её
    if request.method == 'POST':
        form = DateForm(request.POST)
        if form.is_valid():
            selected_date = form.cleaned_data['selected_date']
            # Фильтруем отчёты по выбранной дате
            tpir_queryset = tpir_queryset.filter(directive_date=selected_date).order_by('created_at')
    else:
        # Если форма не отправлена, создаем форму с начальной датой для отчета
        form = DateForm(initial={'selected_date': get_date_for_report()})

    # Добавляем пагинацию
    paginator = Paginator(tpir_queryset, 14)  # Показывать 14 отчетов на странице
    page_number = request.GET.get('page', 1)

    try:
        page_obj = paginator.page(page_number)
    except PageNotAnInteger:
        # Если номер страницы не является целым числом, показываем первую страницу
        page_obj = paginator.page(1)
    except EmptyPage:
        # Если номер страницы превышает количество страниц, показываем последнюю страницу
        page_obj = paginator.page(paginator.num_pages)

    context = {
        'page_obj': page_obj,  # Используем стандартное имя page_obj для пагинации
        'form': form,
    }
    return render(request, 'tpir/tpir_list.html', context)


@login_required
def tpir_add(request):
    """Добавление нового отчета ТПИР"""
    tpir = None  # Инициализируем переменную tpir как None для нового отчета

    if request.method == 'POST':
        form = TpirForm(request.POST, user=request.user)
        if form.is_valid():
            new_tpir = form.save(commit=False)
            new_tpir.created_by = request.user
            new_tpir.save()

            # Обработка финансовых данных
            for key, value in request.POST.items():
                if key.startswith('finance_year_'):
                    prefix = key.replace('finance_year_', '')
                    year = value
                    amount = request.POST.get(f'finance_amount_{prefix}', 0)

                    if year and amount:
                        TpirFinance.objects.create(
                            report=new_tpir,
                            year=year,
                            amount=amount
                        )

            messages.success(request, 'Отчет успешно добавлен')
            return redirect('tpir:tpir_detail', pk=new_tpir.id)
    else:
        form = TpirForm(user=request.user)

    context = {
        'form': form,
        'title': 'Добавление нового отчета',
        'tpir': tpir  # Передаем None для нового отчета
    }
    return render(request, 'tpir/edit_tpir.html', context)


@login_required
# def tpir_edit(request, pk):
#     """Редактирование существующего отчета ТПИР"""
#     tpir = get_object_or_404(
#         Tpir.objects.select_related(
#             'department',
#             'facility',
#             'created_by',
#             'updated_by'
#         ).prefetch_related(
#             'finance_records',
#             'attached_files'
#         ),
#         pk=pk
#     )
#
#     if request.method == 'POST':
#         form = TpirForm(request.POST, instance=tpir, user=request.user)
#         if form.is_valid():
#             updated_tpir = form.save(commit=False)
#             updated_tpir.updated_by = request.user
#             updated_tpir.save()
#
#             # Обработка финансовых данных
#             existing_finances = {str(f.id): f for f in tpir.finance_records.all()}
#             existing_years = {f.year for f in existing_finances.values()}
#
#             for key, value in request.POST.items():
#                 if key.startswith('finance_year_'):
#                     prefix = key.replace('finance_year_', '')
#                     year = value
#                     amount = request.POST.get(f'finance_amount_{prefix}', 0)
#
#                     if year and amount:
#                         try:
#                             year_int = int(year)
#                             # Если это существующая запись (по ID)
#                             if prefix.isdigit() and prefix in existing_finances:
#                                 finance = existing_finances[prefix]
#                                 finance.year = year_int
#                                 finance.amount = amount
#                                 finance.save()
#                                 del existing_finances[prefix]
#                                 existing_years.discard(year_int)
#                             else:
#                                 # Для новой записи проверяем, нет ли дубликата года
#                                 if year_int in existing_years:
#                                     messages.error(request,
#                                                    f'Финансовая запись для {year_int} года уже существует. '
#                                                    'Измените существующую запись вместо создания новой.')
#                                     continue
#
#                                 # Создаем новую запись
#                                 TpirFinance.objects.create(
#                                     report=tpir,
#                                     year=year_int,
#                                     amount=amount
#                                 )
#                                 existing_years.add(year_int)
#                         except ValueError:
#                             messages.error(request, f'Некорректное значение года: {year}')
#                         except IntegrityError as e:
#                             messages.error(request,
#                                            f'Ошибка при сохранении данных для {year} года: {str(e)}')
#                             continue
#
#             # Удаление отмеченных записей
#             for key in request.POST:
#                 if key.startswith('delete_finance_'):
#                     finance_id = key.replace('delete_finance_', '')
#                     if finance_id in existing_finances:
#                         existing_finances[finance_id].delete()
#
#             messages.success(request, 'Отчет успешно обновлен')
#             return redirect('tpir:tpir_detail', pk=pk)
#     else:
#         form = TpirForm(instance=tpir, user=request.user)
#
#     context = {
#         'form': form,
#         'title': f'Редактирование отчета #{tpir.id}',
#         'tpir': tpir  # Передаем существующий отчет
#     }
#     return render(request, 'tpir/edit_tpir.html', context)
@login_required
def tpir_edit(request, pk):
    """Редактирование существующего отчета ТПИР"""
    tpir = get_object_or_404(
        Tpir.objects.select_related(
            'department',
            'facility',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'finance_records',
            'attached_files'
        ),
        pk=pk
    )

    if request.method == 'POST':
        form = TpirForm(request.POST, instance=tpir, user=request.user)
        if form.is_valid():
            try:
                updated_tpir = form.save(commit=False)
                updated_tpir.updated_by = request.user
                updated_tpir.save()

                # Обработка финансовых данных
                existing_finances = {str(f.id): f for f in tpir.finance_records.all()}
                existing_years = {f.year for f in existing_finances.values()}

                for key, value in request.POST.items():
                    if key.startswith('finance_year_'):
                        prefix = key.replace('finance_year_', '')
                        year = value
                        amount = request.POST.get(f'finance_amount_{prefix}', 0)

                        if year and amount:
                            try:
                                year_int = int(year)
                                amount_float = float(amount)

                                # Обработка существующей записи
                                if prefix.isdigit() and prefix in existing_finances:
                                    finance = existing_finances[prefix]
                                    finance.year = year_int
                                    finance.amount = amount_float
                                    finance.save()
                                    del existing_finances[prefix]
                                else:
                                    # Обработка новой записи
                                    TpirFinance.objects.create(
                                        report=tpir,
                                        year=year_int,
                                        amount=amount_float
                                    )

                            except (ValueError, IntegrityError):
                                continue

                # Удаление отмеченных записей
                for key in request.POST:
                    if key.startswith('delete_finance_'):
                        finance_id = key.replace('delete_finance_', '')
                        if finance_id in existing_finances:
                            existing_finances[finance_id].delete()

                return redirect('tpir:tpir_detail', pk=pk)

            except Exception:
                pass  # Ошибки обрабатываются через форму
    else:
        form = TpirForm(instance=tpir, user=request.user)

    context = {
        'form': form,
        'title': f'Редактирование отчета #{tpir.id}',
        'tpir': tpir
    }
    return render(request, 'tpir/edit_tpir.html', context)


@login_required
def tpir_detail(request, pk: int):
    """
    Детальный просмотр отчета ТПИР с проверкой доступа и всеми связанными данными
    """
    # Получаем отчет с оптимизированными запросами
    tpir = get_object_or_404(
        Tpir.objects.select_related(
            'department',
            'facility',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'attached_files',
            'finance_records'
        ),
        pk=pk
    )

    # Проверяем доступ пользователя к отчету
    user_departments = TpirUserDepartment.objects.filter(
        user=request.user
    ).values_list('department__id', flat=True)

    if tpir.department_id not in user_departments:
        raise PermissionDenied("У вас нет доступа к этому отчету")

    # Подготавливаем финансовые данные
    finances = tpir.finance_records.all().order_by('year')

    context = {
        'tpir': tpir,
        'title': f'Отчет ТПИР #{tpir.id}',
        'finances': finances,  # Передаем queryset вместо словаря
        'has_attachments': tpir.has_attachments(),
        'current_year': timezone.now().year,
    }

    return render(request, 'tpir/tpir_detail.html', context)


@contextmanager
def temp_zipfile():
    """Контекстный менеджер для временного ZIP-файла"""
    tmp = NamedTemporaryFile(suffix='.zip', delete=False)
    try:
        yield tmp
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


@login_required
def add_file(request, pk):
    tpir = get_object_or_404(Tpir, pk=pk)

    if request.method == 'POST':
        form = TpirAttachedFileForm(request.POST, request.FILES)
        if form.is_valid():
            files = request.FILES.getlist('file_field')
            uploaded_files = []
            errors = []

            for file in files:
                try:
                    # Создаем запись в базе и сохраняем файл
                    attached_file = TpirAttachedFile.objects.create(
                        tpir=tpir,
                        file=file
                    )
                    uploaded_files.append(attached_file)
                except Exception as e:
                    filename = file.name[:50] + '...' if len(file.name) > 50 else file.name
                    errors.append(f'Ошибка при загрузке файла "{filename}": {str(e)}')

            # Обновляем кэш
            cache_key = f'tpir_{pk}_has_attachments'
            cache.delete(cache_key)

            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                if errors:
                    return JsonResponse({'success': False, 'errors': errors}, status=400)
                return JsonResponse({'success': True})

            if errors:
                return render(request, 'tpir/attach_file_form.html', {
                    'form': form,
                    'tpir': tpir,
                    'upload_errors': errors
                })

            return redirect('tpir:manage_attach', pk=pk)
    else:
        form = TpirAttachedFileForm()

    return render(request, 'tpir/attach_file_form.html', {
        'form': form,
        'tpir': tpir
    })


@login_required
def delete_file(request, file_id):
    attached_file = get_object_or_404(TpirAttachedFile, id=file_id)
    tpir_id = attached_file.tpir.id

    if request.method == 'POST':
        file_path = os.path.join(settings.MEDIA_ROOT, str(attached_file.file))
        attached_file.delete()

        # Очищаем кэш
        cache_key = f'tpir_{tpir_id}_has_attachments'
        cache.delete(cache_key)

        # Удаляем физический файл
        if os.path.exists(file_path):
            os.remove(file_path)

        return redirect('tpir:manage_attach', pk=tpir_id)

    return render(request, 'tpir/delete_file_confirm.html', {
        'attached_file': attached_file,
        'short_name': os.path.basename(attached_file.file.name)
    })


@login_required
def download_file(request, file_id):
    attached_file = get_object_or_404(TpirAttachedFile, id=file_id)
    file_path = os.path.join(settings.MEDIA_ROOT, str(attached_file.file))
    response = FileResponse(open(file_path, 'rb'), as_attachment=True)
    return response


@login_required
def manage_attach(request, pk):
    tpir = get_object_or_404(Tpir.objects.prefetch_related('attached_files'), pk=pk)
    attached_files = tpir.attached_files.all()

    return render(request, 'tpir/manage_attach.html', {
        'tpir': tpir,
        'attached_files': attached_files
    })


@login_required
def download_attaches_zip(request, pk):
    tpir = get_object_or_404(Tpir, pk=pk)
    if not tpir.has_attachments():
        return HttpResponse('Нет файлов для скачивания')

    attached_files = tpir.attached_files.all()

    with temp_zipfile() as tmp:
        with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for attached_file in attached_files:
                file_path = os.path.join(settings.MEDIA_ROOT, str(attached_file.file))
                zipf.write(file_path, os.path.basename(file_path))

        response = FileResponse(
            open(tmp.name, 'rb'),
            as_attachment=True,
            filename=f'Attachments_TPIR_{pk}.zip'
        )
        response['Content-Type'] = 'application/zip'
        return response
