from django.db import models
from django.utils import timezone


class Program(models.Model):
    name = models.CharField("Program Adı", max_length=150, unique=True)
    description = models.TextField("Açıklama", blank=True, null=True)
    is_active = models.BooleanField("Aktif mi?", default=True)

    class Meta:
        verbose_name = "Program"
        verbose_name_plural = "Programlar"

    def __str__(self):
        return self.name


class Branch(models.Model):
    name = models.CharField("Şube Adı", max_length=100, unique=True)
    is_active = models.BooleanField("Aktif mi?", default=True)

    class Meta:
        verbose_name = "Şube"
        verbose_name_plural = "Şubeler"

    def __str__(self):
        return self.name

class Student(models.Model):
    GENDER_CHOICES = (
        ("M", "Erkek"),
        ("F", "Kadın"),
        ("O", "Diğer / Belirtmek İstemiyorum"),
    )

    full_name = models.CharField("Adı Soyadı", max_length=150)
    national_id = models.CharField("T.C Kimlik No", max_length=11, unique=True)
    birth_date = models.DateField("Doğum Tarihi")
    gender = models.CharField("Cinsiyet", max_length=1, choices=GENDER_CHOICES)
    school = models.CharField("Okulu", max_length=200, blank=True, null=True)

    CLASS_CHOICES = [(str(i), f"{i}. Sınıf") for i in range(1, 13)] + [
        ("MEZUN", "Mezun"),
    ]
    school_class = models.CharField("Sınıfı", max_length=10, choices=CLASS_CHOICES)

    emergency_contact_name = models.CharField(
        "Acil Durum Kişi Adı", max_length=150
    )
    emergency_contact_phone = models.CharField(
        "Acil Durum Telefonu", max_length=20
    )

    created_at = models.DateTimeField("Oluşturma Tarihi", auto_now_add=True)

    class Meta:
        verbose_name = "Öğrenci"
        verbose_name_plural = "Öğrenciler"

    def __str__(self):
        return f"{self.full_name} ({self.national_id})"


class Guardian(models.Model):
    RELATION_CHOICES = (
        ("anne", "Anne"),
        ("baba", "Baba"),
        ("veli", "Veli"),
        ("diger", "Diğer"),
    )

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="guardians"
    )
    full_name = models.CharField("Veli Adı Soyadı", max_length=150)
    national_id = models.CharField("Veli T.C Kimlik No", max_length=11)
    relation = models.CharField(
        "Yakınlık Derecesi", max_length=20, choices=RELATION_CHOICES
    )
    phone = models.CharField("Telefon Numarası", max_length=20)
    email = models.EmailField("E-posta Adresi", blank=True, null=True)
    address = models.TextField("Adres Bilgisi", blank=True, null=True)

    class Meta:
        verbose_name = "Veli"
        verbose_name_plural = "Veliler"

    def __str__(self):
        return f"{self.full_name} - {self.student.full_name}"


class Enrollment(models.Model):
    LEVEL_CHOICES = [(f"T{i}", f"T{i}") for i in range(1, 18)]

    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="enrollments"
    )
    program = models.ForeignKey(
        Program, on_delete=models.PROTECT, related_name="enrollments"
    )
    branch = models.ForeignKey(
        Branch,
        on_delete=models.PROTECT,
        related_name="enrollments",
        verbose_name="Şube",
        null=True,
        blank=True,
    )
    start_date = models.DateField("Başlangıç Tarihi", default=timezone.now)
    level = models.CharField(
        "Seviye / Kur", max_length=5, choices=LEVEL_CHOICES
    )

    created_at = models.DateTimeField("Kayıt Tarihi", auto_now_add=True)

    class Meta:
        verbose_name = "Kayıt"
        verbose_name_plural = "Kayıtlar"

    def __str__(self):
        return f"{self.student.full_name} - {self.program.name} ({self.level})"


class PaymentPlan(models.Model):
    PAYMENT_METHOD_CHOICES = (
        ("nakit", "Nakit"),
        ("havale", "Havale / EFT"),
        ("taksit", "Taksit"),
        ("kredi_karti", "Kredi Kartı"),
    )

    enrollment = models.OneToOneField(
        Enrollment, on_delete=models.CASCADE, related_name="payment_plan"
    )
    total_amount = models.DecimalField("Toplam Ücret", max_digits=10, decimal_places=2)
    payment_method = models.CharField(
        "Ödeme Şekli", max_length=20, choices=PAYMENT_METHOD_CHOICES
    )
    installment_count = models.PositiveSmallIntegerField(
        "Taksit Sayısı (2-10)",
        blank=True,
        null=True,
        help_text="Sadece taksitli ödemelerde doldurun.",
    )

    class Meta:
        verbose_name = "Ödeme Planı"
        verbose_name_plural = "Ödeme Planları"

    def __str__(self):
        return f"{self.enrollment} - {self.total_amount} TL"

    @property
    def total_paid(self):
        return (
            self.installments.filter(is_paid=True)
            .aggregate(models.Sum("amount"))["amount__sum"]
            or 0
        )

    @property
    def remaining(self):
        return self.total_amount - self.total_paid


class PaymentInstallment(models.Model):
    payment_plan = models.ForeignKey(
        PaymentPlan, on_delete=models.CASCADE, related_name="installments"
    )
    amount = models.DecimalField("Tutar", max_digits=10, decimal_places=2)
    is_paid = models.BooleanField("Ödendi mi?", default=False)
    paid_at = models.DateField("Ödeme Tarihi", blank=True, null=True)
    notes = models.CharField("Açıklama", max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = "Ödeme / Taksit"
        verbose_name_plural = "Ödemeler / Taksitler"
        ordering = ["id"]

    def __str__(self):
        return f"{self.payment_plan.enrollment} - {self.amount} TL"
