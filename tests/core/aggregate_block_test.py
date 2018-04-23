from datetime import datetime, timezone
from typing import Dict, Any

from pytest import fixture

from blurr.core.evaluation import EvaluationContext
from blurr.core.field import Field
from blurr.core.schema_loader import SchemaLoader
from blurr.core.aggregate_streaming import StreamingAggregateSchema, \
    StreamingAggregate
from blurr.core.store_key import Key


@fixture
def block_aggregate_schema_spec() -> Dict[str, Any]:
    return {
        'Type': 'Blurr:Aggregate:BlockAggregate',
        'Name': 'user',
        'Store': 'memstore',
        'Fields': [{
            'Name': 'event_count',
            'Type': 'integer',
            'Value': 'user.event_count + 1'
        }]
    }


@fixture
def store_spec() -> Dict[str, Any]:
    return {'Name': 'memstore', 'Type': 'Blurr:Store:MemoryStore'}


@fixture
def schema_loader(store_spec) -> SchemaLoader:
    schema_loader = SchemaLoader()
    schema_loader.add_schema(store_spec, 'user')
    return schema_loader


def check_fields(fields: Dict[str, Field], expected_field_values: Dict[str, Any]) -> None:
    assert len(fields) == len(expected_field_values)

    for field_name, field in fields.items():
        assert isinstance(field, Field)
        assert field.value == expected_field_values[field_name]


def create_block_aggregate(schema, time, identity) -> StreamingAggregate:
    evaluation_context = EvaluationContext()
    block_aggregate = StreamingAggregate(
        schema=schema, identity=identity, evaluation_context=evaluation_context)
    evaluation_context.global_add('time', time)
    evaluation_context.global_add('user', block_aggregate)
    evaluation_context.global_add('identity', identity)
    return block_aggregate


def test_block_aggregate_schema_evaluate_without_split(block_aggregate_schema_spec, schema_loader):
    name = schema_loader.add_schema(block_aggregate_schema_spec)
    block_aggregate_schema = StreamingAggregateSchema(name, schema_loader)

    identity = 'userA'
    time = datetime(2018, 3, 7, 19, 35, 31, 0, timezone.utc)
    block_aggregate = create_block_aggregate(block_aggregate_schema, time, identity)
    block_aggregate.evaluate()

    # Check eval results of various fields
    assert len(block_aggregate._nested_items) == 4
    check_fields(block_aggregate._nested_items, {
        '_identity': identity,
        'event_count': 1,
        '_start_time': time,
        '_end_time': time
    })

    # aggregate snapshot should not exist in store
    assert block_aggregate_schema.store.get(
        Key(identity=block_aggregate._identity,
            group=block_aggregate._name,
            timestamp=block_aggregate._start_time)) is None
