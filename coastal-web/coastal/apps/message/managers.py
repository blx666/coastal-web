from django.db import models


class DialogueManager(models.Manager):
    def get_queryset(self):
        return super(DialogueManager, self).get_queryset().filter(is_deleted=False)

    def get_all_queryset(self):
        return self._queryset_class(self.model, using=self._db, hints=self._hints)