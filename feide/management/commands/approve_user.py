from django.core.management import BaseCommand
from feide.models import ApprovedUser


class Command(BaseCommand):
    """

    Usage
    -----
    In the console, use the command:
    ```
    python manage.py approve_user smistad@ntnu.no
    ```
    """

    help = 'Add a user on the approve list'

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument('username', type=str, help='Username')

    def handle(self, *args, **options):
        try:
            user = ApprovedUser()
            user.username = options['username']
            user.save()
            print(f'User {user.username} was added to list of approved users.')
        except Exception as e:
            print('Exception occured while trying to add user to approve list: ' + str(e))


