from django.utils.encoding import smart_unicode
                        
from django.db import models
from django.conf import settings
from django.contrib.auth.models import User
from datetime import datetime

RESOURCE_TYPE_CHOICES = (
    ('pic', 'Image / graphic'),
    ('pub', 'esmg scientific publication'),
    ('doc', 'Other document'),
    ('res', 'Other resource')
)

class Tree(models.Model):
    #import Group and Person here to avoid recursive loading when adding Trees
    #after creating Groups and People
    from esmg.groups.models import Group
    from esmg.people.models import Person
    
    #fields
    identifier = models.CharField(maxlength=100, unique=True)
    type = models.CharField(maxlength=10, blank=False)
    group = models.ForeignKey(Group, null=True, blank=True)
    person = models.ForeignKey(Person, null=True, blank=True)
    css = models.URLField(blank=True)

    class Admin:
        pass

    def __unicode__(self):
        return self.identifier

# Do all of this with treecreate()
    #def save(self):
    #    """Create top level pages for new trees.
    #    NEEDS TO update uri's of trees when
    #    identifier changes
    #    """
    #    from esmg.apparatus.models import Page
    #    try:
    #        #update pages if tree already exists
    #        t = Tree.objects.get(id=self.id)
    #        id = t.identifier
    #        p=Page.objects.get(identifier=id)
    #        p.identifier = self.identifier
    #        p.save()
    #        super(Tree, self).save()
    #    except:
    #        super(Tree, self).save()
    #        #create new 'treetop' page if not
    #        p=Page(identifier=self.identifier, is_tree_top=True)
    #        p.save()

def treecreate(identifier, type, group, person, editor, css):
    try:
        t = Tree.objects.get(identifier=identifier)
        treeupdate(identifier,t.identifier,editor,css)
    except Tree.DoesNotExist:
        if type=='person':
            t = Tree(identifier=identifier, type=type, group=None,
                    person=person, css=css)
            t.save()
            p = Page(identifier=identifier, is_tree_top=True, editor=editor,
                    is_person_page=True, tree=t, disabled=False, private=False)
        else:
            t = Tree(identifier=identifier, type=type, group=group,
                person=None, css=css)
            t.save()
            p = Page(identifier='', editor=editor, is_person_page=False,
                    is_tree_top=True, tree=t, disabled=False, private=False)
        p.save()

def treeupdate(identifier, treeid, editor, css):
    t = Tree.objects.get(id=treeid)
    t.identifier = identifier
    t.css = css
    p = Page.objects.get(tree=t, is_tree_top=True)
    p.identifier=identifier
    p.editor=editor
    t.save()
    p.save()

        



