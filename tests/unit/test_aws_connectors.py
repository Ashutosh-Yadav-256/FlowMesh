"""
Unit tests for FlowMesh AWS Enterprise Connector Suite
Tests all 11 AWS connectors:
- aws (Master Suite)
- aws_s3 (Amazon S3)
- aws_sqs (Amazon SQS)
- aws_sns (Amazon SNS)
- aws_lambda (AWS Lambda)
- aws_dynamodb (Amazon DynamoDB)
- aws_eventbridge (Amazon EventBridge)
- aws_secrets_manager (AWS Secrets Manager)
- aws_cloudwatch (Amazon CloudWatch)
- aws_step_functions (AWS Step Functions)
- aws_kms (AWS Key Management Service)
"""

import pytest
from flowmesh_connector.protocol import ConnectionSpec, Operation
from flowmesh_connector.registry import registry, get_connector
from connectors.aws import (
    AwsConnector,
    AwsS3Connector,
    AwsSqsConnector,
    AwsSnsConnector,
    AwsLambdaConnector,
    AwsDynamoDbConnector,
    AwsEventBridgeConnector,
    AwsSecretsManagerConnector,
    AwsCloudWatchConnector,
    AwsStepFunctionsConnector,
    AwsKmsConnector,
)

ALL_AWS_TYPES = [
    "aws",
    "aws_s3",
    "aws_sqs",
    "aws_sns",
    "aws_lambda",
    "aws_dynamodb",
    "aws_eventbridge",
    "aws_secrets_manager",
    "aws_cloudwatch",
    "aws_step_functions",
    "aws_kms",
]


def make_spec(conn_type: str, custom_config: dict = None) -> ConnectionSpec:
    config = {
        "region": "us-east-1",
        "role_arn": "arn:aws:iam::123456789012:role/FlowMeshIntegrationRole",
    }
    if custom_config:
        config.update(custom_config)

    return ConnectionSpec(
        id=f"conn_test_{conn_type}",
        tenant_id="tenant_acme",
        type=conn_type,
        name=f"Test {conn_type.upper()}",
        config=config,
        credentials={
            "aws_access_key_id": "AKIAIOSFODNN7EXAMPLE",
            "aws_secret_access_key": "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY",
            "aws_session_token": "AQoDYXdzEJr1EXAMPLE==",
        },
        agent_id=None,
    )


def test_registry_has_all_aws_connectors():
    """Verify that all 11 AWS connectors are registered and accessible by type."""
    registered = registry.list_types()
    for aws_type in ALL_AWS_TYPES:
        assert aws_type in registered, f"Missing {aws_type} in registry"
        conn = get_connector(aws_type)
        assert conn is not None
        assert conn.type == aws_type


