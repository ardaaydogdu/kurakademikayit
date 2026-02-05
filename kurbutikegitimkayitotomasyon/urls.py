"""
URL configuration for kurbutikegitimkayitotomasyon project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from kurbutikegitimkayitotomasyonapp import views

urlpatterns = [
    path("kuradmin/", admin.site.urls),
    path("", views.home, name="home"),
    path("giris/", views.login_view, name="login"),
    path("cikis/", views.logout_view, name="logout"),
    path("ogrenci/yeni/", views.student_create, name="student_create"),
    path("ogrenciler/", views.student_list, name="student_list"),
    path("ogrenci/<int:pk>/", views.student_detail, name="student_detail"),
    path("kayit/<int:pk>/", views.enrollment_detail, name="enrollment_detail"),
    path("kayit/<int:pk>/pdf/", views.enrollment_pdf, name="enrollment_pdf"),
    path("kayit/<int:pk>/odeme-ekle/", views.payment_add_installment, name="payment_add_installment"),
]
