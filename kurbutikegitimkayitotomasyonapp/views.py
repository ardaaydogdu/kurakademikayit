from django.shortcuts import render, redirect, get_object_or_404
from django.db import transaction
from django.urls import reverse
from functools import wraps
from .models import Student, Enrollment, Branch
from .forms import (
    StudentForm,
    GuardianFormSet,
    EnrollmentForm,
    PaymentPlanForm,
    PaymentInstallmentForm,
)
from .utils import render_to_pdf


def home(request):
    return redirect("student_create")


# Sadece bu uygulamanın kendi girişini kontrol eden decorator
def portal_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get("portal_authenticated"):
            login_url = reverse("login")
            return redirect(f"{login_url}?next={request.path}")
        return view_func(request, *args, **kwargs)

    return _wrapped


def login_view(request):
    # Zaten giriş yaptıysa direkt listeye
    if request.session.get("portal_authenticated"):
        return redirect("student_list")

    error = None
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        # Sabit belirlediğin kullanıcı bilgileri
        if username == "kurakademi" and password == "2025kurakademi2026":
            request.session["portal_authenticated"] = True
            next_url = request.GET.get("next") or reverse("student_list")
            return redirect(next_url)
        else:
            error = "Kullanıcı adı veya şifre hatalı."

    return render(
        request,
        "login.html",
        {"error": error},
    )


def logout_view(request):
    request.session.flush()
    return redirect("login")


@transaction.atomic
@portal_login_required
def student_create(request):
    if request.method == "POST":
        student_form = StudentForm(request.POST)
        guardian_formset = GuardianFormSet(request.POST, prefix="guardians")
        enrollment_form = EnrollmentForm(request.POST)
        payment_plan_form = PaymentPlanForm(request.POST)

        if (
            student_form.is_valid()
            and guardian_formset.is_valid()
            and enrollment_form.is_valid()
            and payment_plan_form.is_valid()
        ):
            student = student_form.save()
            guardians = guardian_formset.save(commit=False)
            for g in guardians:
                g.student = student
                g.save()

            enrollment = enrollment_form.save(commit=False)
            enrollment.student = student
            enrollment.save()

            payment_plan = payment_plan_form.save(commit=False)
            payment_plan.enrollment = enrollment
            payment_plan.save()

            return redirect("enrollment_detail", pk=enrollment.pk)
    else:
        student_form = StudentForm()
        guardian_formset = GuardianFormSet(prefix="guardians")
        enrollment_form = EnrollmentForm()
        payment_plan_form = PaymentPlanForm()

    return render(
        request,
        "student_create.html",
        {
            "student_form": student_form,
            "guardian_formset": guardian_formset,
            "enrollment_form": enrollment_form,
            "payment_plan_form": payment_plan_form,
        },
    )


@portal_login_required
def enrollment_detail(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    payment_plan = getattr(enrollment, "payment_plan", None)
    installment_form = PaymentInstallmentForm()

    return render(
        request,
        "enrollment_detail.html",
        {
            "enrollment": enrollment,
            "payment_plan": payment_plan,
            "installment_form": installment_form,
        },
    )


@portal_login_required
def enrollment_pdf(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    payment_plan = getattr(enrollment, "payment_plan", None)
    context = {
        "enrollment": enrollment,
        "student": enrollment.student,
        "guardians": enrollment.student.guardians.all(),
        "payment_plan": payment_plan,
    }
    filename = f"kayit_{enrollment.student.full_name}.pdf"
    return render_to_pdf("enrollment_pdf.html", context, filename=filename)


@portal_login_required
def payment_add_installment(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    payment_plan = getattr(enrollment, "payment_plan", None)
    if not payment_plan:
        return redirect("enrollment_detail", pk=pk)

    if request.method == "POST":
        form = PaymentInstallmentForm(request.POST)
        if form.is_valid():
            installment = form.save(commit=False)
            installment.payment_plan = payment_plan
            installment.save()
    return redirect("enrollment_detail", pk=pk)


@portal_login_required
def student_list(request):
    branch_id = request.GET.get("branch")
    branches = Branch.objects.filter(is_active=True).order_by("name")

    students = Student.objects.all()
    selected_branch = None
    if branch_id:
        try:
            selected_branch = branches.get(id=branch_id)
            students = students.filter(enrollments__branch=selected_branch)
        except Branch.DoesNotExist:
            selected_branch = None
    students = students.order_by("-created_at").distinct()
    return render(
        request,
        "student_list.html",
        {
            "students": students,
            "branches": branches,
            "selected_branch": selected_branch,
        },
    )


@portal_login_required
def student_detail(request, pk):
    student = get_object_or_404(Student, pk=pk)
    enrollments = student.enrollments.select_related("program").all()
    return render(
        request,
        "student_detail.html",
        {
            "student": student,
            "enrollments": enrollments,
        },
    )

