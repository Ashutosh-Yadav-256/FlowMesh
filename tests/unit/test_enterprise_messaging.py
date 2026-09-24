"""
Unit Tests for Enterprise Messaging (Kafka, NATS, Memory EventBus & IBM MQ Connector)
"""

import pytest
from flowmesh_events.event_bus import (
    EventBus,
    EventMessage,
    InMemoryDriver,
    KafkaDriver,
    NatsDriver,
)
from flowmesh_connector.protocol import Connector, ConnectionSpec, Operation
from connectors.ibmmq.connector import IbmMqConnector


@pytest.mark.asyncio
async def test_pluggable_event_bus_drivers():
    mem_bus = EventBus(driver=InMemoryDriver())
    received = []

    async def handler(msg: EventMessage):
        received.append(msg)

    mem_bus.subscribe("orders.*", handler)

    msg = EventMessage(
        tenant_id="tenant_bank",
        subject="orders.created",
        type="order.created",
        source="checkout_service",
        payload={"amount": 100},
    )
    await mem_bus.publish("orders.created", msg)
    assert len(received) == 1
    assert received[0].payload["amount"] == 100

    kafka_bus = EventBus(driver=KafkaDriver(bootstrap_servers="localhost:9092"))
    kafka_received = []

    async def kafka_handler(msg: EventMessage):
        kafka_received.append(msg)

    kafka_bus.subscribe("payments.>", kafka_handler)
    pay_msg = EventMessage(
        tenant_id="tenant_bank",
        subject="payments.settled",
        type="payment.settled",
        source="settlement_engine",
        payload={"transaction_id": "tx_881"},
    )
    await kafka_bus.publish("payments.settled", pay_msg)
    assert len(kafka_received) == 1


@pytest.mark.asyncio
async def test_ibmmq_connector_protocol():
    connector = IbmMqConnector()
    assert isinstance(connector, Connector)
    assert connector.type == "ibmmq"

    spec = ConnectionSpec(
        id="conn_ibmmq_1",
        tenant_id="tenant_finance",
        type="ibmmq",
        name="IBM MQ Core Banking",
        config={"host": "127.0.0.1", "port": 1414, "queue_manager": "QM1", "channel": "DEV.APP.SVRCONN"},
        credentials={"username": "mq_operator"},
    )

    test_res = await connector.test(spec)
    assert test_res.success is True
    assert len(test_res.steps) == 4

    graph = await connector.discover(spec)
    assert len(graph.entities) >= 1
    assert graph.entities[0].table_name == "PAYMENT.ORDERS.IN"

    op = Operation(
        id="op_put",
        name="put_message",
        parameters={"queue": "PAYMENT.ORDERS.IN", "message": {"order_id": "ORD-5541"}},
    )
    res = await connector.execute(spec, op)
    assert res.success is True
    assert res.data["status"] == "DELIVERED"
