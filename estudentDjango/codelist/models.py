from django.db import models
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from urllib import urlopen, urlencode


# Create your models here.
class Country(models.Model):
    category_code = models.CharField(max_length=3)
    descriptor = models.CharField(max_length=255)
    descriptor_english = models.CharField(max_length=255)
    
    class Meta:
        verbose_name_plural = _("countries")
        verbose_name = _("country")
        
    def __unicode__(self):
        return self.descriptor
    
    @classmethod
    def updateAll(cls):
        UPDATE_URL = 'http://www.stat.si/klasje/tabela.aspx?CVN=3888'
        
        csv_data = urlopen(UPDATE_URL, data=urlencode(
                {'__EVENTTARGET':'lbtnCSV',
                 '__VIEWSTATE':'/wEPDwUKMTE0NzM0NDIwOA8WAh4IRmlsZU5hbWUFDERSWkFWRV8yMDA3YRYCAgUPZBYCAgEPDxYCHgRUZXh0BUZEUlpBVkUgLSBEcsW+YXZlIGluIGRydWdhIG96ZW1samEgLSBzbG92ZW5za2kgc3RhbmRhcmQgSVNPIDMxNjYsIDIwMDdhZGRkGIb41rYrP0v4AjxvttSQlHzBYkKrRV1AnnRqhWi3Khc=',
                 '__EVENTVALIDATION':'/wEWBgLjvsyeCgL9jOOoBAKy46z3AQK9zJaBCQLs0bLrBgKM54rGBqOqwJFQsH2QbRBir2QR/GT3KuQJWO2Z+1fyMQB26Y8j'
                        
                }))
        csv_data.readline()
        
        # remove all the data from the table:
        Country.objects.all().delete();
        
        for line in csv_data.readlines():
            l = line.split(';')
            c = Country()
            c.category_code = l[1].strip()
            c.descriptor = smart_unicode(l[2].strip(), encoding='windows-1250', strings_only=False, errors='strict')
            c.descriptor_english = l[3].strip()
            c.save()
