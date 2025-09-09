from django.core.management import BaseCommand
from slide.models import Slide
from slide.views import create_thumbnail


class Command(BaseCommand):
    """

    Usage
    -----
    In the console, use the command:
    ```
    python manage.py recreate_thumbnails
    ```
    """

    help = 'Recreate thumbnails'

    def handle(self, *args, **options):
        slides = Slide.objects.all()
        for slide in slides:
            try:
                slide.load_image()  # This will load slide with FAST, so it is ready to use
                create_thumbnail(slide.image, f'thumbnails/{slide.id}.jpg')
                print('Thumbnail for', slide.id, 'recreated')
            except Exception as e:
                print('Failed to recreate thumbnail for ', slide.id, 'because: ', str(e))
