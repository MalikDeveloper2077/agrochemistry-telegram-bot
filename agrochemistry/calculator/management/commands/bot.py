from django.core.management import BaseCommand

from agrochemistry.settings import TG_TOKEN
from calculator.bot.bot import get_updater


class Command(BaseCommand):
    def handle(self, *args, **kwargs):
        updater = get_updater(token=TG_TOKEN)
        updater.start_polling()
        updater.idle()
