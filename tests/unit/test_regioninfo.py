import pytest

from chalice.regioninfo import service_principal


@pytest.fixture
def region():
    return 'bermuda-triangle-42'


@pytest.fixture
def url_suffix():
    return '.nowhere.null'


@pytest.fixture
def non_iso_suffixes():
    return ['', '.amazonaws.com', '.amazonaws.com.cn']


def test_unmatched_service():
    assert service_principal('taco.magic.food.com',
                             None,
                             None) == 'taco.magic.food.com'


def test_defaults():
    assert service_principal('lambda') == 'lambda.amazonaws.com'


def test_states(region, url_suffix, non_iso_suffixes):
    services = ['states']
    for suffix in non_iso_suffixes:
        for service in services:
            assert service_principal('{}{}'.format(service, suffix), region,
                                     url_suffix) == '{}.{}.amazonaws.com'.format(
                service, region)


def test_codedeploy_and_logs(region, url_suffix, non_iso_suffixes):
    services = ['codedeploy', 'logs']
    for suffix in non_iso_suffixes:
        for service in services:
            assert service_principal('{}{}'.format(service, suffix), region,
                                     url_suffix) == '{}.{}.{}'.format(
                service, region, url_suffix)


def test_ec2(region, url_suffix, non_iso_suffixes):
    services = ['ec2']
    for suffix in non_iso_suffixes:
        for service in services:
            assert service_principal('{}{}'.format(service, suffix), region,
                                     url_suffix) == '{}.{}'.format(
                service, url_suffix)


def test_others(region, url_suffix, non_iso_suffixes):
    services = ['autoscaling', 'lambda', 'events', 'sns', 'sqs', 'foo-service']
    for suffix in non_iso_suffixes:
        for service in services:
            assert service_principal('{}{}'.format(service, suffix), region,
                                     url_suffix) == '{}.amazonaws.com'.format(
                service)


def test_local_suffix(region, url_suffix):
    assert service_principal('foo-service.local', region,
                             url_suffix) == 'foo-service.local'


def test_states_iso():
    assert service_principal('states.amazonaws.com', 'us-iso-east-1',
                             'c2s.ic.gov') == 'states.amazonaws.com'


def test_states_isob():
    assert service_principal('states.amazonaws.com', 'us-isob-east-1',
                             'sc2s.sgov.gov') == 'states.amazonaws.com'


def test_iso_exceptions():
    services = ['cloudhsm', 'config', 'workspaces']
    for service in services:
        assert service_principal('{}.amazonaws.com'.format(service),
                                 'us-iso-east-1',
                                 'c2s.ic.gov') == '{}.c2s.ic.gov'.format(
            service)
