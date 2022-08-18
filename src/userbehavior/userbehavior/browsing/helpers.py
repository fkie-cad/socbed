#!/usr/bin/python3
# -*- coding: utf-8 -*-


def url_in_domain(url, domain, compare_depth=-1):
    """
    Check if the domain of url is a subdomain of 'domain'.
    Optionally the check runs up to a given non-negative depth.
    Special cases:
    If url begins with / or . then True is returned.
    If url is "" then False is returned.
    If domain is "" then True is returned.
    """

    # TypeErrors
    if not isinstance(url, str):
        raise TypeError("Incompatible type \'" +
                        type(url).__name__ + "\' of variable url.\
                        Should be \'str\'")
    if not isinstance(domain, str):
        raise TypeError("Incompatible type \'" +
                        type(domain).__name__ + "\' of variable domain.\
                        Should be \'str\'")

    if len(url) == 0:
        return False
    if url[0] == "/" or url[0] == "." or domain == "":
        return True

    # reverse and split domains at '.'
    url_list = list(reversed(get_domain_name(url).split(".")))
    domain_list = list(reversed(get_domain_name(domain).split(".")))

    # cut domains if necessary
    if compare_depth >= 0:
        url_list = url_list[:compare_depth]
        domain_list = domain_list[:compare_depth]

    # Check if domain path is equal
    if len(domain_list) > len(url_list):
        return False
    else:
        for i in range(len(domain_list)):
            if domain_list[i] != url_list[i]:
                return False

    # At this point, the url has the same domain path as domain
    return True


def get_domain_name(url, depth=-1):
    """Get domain of a url. Optionally up to a given depth."""

    # Check if string

    if not isinstance(url, str):
        raise TypeError("Incompatible type \'" +
                        type(url).__name__ + "\' of parameter url.\
                        Should be \'str\'")

    # Get rid of protocol at beginning
    tmp = url.split("://")
    if len(tmp) > 1:
        tmp = tmp[1]
    else:
        tmp = tmp[0]

    # get rid of file-path
    tmp = tmp.split("/")[0]

    # optionally cut depth
    if depth >= 0:
        if depth == 0:
            return ""
        else:
            tmp = ".".join(tmp.split(".")[-depth:])

    return tmp
