from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from .forms import TpirForm
from commondata.forms import DateForm, DateSelectionForm, DateRangeForm

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from .models import Tpir, TpirUserDepartment, TpirFacility, TpirFinance

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.views.decorators.csrf import csrf_exempt


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


# @login_required
# def tpir_add(request):
#     """Добавление нового отчета ТПИР"""
#     if request.method == 'POST':
#         form = TpirForm(request.POST)
#         if form.is_valid():
#             new_tpir = form.save(commit=False)
#             new_tpir.created_by = request.user  # Устанавливаем создателя
#             new_tpir.save()
#             messages.success(request, 'Отчет успешно добавлен')
#             return redirect('tpir:tpir_detail', pk=new_tpir.id)
#     else:
#         form = TpirForm(user=request.user)
#
#     context = {
#         'form': form,
#         'title': 'Добавление нового отчета'
#     }
#     return render(request, 'tpir/add_tpir.html', context)
#
#
# @login_required
# def tpir_edit(request, pk):
#     """Редактирование существующего отчета ТПИР"""
#     tpir = get_object_or_404(Tpir, pk=pk)
#
#     if request.method == 'POST':
#         form = TpirForm(request.POST, instance=tpir)
#         # form = TpirForm(request.POST, instance=tpir, user=request.user)
#         if form.is_valid():
#             updated_tpir = form.save(commit=False)
#             updated_tpir.updated_by = request.user  # Устанавливаем редактора
#             updated_tpir.save()
#             messages.success(request, 'Отчет успешно обновлен')
#             return redirect('tpir:tpir_detail', pk=pk)
#     else:
#         form = TpirForm(instance=tpir, user=request.user)
#
#     context = {
#         'form': form,
#         'title': f'Редактирование отчета #{tpir.id}',
#         'tpir': tpir
#     }
#     return render(request, 'tpir/edit_tpir.html', context)
@login_required
def tpir_add(request):
    """Добавление нового отчета ТПИР"""
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
        'title': 'Добавление нового отчета'
    }
    return render(request, 'tpir/add_tpir.html', context)


@login_required
def tpir_edit(request, pk):
    """Редактирование существующего отчета ТПИР"""
    # tpir = get_object_or_404(Tpir, pk=pk)
    tpir = get_object_or_404(
        Tpir.objects.select_related(
            'department',
            'facility',
            'created_by',
            'updated_by'
        ).prefetch_related(
            'finance_records'
        ),
        pk=pk
    )
    if request.method == 'POST':
        form = TpirForm(request.POST, instance=tpir, user=request.user)
        if form.is_valid():
            updated_tpir = form.save(commit=False)
            updated_tpir.updated_by = request.user
            updated_tpir.save()

            # Обработка финансовых данных
            existing_finances = {str(f.id): f for f in tpir.finance_records.all()}

            for key, value in request.POST.items():
                if key.startswith('finance_year_'):
                    prefix = key.replace('finance_year_', '')
                    year = value
                    amount = request.POST.get(f'finance_amount_{prefix}', 0)

                    if year and amount:
                        # Если это существующая запись (по ID)
                        if prefix.isdigit():
                            finance_id = prefix
                            if finance_id in existing_finances:
                                finance = existing_finances[finance_id]
                                finance.year = year
                                finance.amount = amount
                                finance.save()
                                del existing_finances[finance_id]
                        else:
                            # Новая запись
                            TpirFinance.objects.create(
                                report=tpir,
                                year=year,
                                amount=amount
                            )

            # Удаление отмеченных записей
            for key in request.POST:
                if key.startswith('delete_finance_'):
                    finance_id = key.replace('delete_finance_', '')
                    if finance_id in existing_finances:
                        existing_finances[finance_id].delete()

            # Удаление оставшихся необработанных записей (если есть)
            for finance in existing_finances.values():
                finance.delete()

            messages.success(request, 'Отчет успешно обновлен')
            return redirect('tpir:tpir_detail', pk=pk)
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

