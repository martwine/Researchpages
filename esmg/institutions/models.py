from django.db import models
from django.utils.encoding import smart_unicode

class Institution(models.Model):
    name = models.CharField(maxlength=200, unique=True)
    
    class Admin:
        pass

    class Meta:
        ordering = ['name']

    def __unicode__(self):
        return self.name


class Division(models.Model):
    name = models.CharField(maxlength=200, core=True, unique=False)

    class Admin:
        pass
    
    def __unicode__(self):
        return self.name

class Instdiv(models.Model):
    institution = models.ForeignKey(Institution)
    division = models.ForeignKey(Division)

    class Meta:
        unique_together = (("institution", "division"),)

    class Admin:
        pass
    
    def __unicode__(self):
        if self.division:
            return smart_unicode(self.institution) +', ' + smart_unicode(self.division)
        else:
            return smart_unicode(self.institution) 


class Subdivision(models.Model):
    name = models.CharField(maxlength=200, blank=True)
    instdiv = models.ForeignKey(Instdiv)
    
    class Admin:
        pass

    class Meta:
        unique_together = (("instdiv", "name"),)
    
    def __unicode__(self):
        if self.name:
            return smart_unicode(self.instdiv) + ', ' + smart_unicode(self.name)
        else:
            return smart_unicode(self.instdiv)

