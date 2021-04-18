from aws_cdk import core as cdk
from aws_cdk import aws_rds as _rds
from aws_cdk import aws_ec2 as _ec2
from aws_cdk import aws_secretsmanager as _sm


from stacks.miztiik_global_args import GlobalArgs


class RdsDatabaseStack(cdk.Stack):

    def __init__(
        self,
        scope: cdk.Construct,
        construct_id: str,
        stack_log_level: str,
        vpc,
        rds_instance_size: str,
        enable_multi_az: bool,
        enable_perf_insights: bool,
        **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.db_name = "store_events"
        self.db_secret = _sm.Secret(
            self,
            "storeEventsDbSecret",
            secret_name=f"store-events-db-credentials-{construct_id}",
            description="Credentials for Store Events DB in RDS MySQL.",
            generate_secret_string=_sm.SecretStringGenerator(
                secret_string_template='{"username": "mystiquemaster"}',
                generate_string_key="password",
                password_length=16,
                exclude_characters='"@\\\/',
                exclude_punctuation=True,
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY
        )
        store_events_db_credentials = _rds.Credentials.from_secret(
            self.db_secret)

        # Create Security Group for MySQL Server Instance
        self.my_sql_db_sg = _ec2.SecurityGroup(
            self,
            id="mySqlDbSecurityGroup",
            vpc=vpc,
            security_group_name=f"mysql_db_sg_{construct_id}",
            description="Security Group for MySQL"
        )
        cdk.Tags.of(self.my_sql_db_sg).add("name", "mysql_db_sg")

        self.my_sql_db_sg.add_ingress_rule(
            peer=_ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=_ec2.Port.tcp(3306),
            description="Allow Incoming DB Traffic from within VPC"
        )

        self.my_sql_db_sg.add_ingress_rule(
            peer=self.my_sql_db_sg,
            connection=_ec2.Port.all_tcp(),
            description="Allow ALL PORTS for TCP within SG for GLUE Connections"
        )

        # Create Security Group for PostgreSQL Server Instance
        self.pgsql_db_sg = _ec2.SecurityGroup(
            self,
            id="postgreSqlDbSecurityGroup",
            vpc=vpc,
            security_group_name=f"pgsql_db_sg_{construct_id}",
            description="Security Group for PostgreSQL"
        )
        cdk.Tags.of(self.pgsql_db_sg).add("name", "pgsql_db_sg")

        self.pgsql_db_sg.add_ingress_rule(
            peer=_ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=_ec2.Port.tcp(5432),
            description="Allow Incoming DB Traffic from within VPC"
        )

        # Param Group for Postgresql
        self.store_events_db_params_group = _rds.ParameterGroup(
            self,
            "ordersDbParamsGroup",
            description='Parameter group to allow CDC from RDS using DMS.',
            engine=_rds.DatabaseInstanceEngine.postgres(
                version=_rds.PostgresEngineVersion.VER_11_6),
            parameters={
                "rds.logical_replication": "1",
                "wal_sender_timeout": "0"
            }
        )

        # Create an RDS Database):
        self.store_events_db = _rds.DatabaseInstance(
            self,
            "storeEventsDb",
            credentials=store_events_db_credentials,
            database_name=f"{self.db_name}",
            # engine=_rds.DatabaseInstanceEngine.MYSQL,
            engine=_rds.DatabaseInstanceEngine.postgres(
                version=_rds.PostgresEngineVersion.VER_11_6),
            # engine=_rds.DatabaseInstanceEngine.mysql(
            #     version=_rds.MysqlEngineVersion.VER_5_7_31
            # ),
            vpc=vpc,
            port=5432,
            security_groups=[self.pgsql_db_sg],
            allocated_storage=50,
            multi_az=False,
            # cloudwatch_logs_exports=["error", "general", "slowquery"], # Only for MySQLs
            instance_type=_ec2.InstanceType.of(
                _ec2.InstanceClass.BURSTABLE2,
                _ec2.InstanceSize.MICRO
            ),
            # instance_type=_ec2.InstanceType(
            #     instance_type_identifier=rds_instance_size
            # ),
            parameter_group=self.store_events_db_params_group,
            removal_policy=cdk.RemovalPolicy.DESTROY,
            deletion_protection=False,
            delete_automated_backups=True,
            backup_retention=cdk.Duration.days(
                7)
            # , enable_performance_insights=True
        )

        # Let us configure performance insights
        if enable_perf_insights:
            add_pi = self.store_events_db.node.default_child
            add_pi.add_override(
                "Properties.EnablePerformanceInsights", True)
        # Let us configure performance insights
        if enable_multi_az:
            add_ha = self.store_events_db.node.default_child
            add_ha.add_override(
                "Properties.MultiAZ", True)

        # store_events_db.connections.allow_from(
        #     other=_ec2.Peer.ipv4(vpc.vpc_cidr_block),
        #     port_range=_ec2.Port.tcp(3306),
        #     description="Allow Incoming DB Traffic from within VPC"
        # )

        self.store_events_db_endpoint = self.store_events_db.db_instance_endpoint_address

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
            "StoreEventsDatabase",
            value=f"https://console.aws.amazon.com/rds/home?region={cdk.Aws.REGION}#dbinstance:id={self.store_events_db.instance_identifier}",
            description="Store Events Database in RDS"
        )
        output_2 = cdk.CfnOutput(
            self,
            "DatabaseConnectionCommand",
            value=f"psql -h {self.store_events_db_endpoint} -P 5432 -u mystiquemaster -p",
            description="Connect to the database using this command"
        )
        output_3 = cdk.CfnOutput(
            self,
            "StoreEventsDatabaseSecretArn",
            value=f"{self.db_secret.secret_full_arn}",
            description="The credentials to connect to Store events database"
        )
