from itertools import chain


def to_dict(instance):
    """
    Convert a model instance to a dictionary of field names and values

    This function is taken from this SO thread:  https://stackoverflow.com/questions/21925671/convert-django-model-object-to-dict-with-all-of-the-fields-intact
    I need this functionality to be able to send a POST request to a view and
    have sensible data. The data represents what the rendered from would
    contain. To avoid having to duplicate every field that the form would
    contain this function can be used to create a data payload for the POST.

    This function is basically the same as `django.forms.models.model_to_dict`,
    with the difference that the items in the many-to-many fields are
    represented by their id and not as objects.

    :param instance: Instance of the model that should be converted to a dict.
    :return: Dictionary with the model field names as keys and field values
             as values.
    """
    options = instance._meta
    data = {}
    # Add the normal and private fields to the dictionary
    for field in chain(options.concrete_fields, options.private_fields):
        data[field.name] = field.value_from_object(instance)
    # Add ids of the many-to-many relations.
    for field in options.many_to_many:
        # Since there can be many entries for many-to-many field, these items
        # have to be iterated too.
        data[field.name] = [item.id
                            for item in field.value_from_object(instance)]
    return data