class Page(models.Model):
    """Represent a CMS page. This model is a metadata object, the real page
    content is in the current associated PageContent object.
    
    """
    from esmg.people.models import Person
    parent = models.ForeignKey('self', null=True, related_name='child_set',
            blank=True)
    identifier = models.SlugField(blank=True)
    editor = models.ForeignKey(Person, related_name='page_editorship')
    subeditor = models.ForeignKey(Person, related_name='page_subeditorship',
            blank=True, null=True)
    subeditor2 = models.ForeignKey(Person, related_name='page_subeditorship2',
            blank=True, null=True)
    locked_by = models.ForeignKey(Person, related_name='locked_pages', blank=True,
            editable=False, null=True)
    locked_time = models.DecimalField(max_digits=12, decimal_places=0, blank=True, 
            editable=False, null=True)
    disabled = models.BooleanField()
    private = models.BooleanField()
    uri = models.CharField(maxlength=200, editable=False, blank=True)
    is_tree_top = models.BooleanField(editable=False)
    tree = models.ForeignKey(Tree, editable=False, blank=True)
    is_person_page = models.BooleanField(editable=False, blank=True)
    css = models.URLField(blank=True)

    
    class Admin:
        pass
    
    
    def __unicode__(self):
        return self.get_absolute_url()

    def get_absolute_url(self):
        return settings.URLBASE + self.uri
    
    def save(self):
        from esmg.people.models import Person
        """If my identifier has changed, ask all child records to update their
        url fields before saving. I page has been disabled, disable all child
        pages too"""
        
        if self.private:
            self.privatisechildren()
        super(Page, self).save()
        #else:
        #    self.nationalisechildren()
        #    super(Page, self).save()

        if self.disabled:
            self.disablechildren()
            super(Page, self).save()
        
        if self.tree:
            self.update_child_tree(self.id)
            super(Page, self).save()
            
        if self.parent:
            new_uri = self.parent.uri + self.identifier + "/"
            self.uri = new_uri
            if self.parent.is_person_page and not self.is_person_page:
                self.is_person_page = True
            super(Page, self).save()
            self.update_child_uri(self.id, new_uri)

        elif self.is_person_page:
            self.uri='/people/' + self.identifier +'/'
            super(Page, self).save()
            self.update_child_uri(self.id, self.uri)

        elif self.is_tree_top and not self.uri=='/':
            self.uri = "/" + self.tree.identifier + "/" 
            super(Page, self).save()
            self.update_child_uri(self.id, self.uri)

        else:
            self.uri = "/"
            super(Page, self).save()
        
    def send_notification(self, status):
        from esmg.groups.models import Group
        from esmg.people.models import Person
        from esmg.comms.models import send_notification
        new = status == "new"
        
        #for personal pages 
        if self.is_person_page and not self.private:
            person = self.tree.person
            persongroups=Group.objects.filter(membership__person=person)
            recipients = person.friends.all() | Person.objects.filter(membership__group__in=persongroups) | Person.objects.filter(user__is_superuser=True)
            if new:
                notification_type = "New page by " + str(self.pcontent.latest().last_editor)
            else:
                notification_type = "Page update by " + str(self.pcontent.latest().last_editor)
            from_name = smart_unicode(person)
        
        #for group pages
        if self.tree.group:
            group = self.tree.group
            if self.private:
                recipients = Person.objects.filter(membership__group=group) | Person.objects.filter(user__is_superuser=True)
                
            else:
                recipients = Person.objects.filter(membership__group=group) | Person.objects.filter(watched_groups=group) | Person.objects.filter(user__is_superuser=True)
            if new:
                notification_type = "New " + smart_unicode(group)  + " page by " + smart_unicode(self.pcontent.latest().last_editor)
            else:
                notification_type = smart_unicode(group) + " page update by " + str(self.pcontent.latest().last_editor)
            from_name = smart_unicode(group)
        else:
            recipients=Person.objects.none()
            from_name=""
            notification_type=""
        email = False
        url = self.get_absolute_url()
        from_email = ""
        email_recipients = ""
        if not recipients==[]:
            send_notification(from_name,from_email,notification_type,recipients,email_recipients,self.pcontent.latest().title,self.pcontent.latest().body,url,email)
       
    def disablechildren(self):
        for child in Page.objects.filter(parent__id__exact=self.id):
            child.disabled = True
            child.save()

    def privatisechildren(self):
        for child in Page.objects.filter(parent__id__exact=self.id):
            child.private = True
            child.save()

    def nationalisechildren(self):
        for child in Page.objects.filter(parent__id__exact=self.id):
            child.private = False
            child.save()

    def undisable(self):
        """Call this no a page instance to undisable this page and all their children,
        and all their children's children, and all their children's children's
        children, and all thier chil..."""
        self.disabled = False
        self.save()
        for child in Page.objects.filter(parent__id__exact=self.id):
            child.undisable()
            
    def update_child_uri(self, parent_id, parent_uri):
        """Update uri and cause all child pages to do the same (in page save
        method)."""
        parent = Page.objects.get(id=parent_id)
        for child in parent.child_set.all():
            child_uri = parent_uri + child.identifier + "/"
            child.uri = child_uri
            child.save()
            #super(Page, child).save()
            #child.update_child_uri(child.id, child_uri)
    
    def update_child_tree(self, parent_id):
        """If tree has changed (i.e. in complicated move, update child trees)"""
        parent = Page.objects.get(id=parent_id)
        tree = parent.tree
        for child in parent.child_set.all():
            child.tree = tree
            child.save()
            
    def is_editor(self, user):
        """Return true if user can edit this page."""
        return not user.is_anonymous() and \
                ((user.is_staff or user.is_superuser) or \
                (user.id == self.editor_id) or \
                (user.id == self.subeditor_id) or \
                (user.id == self.subeditor2_id) or \
                (self.parent and self.parent.is_editor(user)) or \
                (self.tree.type == "group" and \
                self.tree.group.editor == user.person) or \
                (self.tree.type == "group" and \
                self.tree.group.project_leader == user.person) or \
                (self.tree.type == "person" and \
                self.is_tree_top and \
                user.person.is_group_leader(self.tree.person))
                )
    
    def get_css(self):
        if self.css:
            return self.css
        elif self.tree.css:
            return self.tree.css
        else:
            return settings.DEFAULT_CSS
    
    def get_logo(self):
        if self.tree.type == 'group':
            return self.tree.group.get_logo_url()
        else:
            return settings.DEFAULT_LOGO

class PageContent(models.Model):
    from esmg.people.models import Person
    page = models.ForeignKey(Page, related_name="pcontent",
            edit_inline=models.STACKED)
    title = models.CharField(maxlength=100)
    body = models.TextField(core=True)
    time = models.DateTimeField(editable=False)
    version = models.PositiveIntegerField(editable=False)
    last_editor = models.ForeignKey(Person, null=True, editable=False)
    #current = models.BooleanField(editable=False)
    
    


    def save(self):
        if not self.version:       
            versioncount = PageContent.objects.filter(page=self.page.id).count() 
            self.version = versioncount + 1 
        
        self.time = datetime.now()
        super(PageContent, self).save()
                
    def __unicode__(self):
        return self.title + " on " + smart_unicode(self.page)

    def htime(self):
        return smart_unicode(self.time)

    class Meta:
        get_latest_by = "time"
        ordering = ['-version']
    

class Sidebar(models.Model):
    from esmg.people.models import Person
    from esmg.groups.models import Group
    name = models.CharField(maxlength=50, blank=False, unique=True)
    creator = models.ForeignKey(Person)
    body = models.TextField()
    time = models.DateTimeField(editable=False)
    group = models.ForeignKey(Group, blank=True, null=True, editable=False) 
    person_only = models.BooleanField()
    class Meta:
        ordering = ['-time']
        
    def is_editor(self, user):
        """Return true if user can edit this page."""
        return user.is_staff or user.is_superuser or user.id == self.creator_id
    
    def save(self):
        self.time = datetime.now()
        super(Sidebar, self).save()
    
    def __unicode__(self):
        return self.name

    def get_edit_url(self):
        return "%s/sidebars/%s/edit/" % (settings.URLBASE, self.id)


class Sidebarjoin(models.Model):
    page = models.ForeignKey(Page)
    sidebar = models.ForeignKey(Sidebar, core=True,)

    class Meta:
        order_with_respect_to = 'page'
        unique_together = (("page", "sidebar" ),)

