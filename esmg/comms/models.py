from django.utils.encoding import smart_unicode
from django.db import models
from django.template import Context
from django.contrib.auth.models import User
from django.conf import settings
from datetime import datetime
from esmg.groups.models import Group
from esmg.people.models import Person
from afternoon.django.mail import send_html_mails

ITEM_PERMISSION_CHOICES = (
    ('prvt', 'Private - visible to only person or group'),
    ('rstrc', 'Restricted - Visible only to people connected to you i.e. friends and group members'),
    ('pblc', 'Public - visible to everyone'),
)                

textile_help_text = "<p class=\"form-note\">The content for this page. You can use \
          <a href=\"http://hobix.com/textile/\" target=\"_blank\">Textile</a> \
          to format your text, or just write plain text if you prefer.</p> <p \
          class=\"form-hint\"><em>Textile</em>: Please try to use\
          basic formatting only - e.g. use heading styles h2 or h3 (e.g \
          \"h2. Your Subtitle\", the main heading being the title field of this\
          form),  and avoid fixing the size or color of your text \
          unless you have a very good reason - the formatting and color of your\
          content will be controlled by stylesheets which may vary and your\
          fixed text may end up looking bad! Bold, underline, italic; links, \
          lists, tables and images are all fine. Ultimately, this is your \
          content, to do with what you wish, so don't be afraid to experiment,\
          but do consider that simple, clean design is the best way to get your\
          message across. The person in charge of your group or project may \
          have more specific requirements of your content on group pages - you \
          should consult with them before doing anything too outlandish! \
          Another good textile reference can be found \
          <a href=\"http://www.brajeshwar.com/reference/mtmanual_textile2.html\">here</a> \
          </p></p>"
        
def send_notification(from_name, from_email, notification_type,
        recipients,email_recipients,title,body,url,email):
    """Recipients should be a queryset of people, email a boolean True or False"""
    # we need to turn this into a queryset of users, as MtM relationship mot
    # possible with Person as it has no pk values (due to being OnetoOne with
    # User)
    user_recipients=User.objects.filter(person__in=recipients)
    user_email_recipients=User.objects.filter(person__in=email_recipients)
    note = Notification(from_name=from_name, from_email=from_email,
            notification_type=notification_type, title=title, body=body,
            url=url, send_email=email)
    note.pre_save()
    for recipient in user_recipients:
        note.recipients.add(recipient)
        note.unread_recipients.add(recipient)
    for recipient in user_email_recipients:
        note.email_recipients.add(recipient)
    note.save()

class ForumThread(models.Model):
    group = models.ForeignKey(Group, blank=True, null=True)
    globalthread = models.BooleanField()

