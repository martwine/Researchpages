from django import template
from django.utils.encoding import smart_unicode
import re
import cgi
import string

register = template.Library()

# register the templatetag
@register.filter("wikify") 
def wikify(content, group):
    out = u''
    for rt in string.split(content,"\n"):
        # link  [[URL]] 
        try:
            rt = re.sub('\[\[([^\]|]*)\]\]',u'<a href="%s/wiki/\\1">\\1</a>' % group.get_absolute_url(),rt)
        except:pass
        # link with title [[URL|TITLE]]
        try:
            rt = re.sub('\[\[([^\]|]*)\|([^\]]*)\]\]',u'<a href="%s/wiki/\\1">\\2</a>' % group.get_absolute_url(),rt)
        except:pass
        # image {{IMG}}
        try: 
            rt = re.sub('\{\{([^\]|]*)\}\}',u'<img src="\\1" alt=""/>',rt)
        except:pass
        # h2 ==H2==
        try:
            rt = re.sub('^==([^=]*)==$',u'<h2>\\1</h2>',rt)
        except:pass
        # h3 ===H3===
        try:
            rt = re.sub('^===([^=]*)===$',u'<h3>\\1</h3>',rt)
        except:pass
        # h4  ====H4====
        try:
            rt = re.sub('^====([^=]*)====$',u'<h4>\\1</h4>',rt)
        except:pass
        # code [code]SOME CODE[/code]
        try:
            rt = re.sub('^\[code\]([^\]]*)\[/code\]$',u'@\\1@',rt)
        except:pass
        out +=  smart_unicode(rt, encoding='utf-8', strings_only=False,
                errors='strict') 
    return smart_unicode(out, encoding='utf-8', strings_only=False,
            errors='strict')

