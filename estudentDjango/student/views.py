# Create your views here.
import datetime
import traceback
from codelist.models import Course, StudyProgram, Instructor
from django import forms
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, get_object_or_404
from django.template import context, loader
from django.template.context import RequestContext, Context
from student.models import *
from codelist.models import Course
from django.core import serializers


def exam_grades_index(request):

    exam_dates=ExamDate.objects.all().order_by('date')
    if request.user.groups.filter(name = 'profesorji'):
        exam_dates = [e for e in exam_dates if e.instructors and e.instructors.instructor.filter(user = request.user)]
    return render_to_response('admin/student/exam_grades_index.html', {'izpitni_roki': exam_dates,}, RequestContext(request))

#http://stackoverflow.com/questions/4148923/is-it-possible-to-create-a-custom-admin-view-without-a-model-behind-it
def exam_grades_view(request, exam_Id, l): #show list of all objects

    examDateId = int(exam_Id)
    exam=ExamDate.objects.get(id=examDateId)

    prijave = ExamSignUp.objects.order_by('enroll__student__surname').filter(examDate=exam) #TODO: Check if this works

    from api.views import _getPolaganja

    showVP = (int(l) in [1])

    settings = {}
    try:
        settings['examId'] = exam.id
        settings['showVP'] = showVP
        settings['l'] = int(l)
        settings['firstyear'] = list(Enrollment.objects.order_by('study_year').filter(student=prijave[0].enroll.student))[0].study_year
        settings['onlyExam'] = Curriculum.objects.filter(course=exam.course)[0].only_exam
    except Exception, e:
        print e
    
    
    result = []
    for p in prijave:
        if not showVP and p.VP: continue
        prijava = {}
        prijava['id'] = p.id
        prijava['priimek'] = p.enroll.student.surname
        prijava['ime'] = p.enroll.student.name
        prijava['leto'] = str(p.enroll.study_year) + "/" + str(p.enroll.study_year + 1)
        prijava['vpisna_st'] = p.enroll.student.enrollment_number
        prijava['opcije']= p.RESULTS
        prijava['tockeIzpit'] = "0" if p.points == None else p.getPointsExam()
        prijava['tockeOstalo'] = "0" if p.points == None else p.getPointsOther()
        prijava['ocena_izpita'] = p.result_exam
        prijava['ocena_vaj']=p.result_practice
        prijava['negativno'] = p.resultNegative()

        stevilo_polaganj, odstevek_ponavljanja = _getPolaganja(p, p.enroll.student, exam.date) 
        polaganja_letos=exam.course.nr_attempts_this_year_till_now(p.enroll.student,exam.date)
        odstevek_ponavljanja = odstevek_ponavljanja if str(p.enroll.enrol_type) == "V2" else 0
        
        #aaa = (stevilo_polaganj - odstevek_ponavljanja, polaganja_letos)
        aaa = (stevilo_polaganj, polaganja_letos)
        
        prijava['polaganja'] = str(aaa[0]) + ((" - "+str(aaa[1])) if aaa[1]>0 else "")

        #polaganja = _getPolaganja(p, p.enroll.student, exam.date)
        #prijava['polaganja'] = str(polaganja[0]) + (("  "+str(polaganja[1])) if polaganja[1]>0 else "")
        #prijava['stevilo_polaganj'], prijava['odstevek_ponavljanja'] = _getPolaganja(p, p.enroll.student,p.examDate.date) 
        prijava['VP'] = p.VP

        result = result + [prijava]

    return render_to_response('admin/student/exam_grades.html', {'izpitnirok': exam, 'prijave':result, 's':settings}, RequestContext(request))
    
    

def exam_grades_fix(request, exam_Id, l, what, signup_Id, newValue): #show list of all objects
    signup_Id = int(signup_Id)
    signup=ExamSignUp.objects.get(id=signup_Id)

    try:
        #change data about signup
        if what=="1":
            signup.result_exam = newValue
            signup.save()
            if signup.resultNegative():
                signup.result_practice = "NR"
                signup.save()
        if what=="2":
            signup.result_practice = newValue
            signup.save()
            try:
                if int(newValue) <= 5:
                    signup.result_practice = "NR"
                    signup.save()
            except:
                pass
        if what=="3":
            signup.setPointsExam(int(newValue))
            signup.save()
        if what=="4":
            signup.setPointsOther(int(newValue))
            signup.save()
        if what=="5":
            if newValue == "0":
                signup.VP = True
            else:
                signup.VP = False
            signup.save()
    except Exception, e:#maybe an error msg?
        print e
    
    return exam_grades_view(request, exam_Id, l)

