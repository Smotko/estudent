from django.utils.text import capfirst
from django.db.models import get_models
from django.utils.safestring import mark_safe
from django.contrib.admin import ModelAdmin
from django.contrib.admin.validation import validate
from django.utils.translation import ugettext as _

# get_models returns all the models, but there are some which we would like to ignore
IGNORE_APPS = (
    "sites",
    "sessions",
    "admin",
    "contenttypes",
    'south',
)
IGNORE_MODEL = (
    "Message",
    "Permission",
    "Address",
    "Phone",
)

def app_list(request):
    '''
    Get all models and add them to the context apps variable.
    '''
    user = request.user
    app_dict = {}
    admin_class = ModelAdmin
    for model in get_models():
        validate(admin_class, model)
        model_admin = admin_class(model, None)
        app_label = model._meta.app_label
        if app_label in IGNORE_APPS:
            continue
        if model.__name__ in IGNORE_MODEL:
            continue
        has_module_perms = user.has_module_perms(app_label)
        if has_module_perms:
            perms = model_admin.get_model_perms(request)
            # Check whether user has any perm for this module.
            # If so, add the module to the model_list.
            if True in perms.values():
                model_dict = {
                    'name': capfirst(model._meta.verbose_name_plural),
                    'admin_url': mark_safe('%s/%s/' % (app_label, model.__name__.lower())),
                }
                if app_label in app_dict:
                    app_dict[app_label]['models'].append(model_dict)
                else:
                    app_dict[app_label] = {
                        'name': app_label.title(),
                        'app_url': app_label + '/',
                        'has_module_perms': has_module_perms,
                        'models': [model_dict],
                }
                    
    def in_groups(group_names):
        if user.is_authenticated():
            if bool(user.groups.filter(name__in=group_names)) or user.is_superuser:
                return True
        return False
    # Add custom views:
    if in_groups(('referentka','profesorji')):
#        model_dict = {
#            'name': capfirst(_("Vpis ocen")),
#            'admin_url': mark_safe('%s/%s/' % ('student', 'ExamGrades')),
#        }
#        app_dict['student']['models'].append(model_dict)

        model_dict = {
            'name': capfirst(_("Seznam za izbirne predmete")),
            'admin_url': mark_safe('%s/%s/' % ('student', 'ClassList')),
        }
        app_dict['student']['models'].append(model_dict)

        model_dict = {
            'name': capfirst(_("Prijava na izpit")),
            'admin_url': mark_safe('%s/%s/' % ('student', 'ExamSignUp')),
        }
        app_dict['student']['models'].append(model_dict)
    
        model_dict = {
            'name': capfirst(_("Kartotecni list")),
            'admin_url': mark_safe('%s/%s/' % ('student', 'StudentIndex')),
        }
        app_dict['student']['models'].append(model_dict)

    app_list = app_dict.values()

    app_list.sort(key=lambda x: x['name'])
    for app in app_list:
        app['models'].sort(key=lambda x: x['name'])
    return {'apps': app_list}
