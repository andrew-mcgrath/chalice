import re


def service_principal(service, region, url_suffix):
    # type: (str, str, str) -> str
    """Computes a "standard" AWS Service principal for a given set of arguments.

    Computes a "standard" AWS Service principal for a given service, region and
    suffix. This is useful for example when you need to compute a service
    principal name, but you do not have a synthesize-time region literal
    available (so all you have is `{ "Ref": "AWS::Region" }`). This way you get
    the same defaulting behavior that is normally used for built-in data.

    :param service: the name of the service (s3, s3.amazonaws.com, ...)
    :param region: the region in which the service principal is needed.
    :param url_suffix: the URL suffix for the partition in which the region is
    located.
    :return: The service principal for the given combination of arguments
    """
    matches = re.match(
        (
            r'^([^.]+)'
            r'(?:(?:\.amazonaws\.com(?:\.cn)?)|'
            r'(?:\.c2s\.ic\.gov)|'
            r'(?:\.sc2s\.sgov\.gov))?$'
        ), service)

    if matches is None:
        #  Return "service" if it does not look like any of the following:
        #  - s3
        #  - s3.amazonaws.com
        #  - s3.amazonaws.com.cn
        #  - s3.c2s.ic.gov
        #  - s3.sc2s.sgov.gov
        return service

    # Simplify the service name down to something like "s3"
    service = matches[1]

    # Exceptions for Service Principals in us-iso-*
    us_iso_exceptions = {'cloudhsm', 'config', 'states', 'workspaces'}

    # Exceptions for Service Principals in us-isob-*
    us_isob_exceptions = {'dms', 'states'}

    # Account for idiosyncratic Service Principals in `us-iso-*` regions
    if region.startswith('us-iso-') and service in us_iso_exceptions:
        if service == 'states':
            # Services with universal principal
            return '{}.amazonaws.com'.format(service)
        else:
            # Services with a partitional principal
            return '{}.{}'.format(service, url_suffix)

    # Account for idiosyncratic Service Principals in `us-isob-*` regions
    if region.startswith('us-isob-') and service in us_isob_exceptions:
        if service == 'states':
            # Services with universal principal
            return '{}.amazonaws.com'.format(service)
        else:
            # Services with a partitional principal
            return '{}.{}'.format(service, url_suffix)

    if service in ['codedeploy', 'logs']:
        return '{}.{}.{}'.format(service, region, url_suffix)
    elif service == 'states':
        return '{}.{}.amazonaws.com'.format(service, region)
    elif service == 'ec2':
        return '{}.{}'.format(service, url_suffix)
    else:
        return '{}.amazonaws.com'.format(service)
