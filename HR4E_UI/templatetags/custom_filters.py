from django import template
register = template.Library()


@register.filter(name='addcss')
def addcss(field, css):
    return field.as_widget(attrs={"class":css})

@register.filter(name='addDangerModel')
def addDangerModel(field, model):
    return field.as_widget(attrs={"ng-model":"question."+model, "class":"alert-danger"})

@register.filter(name='addModel')
def addModel(field, model):
    return field.as_widget(attrs={"ng-model":"question."+model})