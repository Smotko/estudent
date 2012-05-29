# Create your views here.
from codelist.models import Course, StudyProgram
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import context, loader
from django.template.context import RequestContext, Context
from student.models import ExamSignUp, ExamDate, Enrollment, Student


def exam_grades_index(request):

    exam_dates=ExamDate.objects.all().order_by('date')
    return render_to_response('admin/student/exam_grades_index.html', {'izpitni_roki': exam_dates,}, RequestContext(request))

#http://stackoverflow.com/questions/4148923/is-it-possible-to-create-a-custom-admin-view-without-a-model-behind-it
def exam_grades_view(request, exam_Id): #show list of all objects

    examDateId = int(exam_Id)
    exam=ExamDate.objects.get(id=examDateId)

    prijave = ExamSignUp.objects.filter(examDate=exam)


    result = []
    for p in prijave:
        prijava = {}
        prijava['priimek'] = p.enroll.student.surname
        prijava['ime'] = p.enroll.student.name
        prijava['leto'] = str(p.enroll.study_year) + "/" + str(p.enroll.study_year + 1)
        prijava['vpisna_st'] = p.enroll.student.enrollment_number
        prijava['opcije']= p.RESULTS
        prijava['tocke'] = "" if p.points == None else p.points
        prijava['ocena_izpita'] = p.result_exam
        prijava['ocena_vaj']=p.result_practice




        result = result + [prijava]


    return render_to_response('admin/student/exam_grades.html', {'izpitnirok': exam, 'prijave':result}, RequestContext(request))

def class_list(request):
    
    class ClassForm(forms.Form):
        
        choices = []
        for c in Course.objects.all():
            choices.append((c.pk, c.__unicode__()))
        
        programs = []
        for p in StudyProgram.objects.all():
            programs.append((p.pk, p.__unicode__()))
        
        prog = forms.ChoiceField(choices=programs, label="Program")
        cour = forms.ChoiceField(choices=choices, label="Izbirni predmet")
        year = forms.MultipleChoiceField(choices=[(2012, 2012), (2011, 2011), (2010, 2010)], label="Leto")
        
        
    students = []
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if 'year' in request.POST:
            students = Enrollment.objects.filter(study_year__in = request.POST.getlist('year'), courses = request.POST['cour'], program = request.POST['prog'])
            
        
    else:
        form = ClassForm()
        
    return render_to_response('admin/student/class_list.html', {'form':form, 'students': students}, RequestContext(request))


def exam_sign_up_index(request):
    try:
        student_Id=request.POST['vpisna']
        if student_Id.isdigit():
            try:
                student = Student.objects.get(enrollment_number=student_Id)

                if 'prijava' in request.POST:
                    return HttpResponseRedirect(reverse('student.views.exam_sign_up', args=[student.enrollment_number]))
                elif 'odjava' in request.POST:
                    return HttpResponseRedirect(reverse('student.views.exam_sign_out', args=[student.enrollment_number]))
                elif Student.DoesNotExist:
                    return HttpResponseRedirect(reverse('student.views.exam_sign_out', args=[student.enrollment_number]))
            except:
                pass
                
        return render_to_response('admin/student/exam_sign_up_index.html', {
            'error_message': "Student with this number does not exist",
            }, context_instance=RequestContext(request))

    except:
        return render_to_response('admin/student/exam_sign_up_index.html', {}, context_instance=RequestContext(request))




def exam_sign_up(request, student_Id):
    s = get_object_or_404(Student, enrollment_number=student_Id)
    student = Student.objects.get(enrollment_number=student_Id)

    class EnrollForm(forms.Form):
        enrolls=[]
        ePk=[]
        if len(Enrollment.objects.filter(student=student))>1:
            for enroll in Enrollment.objects.filter(student=student):
                enrolls.append((enroll.pk, enroll.__unicode__()))
        else:
            Enrollment.objects.get(student=student)


        enrolments=forms.ChoiceField(choices=enrolls)

    exams=[]
    if request.method == 'POST':
        form = EnrollForm(request.POST)
        enroll= Enrollment.objects.get(id=request.POST['enrolments'])
        classes=Course.objects.filter(curriculum__in=enroll.get_classes()  )
        exams=ExamDate.objects.filter(course__in=classes)

    else:
        form=EnrollForm()


    return render_to_response('admin/student/exam_sign_up.html', {'form':form,'Roki':exams, 'Student':student_Id}, RequestContext(request))

def exam_sign_out(request, student_Id):
    s = get_object_or_404(Student, enrollment_number=student_Id)

    exist=ExamSignUp.objects.filter(examDate__in=s.get_current_exam_dates())


    return render_to_response('admin/student/exam_sign_out.html', {'Prijave':exist}, RequestContext(request))
    
    
def student_index(request):
    try:
        student_Id = request.POST['vpisna']
        if student_Id.isdigit():
            try:
                student = Student.objects.get(enrollment_number=student_Id)
                if 'zadnje' in request.POST:
                    return HttpResponseRedirect(reverse('student.views.student_index_list', args=[student.enrollment_number, 1]))
                else:
                    return HttpResponseRedirect(reverse('student.views.student_index_list', args=[student.enrollment_number, 0]))


                return HttpResponseRedirect(reverse('student.views.student_index_list', args=[student.enrollment_number, 0]))
            except:
                pass
                
        return render_to_response('admin/student/student_index.html', {
            'error_message': "Student with this number does not exist",
            }, context_instance=RequestContext(request))
    except:
        return render_to_response('admin/student/student_index.html', {}, context_instance=RequestContext(request))


def student_index_list(request, student_Id, display): #0=all, 1=last
    s = get_object_or_404(Student, enrollment_number=student_Id)
    response = []
    response={'student_name':"",'study_program':"",'courses':""}       
    response["student_name"] = s.name

    enrolls = Enrollment.objects.filter(student=s).order_by('program', 'study_year', 'class_year')
    prog = ""
    for enroll in enrolls:
        out={}
        out['program'] = enroll.program.descriptor
        if prog != out['program']:
            out['noprogram'] = True
            prog = out['program']

        out['enroll'] = enroll
        courses = []
        
        for p in enroll.courses.order_by('course_code'):
            try:
            course={}
            course["name"]=p.name
                signups = ExamSignUp.objects.filter(enroll=enroll).order_by('examDate__date')
                signups = filter(lambda s: s.examDate.course.name == p.name, signups)
                print display
                if display == "1":
                    signups = signups[-1:]
            
                course["signups"] = signups
            courses = courses+[course]
            except:
                pass
        out["courses"]=courses
        response = response + [out]

    return render_to_response('admin/student/student_index_list.html', {'student':s, 'data':response}, RequestContext(request))