def class_list(request):
    
    class ClassForm(forms.Form):
        
        choices = []
        for c in Course.objects.all():
            choices.append((c.pk, c.__unicode__()))
        
        programs = []
        for p in StudyProgram.objects.all():
            programs.append((p.pk, p.__unicode__()))
        
        prog = forms.ChoiceField(choices=programs, label="Program")
        class_year = forms.IntegerField(label="letnik")
        cour = forms.ChoiceField(choices=choices, label="Izbirni predmet")
        year = forms.MultipleChoiceField(choices=[(2012, 2012), (2011, 2011), (2010, 2010), (2009, 2009)], label="Leto")
        
        
    students = []
    if request.method == 'POST':
        form = ClassForm(request.POST)
        if 'year' in request.POST:
            students = Enrollment.objects.filter(study_year__in = request.POST.getlist('year'), courses = request.POST['cour'], program = request.POST['prog']).order_by('student__surname')
            
        
    else:
        form = ClassForm()
        
    return render_to_response('admin/student/class_list.html', {'form':form, 'students': students}, RequestContext(request))


def exam_sign_up_index(request):
    student_enrolls = Student.objects.all()
    student_enrolls = "[ " + ", ".join([ '"' + str(s.pk) + '"' for s in student_enrolls]) + " ]"

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
            'error_message': "Student s to vpisno stevilko ne obstaja",
            'students':student_enrolls
            }, context_instance=RequestContext(request))

    except:
        return render_to_response('admin/student/exam_sign_up_index.html', {'students':student_enrolls}, context_instance=RequestContext(request))




def exam_sign_up(request, student_Id):
    s = get_object_or_404(Student, enrollment_number=student_Id)
    student = Student.objects.get(enrollment_number=student_Id)
    enroll= Enrollment.objects.filter(student=s)

    class EnrollForm(forms.Form):
        enrolls=[]
        ePk=[]

        for enroll in Enrollment.objects.filter(student=student):
                enrolls.append((enroll.pk, enroll.__unicode__()))

        enrolments=forms.ChoiceField(choices=enrolls, label="Vpisi")

    exams=[]
    if request.method == 'POST':
        form = EnrollForm(request.POST)
        enroll= Enrollment.objects.get(id=request.POST['enrolments'])
        classes=Course.objects.filter(curriculum__in=enroll.get_classes()  )
        examss=ExamDate.objects.filter(course__in=classes)
        for e in examss:
            if e.date.year>=datetime.date.today().year:
                if not e.already_positive(student) :
                    exams.append(e)

    else:
        form=EnrollForm()


    return render_to_response('admin/student/exam_sign_up.html', {'form':form,'Roki':exams, 'Student':student_Id, 'Vpis':enroll}, RequestContext(request))

def exam_sign_out(request, student_Id):
    s = get_object_or_404(Student, enrollment_number=student_Id)

    exist=ExamSignUp.objects.filter(examDate__in=s.get_current_exam_dates())

    #print str('neki')+str(exist)
    return render_to_response('admin/student/exam_sign_out.html', {'Prijave':exist}, RequestContext(request))
    
    
def student_index(request):
    student_enrolls = Student.objects.all()
    student_enrolls = "[ " + ", ".join([ '"' + str(s.pk) + '"' for s in student_enrolls]) + " ]"
    
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
            'error_message': "Student s to vpisno stevilko ne obstaja",
            'students':student_enrolls
            }, context_instance=RequestContext(request))
    except:
        return render_to_response('admin/student/student_index.html', {'students':student_enrolls}, context_instance=RequestContext(request))


