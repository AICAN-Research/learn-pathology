from resources.models import Tutorial

def tutorials_list(request):
    return {
        "tutorials": Tutorial.objects.all()
    }
