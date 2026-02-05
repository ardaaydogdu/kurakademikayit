from django import forms
from django.forms import inlineformset_factory
from .models import Student, Guardian, Enrollment, PaymentPlan, PaymentInstallment


class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            "full_name",
            "national_id",
            "birth_date",
            "gender",
            "school",
            "school_class",
            "emergency_contact_name",
            "emergency_contact_phone",
        ]
        widgets = {
            "birth_date": forms.DateInput(attrs={"type": "date"}),
        }


GuardianFormSet = inlineformset_factory(
    Student,
    Guardian,
    fields=[
        "full_name",
        "national_id",
        "relation",
        "phone",
        "email",
        "address",
    ],
    extra=1,
    can_delete=True,
)


class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = Enrollment
        fields = ["program", "branch", "start_date", "level"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date"}),
        }


class PaymentPlanForm(forms.ModelForm):
    class Meta:
        model = PaymentPlan
        fields = ["total_amount", "payment_method", "installment_count"]

    def clean_installment_count(self):
        count = self.cleaned_data.get("installment_count")
        method = self.cleaned_data.get("payment_method")
        if method == "taksit":
            if not count:
                raise forms.ValidationError("Taksitli ödemede taksit sayısı zorunludur.")
            if count < 2 or count > 10:
                raise forms.ValidationError("Taksit sayısı 2 ile 10 arasında olmalıdır.")
        else:
            # taksitli değilse alanı sıfırla
            return None
        return count


class PaymentInstallmentForm(forms.ModelForm):
    class Meta:
        model = PaymentInstallment
        fields = ["amount", "is_paid", "paid_at", "notes"]
        widgets = {
            "paid_at": forms.DateInput(attrs={"type": "date"}),
        }

