import re

# Exceptions for Service Principals in us-iso-*
US_ISO_EXCEPTIONS = {'cloudhsm', 'config', 'states', 'workspaces'}

# Exceptions for Service Principals in us-isob-*
US_ISOB_EXCEPTIONS = {'dms', 'states'}


def service_principal(service, region, url_suffix) -> str:
    # type: (str, str, str) -> str
    """

    Computes a "standard" AWS Service principal for a given service, region and
    suffix. This is useful for example when you need to compute a service
    principal name, but you do not have a synthesize-time region literal
    available (so all you have is `{ "Ref": "AWS::Region" }`). This way you get
    the same defaulting behavior that is normally used for built-in data.

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

    # Account for idiosyncratic Service Principals in `us-iso-*` regions
    if region.startswith('us-iso-') and service in US_ISO_EXCEPTIONS:
        if service == 'states':
            # Services with universal principal
            return '{}.amazonaws.com'.format(service)
        else:
            # Services with a partitional principal
            return '{}.{}'.format(service, url_suffix)

    # Account for idiosyncratic Service Principals in `us-isob-*` regions
    if region.startswith('us-isob-') and service in US_ISOB_EXCEPTIONS:
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
