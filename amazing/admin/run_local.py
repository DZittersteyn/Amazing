from django.core.management import call_command
call_command('syncdb', interactive=True)
call_command('runserver')
