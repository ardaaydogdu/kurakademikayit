from django.contrib import admin
from .models import Program, Branch, Student, Guardian, Enrollment, PaymentPlan, PaymentInstallment


class GuardianInline(admin.TabularInline):
    model = Guardian
    extra = 1


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("full_name", "national_id", "school_class", "school")
    search_fields = ("full_name", "national_id", "school")
    inlines = [GuardianInline]


class PaymentInstallmentInline(admin.TabularInline):
    model = PaymentInstallment
    extra = 0


@admin.register(Program)
class ProgramAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("student", "program", "branch", "level", "start_date")
    list_filter = ("program", "branch", "level")


@admin.register(PaymentPlan)
class PaymentPlanAdmin(admin.ModelAdmin):
    list_display = ("enrollment", "total_amount", "payment_method", "total_paid", "remaining")
    inlines = [PaymentInstallmentInline]


@admin.register(PaymentInstallment)
class PaymentInstallmentAdmin(admin.ModelAdmin):
    list_display = ("payment_plan", "amount", "is_paid", "paid_at")
    list_filter = ("is_paid", "paid_at")
