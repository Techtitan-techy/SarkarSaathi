"""
Metrics Publisher
Helper module for publishing custom business metrics to CloudWatch
"""

import boto3
from datetime import datetime
from typing import Dict, Any, List, Optional

cloudwatch = boto3.client('cloudwatch')

NAMESPACE = 'SarkariSaathi'


def publish_metric(metric_name: str, value: float, unit: str = 'Count',
                  dimensions: Optional[List[Dict[str, str]]] = None):
    """Publish a single metric to CloudWatch"""
    try:
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit,
            'Timestamp': datetime.utcnow()
        }
        
        if dimensions:
            metric_data['Dimensions'] = dimensions
        
        cloudwatch.put_metric_data(
            Namespace=NAMESPACE,
            MetricData=[metric_data]
        )
    except Exception as e:
        print(f"Error publishing metric {metric_name}: {str(e)}")


def publish_user_engagement(active_users: int, new_users: int):
    """Publish user engagement metrics"""
    publish_metric('ActiveUsers', active_users)
    publish_metric('NewUsers', new_users)


def publish_scheme_discovery(searches: int, matches: int):
    """Publish scheme discovery metrics"""
    publish_metric('SchemeSearches', searches)
    publish_metric('SchemeMatches', matches)


def publish_application_metrics(submitted: int, approved: int):
    """Publish application metrics"""
    publish_metric('ApplicationsSubmitted', submitted)
    publish_metric('ApplicationsApproved', approved)


def publish_channel_usage(channel: str, interactions: int):
    """Publish channel usage metrics"""
    publish_metric(
        f'{channel}Interactions',
        interactions,
        dimensions=[{'Name': 'Channel', 'Value': channel}]
    )


def publish_voice_accuracy(accuracy: float):
    """Publish voice processing accuracy"""
    publish_metric('VoiceAccuracy', accuracy, unit='Percent')


def publish_response_time(operation: str, duration_ms: float):
    """Publish operation response time"""
    publish_metric(
        'ResponseTime',
        duration_ms,
        unit='Milliseconds',
        dimensions=[{'Name': 'Operation', 'Value': operation}]
    )


def publish_error_rate(error_type: str, count: int):
    """Publish error metrics"""
    publish_metric(
        'Errors',
        count,
        dimensions=[{'Name': 'ErrorType', 'Value': error_type}]
    )


def publish_cost_metric(service: str, estimated_cost: float):
    """Publish cost tracking metrics"""
    publish_metric(
        'EstimatedCost',
        estimated_cost,
        unit='None',
        dimensions=[{'Name': 'Service', 'Value': service}]
    )
