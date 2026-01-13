from django.urls import path
from . import views  # 這裡的 . 才是指 core 資料夾
from django.urls import path, include
urlpatterns = [
    path('', views.index, name='index'),
    path('upload/committee/', views.upload_excel, {'mode': 'committee'}, name='upload_committee'),
    path('upload/andou/', views.upload_excel, {'mode': 'andou'}, name='upload_andou'),
    path('upload/light/', views.upload_excel, {'mode': 'light'}, name='upload_light'),
    path('export/andou/pdf/<str:year>/', views.andou_pdf, name='andou_pdf'),
    path('get_form/', views.get_form_content, name='get_form'),
    path('save_data/', views.save_data, name='save_data'),
    path('delete_data/', views.delete_data, name='delete_data'),
    path('export_excel/<str:mode>/', views.export_excel, name='export_excel'),
    path('andou_pdf/<str:year>/', views.andou_pdf, name='andou_pdf'),
    path('upload/<str:mode>/', views.upload_excel, name='upload_excel')
]