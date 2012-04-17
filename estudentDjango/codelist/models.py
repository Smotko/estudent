from django.db import models
from django.utils.encoding import smart_unicode
from django.utils.translation import ugettext as _
from settings import PROJECT_PATH
from urllib import urlopen, urlencode
from django.db.transaction import commit_on_success # pohitri insert
import os


# Create your models here.
class Country(models.Model):
    category_code = models.CharField(_("country code"), max_length=3,  primary_key=True, unique=True)
    descriptor = models.CharField(_("country name"), max_length=255)
    descriptor_english = models.CharField(_("country name original"), max_length=255)
    valid = models.BooleanField(_("valid"), default=True)
    
    class Meta:
        verbose_name_plural = _("countries")
        verbose_name = _("country")
        
    def __unicode__(self):
        return self.descriptor
    
    @classmethod
    @commit_on_success
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
            c.valid = True
            c.save()
            
class StudyProgram(models.Model):
    program_code = models.CharField(_("program code"), max_length=5, primary_key=True, unique=True)
    descriptor = models.CharField(_("program name"), max_length=255)
    valid = models.BooleanField(_("valid"), default=True)
        
    class Meta:
        verbose_name_plural = _("study programs")
        verbose_name = _("study program")
        
    def __unicode__(self):
        return self.descriptor
    
    @classmethod
    def updateAll(cls):
        UPDATE_FILE = os.path.join(PROJECT_PATH, 'programSmerIzbirnaSkupina.txt')
        
        csv_file = open(UPDATE_FILE)
        csv_data = csv_file.readlines()
        csv_file.close()
        
        # remove all the data from the table:
        StudyProgram.objects.all().delete();
        
        for line in csv_data:
            l = line.split('\t')
            c = StudyProgram()
            c.program_code = l[0].strip()
            c.descriptor = smart_unicode(l[1].strip(), encoding='windows-1250', strings_only=False, errors='strict')
            c.save()
            
class Post(models.Model):
    post_code = models.CharField(_("post code"), max_length=5, primary_key=True, unique=True)
    descriptor = models.CharField(_("post name"), max_length=255)
    valid = models.BooleanField(_("valid"), default=True)
    
    class Meta:
        verbose_name_plural = _("posts")
        verbose_name = _("post")
        
    def __unicode__(self):
        return self.descriptor
    
    @classmethod
    @commit_on_success    
    def updateAll(cls):
        UPDATE_FILE = os.path.join(PROJECT_PATH, 'poste.txt')
        
        csv_file = open(UPDATE_FILE)
        csv_data = csv_file.readlines()
        csv_file.close()
        
        # remove all the data from the table:
        Post.objects.all().delete();
        
        for line in csv_data:
            l = line.split('\t')
            c = Post()
            c.post_code = l[0].strip()
            c.descriptor = l[1].strip()
            c.save()
            
class Region(models.Model):
    region_code = models.CharField(_("region code"), max_length=3, primary_key=True, unique=True)
    descriptor = models.CharField(_("region name"), max_length=255)
    valid = models.BooleanField(_("valid"), default=True)

    class Meta:
        verbose_name_plural = _("regions")
        verbose_name= _("region")
        
    def __unicode__(self):
        return self.descriptor
    
    @classmethod
    @commit_on_success    
    def updateAll(cls):
        UPDATE_FILE = os.path.join(PROJECT_PATH, 'obcine.txt')
        
        csv_file = open(UPDATE_FILE)
        csv_data = csv_file.readlines()
        csv_file.close()
        
        Region.objects.all().delete()
        
        for line in csv_data:
            l = line.split('\t')
            c = Region()
            c.region_code = l[0].strip()
            c.descriptor = l[1].strip()
            c.save()    

class Faculty(models.Model):
    faculty_code =  models.CharField(_("faculty code"), max_length=3, primary_key=True, unique=True)
    descriptor = models.CharField(_("faculty name"), max_length=255)
    valid = models.BooleanField(_("valid"), default=True)
    
    class Meta:
        verbose_name_plural = _("faculties")
        verbose_name= _("faculty")
        
    def __unicode__(self):
        return self.descriptor
    
    @classmethod
    def updateAll(cls):
        Faculty.objects.all().delete()                
        c = Faculty()
        c.faculty_code = "163"
        c.descriptor = "FRI"
        c.save()
            
class Course(models.Model):
    course_code = models.CharField(_("course code"), max_length=5, primary_key=True, unique=True)
    name = models.CharField(_("course name"), max_length=255)
    instructors = models.ManyToManyField("Instructor", related_name=("instructors"), verbose_name = _("instructors"))
    CT_JOINED = ('S', 'Skupni') # vec predavateljev istim studentom, kdorkoli razpise rok
    CT_SPLIT = ('R', 'Razdeljeni') # studentje se razdelijo med predavatelje, vsak zase razpise rok
    course_type = models.CharField(_("course type"), max_length=255, choices=(CT_JOINED, CT_SPLIT))
    valid = models.BooleanField(_("valid"), default=True)

    # tuki je se treba nekam dodat za kater letnik je to... pa se v enrollment
    compulsoryfor = models.ManyToManyField("StudyProgram", related_name=("compulsoryfor"), blank=True)
    selectivefor = models.ManyToManyField("StudyProgram", related_name=("selectivefor"), blank=True)

    def __unicode__(self):
        return self.name + " (" + self.course_code + ")"
    
    @classmethod
    def updateAll(cls):
        FILE = os.path.join(PROJECT_PATH, 'predmeti.txt')
        
        csv_file = open(FILE)
        csv_data = csv_file.readlines()
        csv_file.close()
        
        Course.objects.all().delete()
        
        for line in csv_data:
            l = line.split(',')
            if len(l)<3: continue
            c = Course()
            c.course_code = l[0].strip()
            c.name = l[1].strip()
            c.save()
            for ins in l[2:-1]:
                c.instructors.add(Instructor.objects.get(instructor_code=ins.strip()))

            if l[-1].strip()=='R':
                c.course_type = Course.CT_SPLIT
            else:
                c.course_type = Course.CT_JOINED                

            c.save()
                    
    class Meta:
        verbose_name_plural =_("courses")
        verbose_name=_("course")
        
class Instructor(models.Model):
    instructor_code = models.CharField(_("instructor code"), max_length=5, primary_key=True, unique=True)
    name = models.CharField(_("name"), max_length=255)
    surname = models.CharField(_("surname"), max_length=255)
    valid = models.BooleanField(_("valid"), default=True)
    courses = models.ManyToManyField("Course", related_name=("courses"), verbose_name = _("courses"))
    
    def __unicode__(self):
        return self.name + ' ' + self.surname +" (" + self.instructor_code + ")"

    @classmethod
    def updateAll(cls):
        FILE = os.path.join(PROJECT_PATH, 'profesorji.txt')
        
        csv_file = open(FILE)
        csv_data = csv_file.readlines()
        csv_file.close()
        
        Instructor.objects.all().delete()
        
        for line in csv_data:
            l = line.split(',')
            if len(l)<3: continue
            c = Instructor()
            c.instructor_code = l[0].strip()
            c.name = l[1].strip()
            c.surname = l[2].strip()
            c.save()

    class Meta:
        verbose_name_plural =_("instructors")
        verbose_name=_("instructor")
    
