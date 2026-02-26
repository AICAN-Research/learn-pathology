from django.http import FileResponse
from resources.models import Tutorial
from user.decorators import teacher_required


@teacher_required
def download_tutorial(request, tutorial_id):
    tutorial = Tutorial.objects.get(pk=tutorial_id)
    return FileResponse(tutorial.pdf.open(), as_attachment=True)
