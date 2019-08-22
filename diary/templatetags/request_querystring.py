from django import template
from django.http import QueryDict

register = template.Library()


@register.simple_tag
def get_extendable_request_querystring(request):
    """
    Get the query string from a request and append `&` if it exists

    If a querystring exists, it is appended with a `&` for extension.
    If no querystring exists, the return is the empty string.

    Parameters
    ----------
    request :  django.http.HttpRequest

    Returns
    -------
    str
        Verbose name of the field.
    """
    querydict = QueryDict(request.GET.urlencode(), mutable=True)
    # querydict = request.GET
    # querydict.mutable = True
    if "page" in querydict:
        querydict.pop("page")
    querystring = querydict.urlencode()
    if querystring:
        return querystring + "&"
    else:
        return ""


# @register.simple_tag
# def get_full_querystring(request):
#     """
#     Get the querystring from a request with leading `?` or empty string

#     Parameters
#     ----------
#     request :  django.http.HttpRequest

#     Returns
#     -------
#     str
#         Querystring with leading `?` if a querystring could be extracted from
#         the request. Otherwise the empty string is returned.

#     """

#     querystring = request.GET.urlencode()
#     if querystring:
#         return "?" + querystring
#     else:
#         return ""