def student_index_list(request, student_Id, display): #0=all, 1=last
    student = get_object_or_404(Student, enrollment_number=student_Id)

    response = []

    enrolls = Enrollment.objects.filter(student=student).order_by('program', 'study_year', 'class_year')
    prog = ""
    for enroll in enrolls:
        out={}
        out['program'] = enroll.program.descriptor
        # same program, don't repeat
        if prog != out['program']:
            out['noprogram'] = True
            prog = out['program']

        out['enrollment_type'] = enroll.enrol_type+' - '+enroll.get_enrol_type_display()
        out["redni"]="Redni" if enroll.regular else "Izredni"
        out["letnik"]=enroll.class_year
        out["study_year"]=enroll.class_year

        #out['enroll'] = enroll
        
        courses = []
        classes = enroll.get_classes()
        courses2 = Course.objects.filter(curriculum__in=classes).order_by('course_code')
        enrollsV2 = Enrollment.objects.filter(student = student,class_year = enroll.class_year, program = enroll.program)
        
        cntr = 0
        
        for p in courses2:
            try:
                course={}
                cntr += 1
                course["cntr"]=str(cntr) 
                course["name"]=p.name
                course["sifra_predmeta"]=p.course_code
                course["izvajalci"]=p.predavatelji()
                
                signs = []
                for enrollV2 in enrollsV2:
                    signups = ExamSignUp.objects.filter(examDate__course__course_code=p.course_code,enroll=enrollV2).order_by('examDate__date')
                    #signups = ExamSignUp.objects.filter(enroll=enrollV2).order_by('examDate__date')
                    signups = filter(lambda s: s.examDate.course.name == p.name, signups)
                    signups = filter(lambda s: (s.result_exam != "NR" and s.VP != True), signups)
                    
                    for s in signups:
                        polaganje={}
                        polaganje['datum']=s.examDate.date.strftime("%d.%m.%Y")
                        polaganje['izvajalci']=s.examDate.instructors
                        if(polaganje['izvajalci']==None):
                            polaganje['izvajalci']=p.predavatelji()
                        cur=Curriculum.objects.all().filter(course=p, program=enrollV2.program)[0]
                        if(cur.only_exam==True):
                            polaganje['ocena']=s.result_exam
                        else:
                            polaganje['ocena']=str(s.result_exam)+"/"+ str((s.result_practice if int(s.result_exam) > 5 else 0))

                        from api.views import _getPolaganja
                        aaa = _getPolaganja(s, student, s.examDate.date)

                        polaganje['stevilo_polaganj'], polaganje['odstevek_ponavljanja'] = _getPolaganja(s, student,s.examDate.date) 
                        polaganje['polaganja_letos']=s.examDate.course.nr_attempts_this_year_till_now(student,s.examDate.date)
                        polaganje['odstevek_ponavljanja'] = polaganje['odstevek_ponavljanja'] if str(enrollV2.enrol_type) == "V2" else 0
                        
                        #aaa = (polaganje['stevilo_polaganj'] - polaganje['odstevek_ponavljanja'], polaganje['polaganja_letos'])
                        aaa = (polaganje['stevilo_polaganj'], polaganje['polaganja_letos'])
                        
                        polaganje['polaganja'] = str(aaa[0]) + ((" - "+str(aaa[1])) if aaa[1]>0 else "")
                       
                        signs.append(polaganje)

                if (display == "1" and len(signs)>1):
                    signs = signs[-1:]

                course["signups"] = signs

                courses = courses+[course]
            except:
                raise
                pass
        out["courses"]=courses
        out["povprecje_izpitov"]=str(enroll.get_exam_avg())[0:5]
        out["povprecje_vaj"]=str(enroll.get_practice_avg())[0:5]
        out["povprecje"]=str(enroll.get_avg())[0:5]
        response = response + [out]
        
    return render_to_response('admin/student/student_index_list.html', {'student':student, 'data':response}, RequestContext(request))
    
    
    
