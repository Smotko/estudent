from django.db import models
from django.utils.translation import ugettext as _


class Student(models.Model):
    enrollment_number = models.IntegerField(_("enrollment number"))
    name = models.CharField(_(_("name")), max_length=255)
    surname = models.CharField(_("surname"), max_length=255)
    social_security_number = models.CharField(_("social security number"), max_length=13)
    tax_number = models.CharField(_("tax number"), max_length=8)
    address = models.OneToOneField("Address", related_name=("address"), verbose_name=_('address'))
    temp_address = models.OneToOneField("Address", related_name=("temp_address"), verbose_name=_('temporary address'))
    
class Address(models.Model):
    street = models.CharField(_("street"), max_length=255)
    country = models.ForeignKey("codelist.Country", related_name=("country"), verbose_name = _("country"))

class Enrollement(models.Model):
    student = models.OneToOneField("Student", verbose_name=_("student"))