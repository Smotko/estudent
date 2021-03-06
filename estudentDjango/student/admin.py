from django.conf.urls.defaults import *
from django.contrib import admin, messages
from django.contrib.admin.options import csrf_protect_m
from django.core.context_processors import request
from django.http import HttpRequest
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from student.forms import StudentForm
from student.models import *
from django import forms

class AddressInLine(admin.TabularInline):
    model = Address
    max_num = 2
    raw_id_fields = ("country","region","post")
    
class PhoneInLine(admin.TabularInline):
    model = Phone
    max_num = 2
    
class StudentAdmin(admin.ModelAdmin):
    model = Student
    search_fields = ('enrollment_number', 'name', 'surname')
    inlines = [PhoneInLine, AddressInLine]
    form = StudentForm
    raw_id_fields = ("birth_country","birth_region")

    def _personal(self, obj):
        return '<a href="/student/StudentPersonal/%s">Osebni podatki</a>' % (obj.enrollment_number)
    _personal.allow_tags = True
    _personal.short_description = 'Osebni podatki'
    
    def _kartotecni(self, obj):
        return '''<a href="/student/StudentIndex/%s/0">Vsa polaganja</a><br />
                  <a href="/student/StudentIndex/%s/1">Zadnje polaganje</a>''' % (obj.enrollment_number,obj.enrollment_number)
    _kartotecni.allow_tags = True
    _kartotecni.short_description = _('Kartotecni list')

    list_display = ['__unicode__', '_personal', '_kartotecni']
class EnrollmentAdmin(admin.ModelAdmin):
    
    
    @csrf_protect_m
    def changelist_view(self, request, extra_context=None):
        self.list_display = ['action_checkbox', '__str__','_vpisna','_ime', '_priimek']
        if 'study_year' not in request.GET:
            self.list_display.append('study_year')
        if 'class_year' not in request.GET:
            self.list_display.append('class_year')
        if 'program' not in request.GET:
            self.list_display.append('program')
        if 'enrol_type__exact' not in request.GET:
            self.list_display.append('enrol_type')
        if 'regular__exact' not in request.GET:
            self.list_display.append('regular')
            
        return admin.ModelAdmin.changelist_view(self, request, extra_context=extra_context)
    
    model = Enrollment
    search_fields = ('student__name','student__surname', 'student__enrollment_number')
    raw_id_fields = ("student","program")
    list_filter = ('study_year', 'class_year', 'modules', 'program', 'enrol_type', 'regular');
    #list_display_links = ('id', )

class CurriculumAdmin(admin.ModelAdmin):
    model = Curriculum
    list_filter = ('mandatory', 'class_year', 'module', 'program');

    search_fields = ('course',)


    def admin_update_curriculum(self, request):
        Curriculum.updateAll()
            
        messages.success(request, _("Curriculum added successfully"))
        
        return redirect('/student/curriculum')

    # override the get_urls to add a custom view:
    def get_urls(self):
        urls = super(CurriculumAdmin, self).get_urls()
        my_urls = patterns('',
            url(
                r'update',
                self.admin_site.admin_view(self.admin_update_curriculum),
                name='admin_update_curriculum',
            ),
        )
        return my_urls + urls





class ModuleAdmin(admin.ModelAdmin):
    model = Module
    #list_filter = ('curriculum__course', 'mandatory');
    
    
    
class ExamDateForm(forms.ModelForm):
    class Meta:
        model = ExamDate
        
    def exam_on_date_exist(self, course, instructors, date):
        try:
            exams=ExamDate.objects.filter(course=course)
        except:
            return False
            
        for e in exams:
            if e.instructors==instructors and e.date==date:
                return True
        
        return False
        
    def clean(self):
        data = super(ExamDateForm, self).clean()

        if hasattr(self, 'instance') and self.instance.pk is not None:
            #update
            pass
            #TODO: se vedno lahko premaknes datum enega obstojecega izpita cez drug obstojec izpit
        else:
            #new 
            if(self.exam_on_date_exist(data.get("course"), data.get("instructors"), data.get("date"))):
                raise forms.ValidationError(u'Na ta dan ze obstaja izpit.')
            
        return self.cleaned_data

class ExamDateAdmin(admin.ModelAdmin):
    model = ExamDate
    form = ExamDateForm
    
    def queryset(self, request):
        qs = super(ExamDateAdmin, self).queryset(request)
        if request.user.groups.filter(name = 'profesorji'):
            qs = qs.filter(instructors__instructor__user = request.user)
        return qs
    
    def _personal(self, obj):
        return u"""<a href="/student/ExamGrades/%(examId)s/1">Seznam prijavljenih</a> <br />
                  <a href="/student/ExamGrades/%(examId)s/0">Rezultati pisnega dela</a> <br />
                  <a href="/student/ExamGrades/%(examId)s/2">Seznam rezultatov pisnega</a> <br />
                  <a href="/student/ExamGrades/%(examId)s/3">Vpis koncnih ocen</a>""" % \
                  {'examId': str(obj.pk)}
    def _study(self, obj):
        return str(obj.date.year-1) + '/' + str(obj.date.year)[2:] 
    _study.short_description = _('study year')
    _personal.allow_tags = True
    _personal.short_description = 'Akcije'

    list_display = ['__unicode__', 'instructors', '_study', '_personal']
    list_filter = ('study_year', 'instructors',)
    search_fields = ('course__name',)
    

    def admin_update_examdate(self, request):
        ExamDate.updateAll()
            
        messages.success(request, _("examdate added successfully"))
        
        return redirect('/student/examdate')

    # override the get_urls to add a custom view:
    def get_urls(self):
        urls = super(ExamDateAdmin, self).get_urls()
        my_urls = patterns('',
            url(
                r'update',
                self.admin_site.admin_view(self.admin_update_examdate),
                name='admin_update_examdate',
            ),
        )
        return my_urls + urls


    
admin.site.register(Student, StudentAdmin)
admin.site.register(Address)
admin.site.register(Enrollment, EnrollmentAdmin)        
admin.site.register(ExamDate, ExamDateAdmin)
admin.site.register(ExamSignUp)
admin.site.register(Curriculum, CurriculumAdmin)
admin.site.register(Module, ModuleAdmin)

