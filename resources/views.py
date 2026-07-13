from django.http import FileResponse
from django.shortcuts import get_object_or_404
from resources.models import Tutorial
from user.decorators import teacher_required


@teacher_required
def download_tutorial(request, tutorial_id):
    tutorial = get_object_or_404(Tutorial, pk=tutorial_id)
    return FileResponse(tutorial.pdf.open(), as_attachment=True)
