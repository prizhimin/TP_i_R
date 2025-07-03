# 25.05.2025 г.
from django.urls import path
from . import views

app_name = 'tpir'

urlpatterns = [
    # Основные маршруты для отчетов ТПИР
    path('', views.tpir_list, name='tpir_list'),
    path('add/', views.tpir_add, name='tpir_add'),
    path('<int:pk>/', views.tpir_detail, name='tpir_detail'),
    path('<int:pk>/edit/', views.tpir_edit, name='tpir_edit'),
    # path('<int:tpir_id>/delete/', views.tpir_delete, name='tpir_delete'),
    #
    # # Маршруты для работы с финансовыми данными
    # path('<int:tpir_id>/finance/add/', views.add_finance, name='add_finance'),
    # path('<int:tpir_id>/finance/<int:finance_id>/edit/', views.edit_finance, name='edit_finance'),
    # path('<int:tpir_id>/finance/<int:finance_id>/delete/', views.delete_finance, name='delete_finance'),
    #
    # # Маршруты для работы с вложениями
    # path('<int:tpir_id>/manage_attach/', views.manage_attach, name='manage_attach'),
    # path('<int:tpir_id>/attach/', views.add_file, name='attach_file'),
    # path('<int:tpir_id>/zipattach/', views.download_attaches_zip, name='download_attaches_zip'),
    # path('file/<int:file_id>/delete/', views.delete_file, name='delete_file'),
    # path('file/<int:file_id>/download/', views.download_file, name='download_file'),
    #
    # # Маршруты для отчетов
    # path('summary_report/', views.summary_report, name='summary_report'),
    # path('generate_summary_report/', views.generate_summary_report, name='generate_summary_report'),
    #
    # # Дополнительные маршруты
    # path('facilities/', views.facility_list, name='facility_list'),
    # path('facilities/add/', views.add_facility, name='add_facility'),
    # path('facilities/<int:facility_id>/edit/', views.edit_facility, name='edit_facility'),
    # path('facilities/<int:facility_id>/toggle/', views.toggle_facility_status, name='toggle_facility_status'),

    path('ajax/load-facilities/', views.load_facilities, name='tpir_load_facilities'),
    path('ajax/add-facility/', views.add_facility, name='tpir_add_facility'),
]