def sign_up_confirm(request, student_Id, exam_Id, enroll_Id):
    student = get_object_or_404(Student, enrollment_number=student_Id)
    exam=ExamDate.objects.get(pk=exam_Id)
    enroll= Enrollment.objects.get(pk=enroll_Id)
    d = datetime.timedelta(days=14)

    error_msgs = exam.signUp_allowed(student)
    nr_this_year = exam.course.nr_attempts_this_year(student)
    nr_all = exam.course.nr_attempts_all(student)
    d14 = datetime.timedelta(days=14)
    nr_repeat = exam.course.repeat_class(student)
    clicked=False
    war=False


    message = {"msg":"","error":"", "warning":""}

    print str(exam.nr_SignUp) + str(len(ExamSignUp.objects.filter(examDate=exam)))

    #try:
    if 'prijava' in request.POST:
            clicked=True
            print exam.already_signedUp(student)
            print message
            if exam.already_positive(student):
                message["error"] = 'Napaka: Za ta predmet obstaja pozitivna ocena.'
                return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam, 'msg':message, 'clicked':clicked}, RequestContext(request))
            elif exam.already_signedUp(student):
                message["error"] = 'Za ta predmet obstaja prijava, ki nima ocene'
                return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam, 'msg':message, 'clicked':clicked}, RequestContext(request))

            elif nr_all - nr_repeat >= 6:
                war = True
                message["warning"] = 'Za ta predmet obstaja 6 polaganj.'
                return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam, 'msg':message, 'clicked':clicked, 'war':war}, RequestContext(request))

            elif nr_this_year >= 3:
                war = True
                message["warning"] = 'Obstajajo vsaj 3 polaganja v tem letu.'
                return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam, 'msg':message, 'clicked':clicked,'war':war}, RequestContext(request))


            elif exam.date < (datetime.date.today() + datetime.timedelta(days=3)):
                war=True
                message["warning"] = 'Rok za prijavo na izpit je potekel'
                return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam, 'msg':message, 'clicked':clicked, 'war':war}, RequestContext(request))

            elif len(ExamDate.objects.filter(examsignup=exam.last_try(student))) > 0 and exam.date < (ExamDate.objects.filter(examsignup=exam.last_try(student))[0].date + d14):
                message["warning"] = 'Ni preteklo 14 dni od zadnje prijave'
                war=True
                return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam, 'msg':message, 'clicked':clicked,'war':war}, RequestContext(request))

            elif int(exam.nr_SignUp) <= len(ExamSignUp.objects.filter(examDate=exam)):
                war= True
                message["warning"] = 'Omejitev dovoljenih prijav za ta izpitni rok'
                return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam, 'msg':message, 'clicked':clicked, 'war':war}, RequestContext(request))

            else:

                ExamSignUp.objects.create(enroll=enroll, examDate=exam).save()
                nr_all= exam.course.nr_attempts_all(student)
                message["msg"]='To je prijava st.:'+ str(nr_all)
                request.session['msg'] = message

                return HttpResponseRedirect(reverse('student.views.sign_up_success', args=[student.enrollment_number, int(exam_Id)]))
                #return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam, 'msg':message['msg']}, RequestContext(request))



    elif 'nazaj' in request.POST:

            return HttpResponseRedirect(reverse('student.views.exam_sign_up', args=(student.enrollment_number, )))

    elif 'prijavaForce' in request.POST:
        ExamSignUp.objects.create(enroll=enroll, examDate=exam).save()
        nr_all= exam.course.nr_attempts_all(student)
        message["msg"]='To je prijava st.:'+ str(nr_all)
        request.session['msg'] = message

        return HttpResponseRedirect(reverse('student.views.sign_up_success', args=[student.enrollment_number, int(exam_Id)]))

#    else:
#        print message
#        return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam, 'msg':message}, RequestContext(request))

    #return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam, 'msg':message['msg']}, RequestContext(request))



    return render_to_response('admin/student/exam_sign_up_confirm.html', {'Student':student, 'rok':exam}, RequestContext(request))

def sign_up_success(request, student_Id, exam_Id):
    student = get_object_or_404(Student, enrollment_number=student_Id)
    exam=ExamDate.objects.get(pk=exam_Id)
    msg = request.session.get('msg', None)
    return render_to_response('admin/student/exam_sign_up_success.html', {'Student':student, 'rok':exam, 'msg':msg}, RequestContext(request))

def student_personal(request, student_Id):
    student= Student.objects.get(enrollment_number = student_Id)
    enrollment = Enrollment.objects.filter(student = student_Id)
    phone = Phone.objects.filter(student = student)[0]
    address = Address.objects.filter(student = student)[0]
    return render_to_response('admin/student/student_personal.html', {'enrollment':enrollment,'student':student, 'phone':phone, 'address':address}, RequestContext(request))

