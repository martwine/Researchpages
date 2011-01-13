from django.utils.encoding import smart_unicode

def textify(html_snippet, maxwords):
    import formatter, htmllib, StringIO, string

    class Parser(htmllib.HTMLParser):
        def anchor_end(self):
            self.anchor = None

    class Formatter(formatter.AbstractFormatter):
        pass

    class Writer(formatter.DumbWriter):
        def send_label_data(self, data):
            self.send_flowing_data(data)
            self.send_flowing_data(" ")

    o = StringIO.StringIO()
    p = Parser(Formatter(Writer(o)))
    p.feed(smart_unicode(html_snippet))
    p.close

    words = smart_unicode(o.getvalue()).split()

    if len(words) < maxwords:
        return string.join(words)
    
    return string.join(words[:maxwords]) + "..."