class Item(models.Model):
    type = models.CharField(maxlength=10, blank=False, editable=False)
    group = models.ForeignKey(Group, null=True, blank=True, editable=False)
    person = models.ForeignKey(Person, null=True, blank=True, editable=False)
    forum = models.ForeignKey(ForumThread, null=True, blank=True, editable=False)
    creator = models.ForeignKey(Person, related_name='creator_item_set',
            editable=False)
    title = models.CharField(maxlength=100, blank=False)
    body = models.TextField(help_text=textile_help_text)
    time = models.DateTimeField(editable=False)
    permissions = models.CharField(maxlength=5, choices=ITEM_PERMISSION_CHOICES)
    
    class Meta:
        ordering = ['-time']
    
    def is_item_editor(self,user):
        """Returns true if user can edit this item"""
        if user.is_anonymous():
            return False
        if self.group:
            grouptest = user.person == self.group.project_leader or user.person == self.group.editor
        return user.is_staff or user.is_superuser or user.id == self.creator_id
    
    def save(self):
        self.time = datetime.now()
        super(Item, self).save()
        
        
        if self.type == "Blog" and self.permissions == "prvt":
            pass

        elif self.type == "Blog":
            persongroups=Group.objects.filter(membership__person=self.person)
            recipients = self.person.friends.all() | Person.objects.filter(membership__group__in=persongroups)
            email_recipients = self.person.friends.all()
            if not self.id:
                email=True
                notification_type = "Blog post by " + smart_unicode(self.person)
            else:
                email=False
                notification_type = "Blog post update " + smart_unicode(self.person)
            from_email=smart_unicode(self.person) + "_blog@researchpages.net"
            url=settings.URLBASE + "/people/" + self.person.slug + "/blog/" + smart_unicode(self.id) + "/"
            from_name = smart_unicode(self.person)
            
            send_notification(from_name,from_email,notification_type,recipients,email_recipients,self.title,self.body,url,email)

        elif self.type == "News" or self.type == "Event":
            if self.permissions == "prvt":
                recipients = Person.objects.filter(membership__group=self.group)
            else:
                recipients = Person.objects.filter(membership__group=self.group) | Person.objects.filter(watched_groups=self.group)
            if not self.id:
                email=True
            else:
                email=False
            email_recipients = recipients
            from_name=smart_unicode(self.creator)
            if self.type == "News":
                from_email=smart_unicode(self.group) + "_news@researchpages.net"
                notification_type = smart_unicode(self.group) + " news item"
                url=settings.URLBASE  + "/" + smart_unicode(self.group) + "/news/" + smart_unicode(self.id) + "/"
                
            else:
                from_email=smart_unicode(self.group) + "_events@researchpages.net>"
                notification_type = smart_unicode(self.group) + " event info"
                url=settings.URLBASE  + "/" + str(self.group.acronym) + "/events/" + str(self.id) + "/"
        
            send_notification(from_name,from_email,notification_type,recipients,email_recipients,self.title,self.body,url,email)
        

    def __unicode__(self):
        return self.title

    def has_comments(self):
        return self.comment_set.count() > 0 

class Comment(models.Model):
    item = models.ForeignKey(Item, editable=False)
    person = models.ForeignKey(Person, editable=False)
    body = models.TextField()
    time = models.DateTimeField(editable=False)
    
    class Meta:
        ordering = ['time']
        
    def is_comment_editor(self,user):
        """Returns true if user can edit this item"""
        return user.is_staff or user.is_superuser or user.id == self.creator_id
    
    def save(self):
        self.time = datetime.now()
        super(Comment, self).save()

    def __unicode__(self):
        return self.body

    
class Notification(models.Model):
    """note that recipients are Users, not Persons - due to Person model not
    having a primary key. This is likely to catch is out later!"""
    from_email=models.CharField(maxlength=100, blank=True)
    from_name=models.CharField(maxlength=100)
    notification_type=models.CharField(maxlength="150")
    unread_recipients=models.ManyToManyField(User, blank=True,
            related_name="unread_notifications")
    recipients=models.ManyToManyField(User, blank=False)
    email_recipients=models.ManyToManyField(User, blank=True, related_name="emailed_notifications", null=True)
    title=models.CharField(maxlength=100, blank=False)
    body=models.TextField(blank=True)
    url=models.URLField(blank=True)
    send_email=models.BooleanField()
    timestamp = models.DateTimeField()


    class Meta:
        get_latest_by = 'timestamp'
        ordering = ['-timestamp']
    
    def __unicode__(self):
        return smart_unicode(self.notification_type) + u": " + smart_unicode(self.title)
    
    def person_recipients(self):
        """returns queryset of recipients as people not users"""
        p = Person.objects.filter(user__in=self.recipients)
        return p

    def pre_save(self):
        self.timestamp = datetime.now()
        super(Notification, self).save()
        
    def save(self):
        if self.send_email:
            subject="[researchpages] " + self.title
            text="comms/notification_text.txt"
            html="comms/notification_text.html"
            sender=self.from_name + "<" + self.from_email + ">"
            
            for recipient in self.email_recipients.all():
                ctx={"body" : self.body, "url" : self.url, "recipient" :
                    recipient.person, "title":self.title, "type":self.notification_type,
                    "from":self.from_name}
                def notification_gen():
                    yield (recipient.email,sender,self.title, text, html, Context(ctx),self.url)
                send_html_mails(settings.EMAIL_HOST,
                        settings.EMAIL_HOST_USER,
                        settings.EMAIL_HOST_PASSWORD,notification_gen)
        super(Notification, self).save()