@pytest.mark.asyncio
@pytest.mark.parametrize("conn_type", ALL_AWS_TYPES)
async def test_aws_4_point_verification(conn_type: str):
    """Verify that every AWS connector performs a complete 4-point verification check."""
    conn = get_connector(conn_type)
    assert conn is not None
    spec = make_spec(conn_type)

    test_res = await conn.test(spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4
    for step in test_res.steps:
        assert step.status == "passed"
        assert step.duration_ms >= 0
        assert len(step.message) > 0


@pytest.mark.asyncio
@pytest.mark.parametrize("conn_type", ALL_AWS_TYPES)
async def test_aws_schema_discovery(conn_type: str):
    """Verify that every AWS connector discovers entities with typed columns and keys."""
    conn = get_connector(conn_type)
    assert conn is not None
    spec = make_spec(conn_type)

    graph = await conn.discover(spec)
    assert len(graph.entities) > 0
    for entity in graph.entities:
        assert len(entity.table_name) > 0
        assert len(entity.columns) > 0
        pk_cols = [c for c in entity.columns if c.is_primary_key]
        assert len(pk_cols) >= 1


@pytest.mark.asyncio
@pytest.mark.parametrize("conn_type", ALL_AWS_TYPES)
async def test_aws_operations_spec_and_execution(conn_type: str):
    """Verify that every AWS connector declares operations and executes cleanly."""
    conn = get_connector(conn_type)
    assert conn is not None
    spec = make_spec(conn_type)

    ops = conn.operations()
    assert len(ops) > 0
    first_op = ops[0]

    op = Operation(
        id="op_test_1",
        name=first_op.name,
        parameters={"test_key": "test_value"},
        timeout_seconds=30,
    )
    result = await conn.execute(spec, op)
    assert result.success is True
    assert result.data is not None
    assert result.duration_ms >= 0


@pytest.mark.asyncio
async def test_aws_s3_functional():
    """Specific tests for S3 operations."""
    connector = AwsS3Connector()
    spec = make_spec("aws_s3", {"bucket": "my-lake-bucket"})

    op_put = Operation(
        id="op_s3_1",
        name="s3.put_object",
        parameters={"bucket": "my-lake-bucket", "key": "data/sample.json", "body": '{"test": 123}'},
    )
    res_put = await connector.execute(spec, op_put)
    assert res_put.success is True
    assert "etag" in res_put.data

    op_get = Operation(
        id="op_s3_2",
        name="s3.get_object",
        parameters={"bucket": "my-lake-bucket", "key": "data/sample.json"},
    )
    res_get = await connector.execute(spec, op_get)
    assert res_get.success is True
    assert "content" in res_get.data


@pytest.mark.asyncio
async def test_aws_sqs_functional():
    """Specific tests for SQS operations."""
    connector = AwsSqsConnector()
    spec = make_spec("aws_sqs", {"queue_url": "https://sqs.us-east-1.amazonaws.com/123/orders"})

    op_send = Operation(
        id="op_sqs_1",
        name="sqs.send_message",
        parameters={"queue_url": "https://sqs.us-east-1.amazonaws.com/123/orders", "message_body": "{\"order_id\": 99}"},
    )
    res_send = await connector.execute(spec, op_send)
    assert res_send.success is True
    assert "message_id" in res_send.data

    op_recv = Operation(
        id="op_sqs_2",
        name="sqs.receive_messages",
        parameters={"queue_url": "https://sqs.us-east-1.amazonaws.com/123/orders", "max_messages": 5},
    )
    res_recv = await connector.execute(spec, op_recv)
    assert res_recv.success is True
    assert "messages" in res_recv.data
    assert len(res_recv.data["messages"]) > 0


@pytest.mark.asyncio
async def test_aws_lambda_functional():
    """Specific tests for Lambda operations."""
    connector = AwsLambdaConnector()
    spec = make_spec("aws_lambda", {"function_name": "order-processor"})

    op_inv = Operation(
        id="op_lambda_1",
        name="lambda.invoke",
        parameters={"function_name": "order-processor", "payload": {"foo": "bar"}},
    )
    res_inv = await connector.execute(spec, op_inv)
    assert res_inv.success is True
    assert res_inv.data["status_code"] == 200
    assert "payload" in res_inv.data


@pytest.mark.asyncio
async def test_aws_dynamodb_functional():
    """Specific tests for DynamoDB operations."""
    connector = AwsDynamoDbConnector()
    spec = make_spec("aws_dynamodb", {"table_name": "Users"})

    op_put = Operation(
        id="op_dynamo_1",
        name="dynamodb.put_item",
        parameters={"table_name": "Users", "item": {"user_id": "u123", "name": "Alice"}},
    )
    res_put = await connector.execute(spec, op_put)
    assert res_put.success is True

    op_get = Operation(
        id="op_dynamo_2",
        name="dynamodb.get_item",
        parameters={"table_name": "Users", "key": {"user_id": "u123"}},
    )
    res_get = await connector.execute(spec, op_get)
    assert res_get.success is True
    assert "item" in res_get.data


@pytest.mark.asyncio
async def test_aws_kms_functional():
    """Specific tests for KMS operations."""
    connector = AwsKmsConnector()
    spec = make_spec("aws_kms", {"key_id": "arn:aws:kms:us-east-1:123:key/abc"})

    op_enc = Operation(
        id="op_kms_1",
        name="kms.encrypt",
        parameters={"key_id": "arn:aws:kms:us-east-1:123:key/abc", "plaintext": "my-secret-data"},
    )
    res_enc = await connector.execute(spec, op_enc)
    assert res_enc.success is True
    assert "ciphertext_blob" in res_enc.data
