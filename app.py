#!/usr/bin/env python3

from aws_cdk import core as cdk

from stacks.back_end.vpc_stack import VpcStack
from stacks.back_end.rds_stack import RdsDatabaseStack
from stacks.back_end.rds_proxy_stack import RdsDatabaseProxyStack
from stacks.back_end.store_events_consumer_on_ec2_stack.store_events_consumer_on_ec2_stack import StoreEventsConsumerOnEC2Stack

app = cdk.App()


# VPC Stack for hosting Secure workloads & Other resources
vpc_stack = VpcStack(
    app,
    f"{app.node.try_get_context('project')}-vpc-stack",
    stack_log_level="INFO",
    description="Miztiik Automation: Custom Multi-AZ VPC"
)

# Deploy RDS Consumer On EC2 instance
store_events_consumer_stack = StoreEventsConsumerOnEC2Stack(
    app,
    f"store-events-consumer-stack",
    stack_log_level="INFO",
    vpc=vpc_stack.vpc,
    ec2_instance_type="t2.micro",
    description="Miztiik Automation: Deploy RDS Consumer On EC2 instance"
)

# Sales Events Database on RDS with PostgreSQL
store_events_db_stack = RdsDatabaseStack(
    app,
    f"store-events-db-stack",
    stack_log_level="INFO",
    vpc=vpc_stack.vpc,
    rds_instance_size="r5.large",  # db. prefix is added by cdk automatically
    enable_multi_az=True,
    enable_perf_insights=True,
    description="Miztiik Automation: Sales Events Database on RDS with PostgreSQL",
)

# Sales Events Database Proxy
store_events_db_proxy_stack = RdsDatabaseProxyStack(
    app,
    f"store-events-db-proxy-stack",
    stack_log_level="INFO",
    vpc=vpc_stack.vpc,
    db_target=store_events_db_stack.store_events_db,
    db_secret=store_events_db_stack.db_secret,
    db_sg=store_events_db_stack.pgsql_db_sg,
    description="Miztiik Automation: Sales Events Database Proxy",
)


# Stack Level Tagging
_tags_lst = app.node.try_get_context("tags")

if _tags_lst:
    for _t in _tags_lst:
        for k, v in _t.items():
            cdk.Tags.of(app).add(
                k, v, apply_to_launched_instances=True, priority=300)

app.synth()
