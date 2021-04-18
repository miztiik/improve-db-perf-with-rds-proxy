from aws_cdk import core as cdk
from aws_cdk import aws_rds as _rds
from aws_cdk import aws_iam as _iam
from aws_cdk import aws_secretsmanager as _sm


from stacks.miztiik_global_args import GlobalArgs


class RdsDatabaseProxyStack(cdk.Stack):

    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        stack_log_level: str,
        vpc,
        db_target,
        db_secret,
        db_sg,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create Proxy Configuration
        rds_db_proxy = _rds.DatabaseProxy(
            self,
            "storeEventsDbProxy",
            db_proxy_name="store-events-db-proxy",
            # proxy_target=_rds.ProxyTarget.from_cluster(cluster),
            proxy_target=_rds.ProxyTarget.from_instance(db_target),
            # secrets=[db_target.secret],
            secrets=[db_secret],
            idle_client_timeout=cdk.Duration.minutes(10),
            max_connections_percent=90,
            max_idle_connections_percent=10,
            vpc=vpc,
            require_tls=False,
            security_groups=[db_sg]
        )

        rds_db_proxy_role = _iam.Role(
            self,
            "storeEventsDbProxyRole",
            assumed_by=_iam.AccountPrincipal(self.account)
        )
        rds_db_proxy.grant_connect(rds_db_proxy_role, "admin")

        ###########################################
        ################# OUTPUTS #################
        ###########################################

        output_0 = cdk.CfnOutput(
            self,
            "AutomationFrom",
            value=f"{GlobalArgs.SOURCE_INFO}",
            description="To know more about this automation stack, check out our github page."
        )

        output_1 = cdk.CfnOutput(
            self,
            "StoreEventsDbProxy",
            value=f"https://console.aws.amazon.com/rds/home?region={cdk.Aws.REGION}#proxy:id={rds_db_proxy.db_proxy_name}",
            description="Sales Events Database Proxy"
        )
