from collections import OrderedDict

import pytest

from chalice.awsclient import TypedAWSClient


@pytest.mark.parametrize('service,region,endpoint', [
    ('sns', 'us-east-1',
     OrderedDict([('partition', 'aws'),
                  ('endpointName', 'us-east-1'),
                  ('protocols', ['http', 'https']),
                  ('hostname', 'sns.us-east-1.amazonaws.com'),
                  ('signatureVersions', ['v4']),
                  ('dnsSuffix', 'amazonaws.com')])),
    ('sqs', 'cn-north-1',
     OrderedDict([('partition', 'aws-cn'),
                  ('endpointName', 'cn-north-1'),
                  ('protocols', ['http', 'https']),
                  ('sslCommonName', 'cn-north-1.queue.amazonaws.com.cn'),
                  ('hostname', 'sqs.cn-north-1.amazonaws.com.cn'),
                  ('signatureVersions', ['v4']),
                  ('dnsSuffix', 'amazonaws.com.cn')])),
    ('dynamodb', 'mars-west-1', None)
])
def test_resolve_endpoint(stubbed_session, service, region, endpoint):
    awsclient = TypedAWSClient(stubbed_session)
    assert endpoint == awsclient.resolve_endpoint(service, region)


@pytest.mark.parametrize('arn,endpoint', [
    ('arn:aws:sns:us-east-1:123456:MyTopic',
     OrderedDict([('partition', 'aws'),
                  ('endpointName', 'us-east-1'),
                  ('protocols', ['http', 'https']),
                  ('hostname', 'sns.us-east-1.amazonaws.com'),
                  ('signatureVersions', ['v4']),
                  ('dnsSuffix', 'amazonaws.com')])),
    ('arn:aws-cn:sqs:cn-north-1:444455556666:queue1',
     OrderedDict([('partition', 'aws-cn'),
                  ('endpointName', 'cn-north-1'),
                  ('protocols', ['http', 'https']),
                  ('sslCommonName', 'cn-north-1.queue.amazonaws.com.cn'),
                  ('hostname', 'sqs.cn-north-1.amazonaws.com.cn'),
                  ('signatureVersions', ['v4']),
                  ('dnsSuffix', 'amazonaws.com.cn')])),
    ('arn:aws:dynamodb:mars-west-1:123456:table/MyTable', None)
])
def test_endpoint_from_arn(stubbed_session, arn, endpoint):
    awsclient = TypedAWSClient(stubbed_session)
    assert endpoint == awsclient.endpoint_from_arn(arn)


@pytest.mark.parametrize('service,region,dns_suffix', [
    ('sns', 'us-east-1', 'amazonaws.com'),
    ('sns', 'cn-north-1', 'amazonaws.com.cn'),
    ('dynamodb', 'mars-west-1', 'amazonaws.com')
])
def test_endpoint_dns_suffix(stubbed_session, service, region, dns_suffix):
    awsclient = TypedAWSClient(stubbed_session)
    assert dns_suffix == awsclient.endpoint_dns_suffix(service, region)


@pytest.mark.parametrize('arn,dns_suffix', [
    ('arn:aws:sns:us-east-1:123456:MyTopic', 'amazonaws.com'),
    ('arn:aws-cn:sqs:cn-north-1:444455556666:queue1', 'amazonaws.com.cn'),
    ('arn:aws:dynamodb:mars-west-1:123456:table/MyTable', 'amazonaws.com')
])
def test_endpoint_dns_suffix_from_arn(stubbed_session, arn, dns_suffix):
    awsclient = TypedAWSClient(stubbed_session)
    assert dns_suffix == awsclient.endpoint_dns_suffix_from_arn(arn)