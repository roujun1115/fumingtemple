from django.db import models

class BaseRecord(models.Model):
    year = models.CharField(max_length=10, verbose_name="年份(如：乙巳年)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True

class Committee(BaseRecord):
    title = models.CharField(max_length=50, verbose_name="職稱")
    name = models.CharField(max_length=50, verbose_name="姓名")

class Andou(BaseRecord):
    item = models.CharField(max_length=50, verbose_name="項目")
    name = models.CharField(max_length=100, verbose_name="姓名")
    address = models.CharField(max_length=255, verbose_name="地址")
    payment_status = models.BooleanField(default=False, verbose_name="繳費狀態")
    remark = models.TextField(blank=True, verbose_name="備註")

class Light(BaseRecord):
    item = models.CharField(max_length=50, verbose_name="項目")
    name = models.CharField(max_length=50, verbose_name="姓名")
    payment_status = models.BooleanField(default=False, verbose_name="繳費狀態")
    remark = models.TextField(blank=True, verbose_name="備註")

class Donation(BaseRecord):
    name = models.CharField(max_length=50, verbose_name="姓名")
    amount = models.IntegerField(verbose_name="金額")