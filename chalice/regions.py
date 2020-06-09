# Copyright 2014 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
# http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
"""Resolves regions and endpoints.

This module implements endpoint resolution, including resolving endpoints for a
given service and region and resolving the available endpoints for a service
in a specific AWS partition.

This file was 'vendored' from botocore core botocore/botocore/regions.py from
commit 0c55d6c3f900fc856e818f06b31c22c6dbc56788. The vendoring/duplication
was due to the concern of utilizing a unexposed class internal to the botocore
library for functionality necessary to implicitly support partitions within
the chalice microframework. More specifically the determination of the dns
suffix for service endpoints based on service and region.

https://github.com/boto/botocore/tree/0c55d6c3f900fc856e818f06b31c22c6dbc56788
"""
import logging
import re
from typing import List, Dict, Any # noqa

from botocore.exceptions import NoRegionError

logger = logging.getLogger(__name__)
DEFAULT_URI_TEMPLATE = '{service}.{region}.{dnsSuffix}'
DEFAULT_SERVICE_DATA = {'endpoints': {}}


class EndpointResolver(object):
    """Resolve endpoints based on partition endpoint metadata."""

    def __init__(self, endpoint_data):
        # type: (Dict[str, Any]) -> None
        """Construct a new EndpointResolver based on a parsed endpoints.json.

        :param endpoint_data: A dict of partition data.
        """
        if 'partitions' not in endpoint_data:
            raise ValueError('Missing "partitions" in endpoint data')
        self._endpoint_data = endpoint_data

    def get_available_partitions(self):
        # type: () -> List[str]
        """List the partitions available to the endpoint resolver.

        :return: Returns a list of partition names (e.g., ["aws", "aws-cn"]).
        """
        result = []
        for partition in self._endpoint_data['partitions']:
            result.append(partition['partition'])
        return result

    def get_available_endpoints(self, service_name, partition_name='aws',
                                allow_non_regional=False):
        # type: (str, str, bool) -> List[str]
        """List the endpoint names of a particular partition.

        :type service_name: string
        :param service_name: Name of a service to list endpoint for (e.g., s3)

        :type partition_name: string
        :param partition_name: Name of the partition to limit endpoints to.
            (e.g., aws for the public AWS endpoints, aws-cn for AWS China
            endpoints, aws-us-gov for AWS GovCloud (US) Endpoints, etc.

        :type allow_non_regional: bool
        :param allow_non_regional: Set to True to include endpoints that are
             not regional endpoints (e.g., s3-external-1,
             fips-us-gov-west-1, etc).
        :return: Returns a list of endpoint names (e.g., ["us-east-1"]).
        """
        result = []
        for partition in self._endpoint_data['partitions']:
            if partition['partition'] != partition_name:
                continue
            services = partition['services']
            if service_name not in services:
                continue
            for endpoint_name in services[service_name]['endpoints']:
                if allow_non_regional or endpoint_name in partition['regions']:
                    result.append(endpoint_name)
        return result

    def construct_endpoint(self, service_name, region_name=None,
                           partition_name=None):
        # type: (str, str, str) -> Dict[str, Any]
        """Resolve an endpoint for a service and region combination.

        :type service_name: string
        :param service_name: Name of the service to resolve an endpoint for
            (e.g., s3)

        :type region_name: string
        :param region_name: Region/endpoint name to resolve (e.g., us-east-1)
            if no region is provided, the first found partition-wide endpoint
            will be used if available.

        :type partition_name: string
        :param partition_name: Partition name to resolve (e.g., aws, aws-cn)
            if no partition is provided, the first found partition-wide
            endpoint will be used if available.

        :rtype: dict
        :return: Returns a dict containing the following keys:
            - partition: (string, required) Resolved partition name
            - endpointName: (string, required) Resolved endpoint name
            - hostname: (string, required) Hostname to use for this endpoint
            - sslCommonName: (string) sslCommonName to use for this endpoint.
            - credentialScope: (dict) Signature version 4 credential scope
              - region: (string) region name override when signing.
              - service: (string) service name override when signing.
            - signatureVersions: (list<string>) A list of possible signature
              versions, including s3, v4, v2, and s3v4
            - protocols: (list<string>) A list of supported protocols
              (e.g., http, https)
            - ...: Other keys may be included as well based on the metadata
        """
        if partition_name is not None:
            valid_partition = None
            for partition in self._endpoint_data['partitions']:
                if partition['partition'] == partition_name:
                    valid_partition = partition

            if valid_partition is not None:
                result = self._endpoint_for_partition(valid_partition,
                                                      service_name,
                                                      region_name, True)
                return result
            return None

        # Iterate over each partition until a match is found.
        for partition in self._endpoint_data['partitions']:
            result = self._endpoint_for_partition(
                partition, service_name, region_name)
            if result:
                return result

    def _endpoint_for_partition(self, partition, service_name, region_name,
                                force_partition=False):
        # type: (str, str, str, bool) -> Dict[str, Any]
        # Get the service from the partition, or an empty template.
        service_data = partition['services'].get(
            service_name, DEFAULT_SERVICE_DATA)
        # Use the partition endpoint if no region is supplied.
        if region_name is None:
            if 'partitionEndpoint' in service_data:
                region_name = service_data['partitionEndpoint']
            else:
                raise NoRegionError()
        # Attempt to resolve the exact region for this partition.
        if region_name in service_data['endpoints']:
            return self._resolve(
                partition, service_name, service_data, region_name)
        # Check to see if the endpoint provided is valid for the partition.
        if self._region_match(partition, region_name) or force_partition:
            # Use the partition endpoint if set and not regionalized.
            partition_endpoint = service_data.get('partitionEndpoint')
            is_regionalized = service_data.get('isRegionalized', True)
            if partition_endpoint and not is_regionalized:
                logger.debug('Using partition endpoint for %s, %s: %s',
                             service_name, region_name, partition_endpoint)
                return self._resolve(
                    partition, service_name, service_data, partition_endpoint)
            logger.debug('Creating a regex based endpoint for %s, %s',
                         service_name, region_name)
            return self._resolve(
                partition, service_name, service_data, region_name)

    def _region_match(self, partition, region_name):
        # type: (str, str) -> bool
        if region_name in partition['regions']:
            return True
        if 'regionRegex' in partition:
            return re.compile(partition['regionRegex']).match(region_name)
        return False

    def _resolve(self, partition, service_name, service_data, endpoint_name):
        # type: (str, str, str, str) -> Dict[str, Any]
        result = service_data['endpoints'].get(endpoint_name, {})
        result['partition'] = partition['partition']
        result['endpointName'] = endpoint_name
        # Merge in the service defaults then the partition defaults.
        self._merge_keys(service_data.get('defaults', {}), result)
        self._merge_keys(partition.get('defaults', {}), result)
        result['hostname'] = self._expand_template(
            partition, result['hostname'], service_name, endpoint_name)
        if 'sslCommonName' in result:
            result['sslCommonName'] = self._expand_template(
                partition, result['sslCommonName'], service_name,
                endpoint_name)
        result['dnsSuffix'] = partition['dnsSuffix']
        return result

    def _merge_keys(self, from_data, result):
        # type: (Dict[str, Any], Dict[str, Any]) -> None
        for key in from_data:
            if key not in result:
                result[key] = from_data[key]

    def _expand_template(self, partition, template, service_name,
                         endpoint_name):
        # type: (Dict[str, Any], str, str, str) -> str
        return template.format(
            service=service_name, region=endpoint_name,
            dnsSuffix=partition['dnsSuffix'])
