from django import template

register = template.Library()


@register.simple_tag
def get_verbose_field_name(instance, field_name):
    """
    Get the verbose_name for a field in a model instance

    Parameters
    ----------
    instance : Django models.Model
        An instance of any sub-class of a Django models.Model
    field_name : str
        Name of the field to return the verbose field name of.

    Returns
    -------
    str
        Verbose name of the field.
    """
    field = instance._meta.get_field(field_name)
    if hasattr(field, "verbose_name"):
        return field.verbose_name.title()
    else:
        return field.name.title()
