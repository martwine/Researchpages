#from django.core.template import register_tag, TemplateSyntaxError, Node
from django import template

register = template.Library()

	
class PushVarsNode(template.Node):	
    """This Node waits for itself to be rendered, calls `varfunc` 
    to get some variables, and pushes them into the Context."""
    
    def __init__(self, varfunc): 
        """Stash our variable generation function for later."""
        self.varfunc = varfunc
        
    def render(self, context):	
        """Call our variable generation function, update the context, and
        return an empty string."""
        vars = self.varfunc(context) # pass the context to varfunc
        context.update(vars) # implicit context.push
        return ''	
	
class PopVarsNode(template.Node):	
    """This Node waits for itself to be rendered, then pops the Context."""
    
    def render(self, context): 
        """Pop the context."""
        context.pop()
        return ''	
	
def do_pushvars(parser, token):	
    """Compilation function for the ``pushvars`` template tag, which 
    runs a nominated function and updates the context's variables with 
    the dictionary returned by that function::
    
        {% pushvars package.module.function %}
    """
    argv = token.contents.split()
    if len(argv)!=2:
        raise template.TemplateSyntaxError, "pushvars takes one argument"
    names = argv[1].split('.') # [package, module, function]
    function_name = names[-1] # function
    full_module_name = '.'.join(names[:-1]) # package.module
    module_name = names[-2] # module
    try: 
        module = __import__(full_module_name, {}, {}, module_name)
    except ImportError: 
        raise template.TemplateSyntaxError, \
                "pushvars: can't import %s" % full_module_name
    try: 
        function = getattr(module, function_name)
    except AttributeError: 
        raise template.TemplateSyntaxError, \
                "pushvars: can't find %s in %s" % (
                        full_module_name, 
                        functoin_name)
    return PushVarsNode(function)

def do_popvars(parser, token): 
    """Handle the ``popvars`` template tag, which pops the context::
    
        {% popvars %}
    """
    argv = token.contents.split()
    if len(argv) != 1: 
        raise template.TemplateSyntaxError, \
            "popvars takes no arguments"
    return PopVarsNode()
    
# Register our tags

register.tag('pushvars', do_pushvars)
register.tag('popvars', do_popvars)


