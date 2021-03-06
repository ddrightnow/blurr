from contextlib import contextmanager
from typing import Dict, Any, Type
from unittest import mock

from pytest import fixture, raises

from blurr.core.aggregate import AggregateSchema
from blurr.core.base import BaseItemCollection, BaseItem, BaseSchemaCollection
from blurr.core.errors import SnapshotError
from blurr.core.evaluation import EvaluationContext
from blurr.core.loader import TypeLoader
from blurr.core.schema_loader import SchemaLoader
from blurr.core.type import Type as BtsType


@fixture
def collection_schema_spec() -> Dict[str, Any]:
    return {
        'Type': 'Blurr:Aggregate:MockAggregate',
        'Name': 'user',
        'When': 'True',
        'Fields': [{
            'Name': 'event_count',
            'Type': BtsType.INTEGER,
            'Value': 5
        }]
    }


@fixture
def mock_nested_items() -> contextmanager:
    return mock.patch(
        'base_item_collection_test.MockBaseItemCollection._nested_items',
        new_callable=mock.PropertyMock,
        return_value=None)


class MockBaseItemCollection(BaseItemCollection):
    """
    This class is to test abstract behavior, and thus, adds no functionality
    """

    def __init__(self, schema: BaseSchemaCollection, evaluation_context: EvaluationContext) -> None:
        super().__init__(schema, evaluation_context)
        self._fields: Dict[str, Type[BaseItem]] = {
            name: TypeLoader.load_item(item_schema.type)(item_schema, self._evaluation_context)
            for name, item_schema in self._schema.nested_schema.items()
        }

    def run_finalize(self) -> None:
        pass

    @property
    def _nested_items(self) -> Dict[str, Type[BaseItem]]:
        return self._fields

    def __getattr__(self, item: str) -> Any:
        """
        Makes the value of the nested items available as properties
        of the collection object.  This is used for retrieving field values
        for dynamic execution.
        :param item: Field requested
        """
        if item in self._nested_items:
            return self._nested_items[item]._snapshot

        return self.__getattribute__(item)


class MockBaseSchemaCollection(BaseSchemaCollection):
    """
    This class is to test abstract behavior, and thus, adds no functionality
    """

    pass


@fixture
def schema_collection(collection_schema_spec: Dict[str, Any]) -> MockBaseSchemaCollection:
    schema_loader = SchemaLoader()
    name = schema_loader.add_schema_spec(collection_schema_spec)
    return MockBaseSchemaCollection(name, schema_loader, AggregateSchema.ATTRIBUTE_FIELDS)


@fixture
def item_collection(schema_collection: MockBaseSchemaCollection) -> MockBaseItemCollection:
    return MockBaseItemCollection(schema_collection, EvaluationContext())


def test_evaluate_needs_evaluation_false(collection_schema_spec: Dict[str, Any]) -> None:
    schema_loader = SchemaLoader()
    collection_schema_spec['When'] = 'False'
    name = schema_loader.add_schema_spec(collection_schema_spec)
    schema_collection = MockBaseSchemaCollection(name, schema_loader,
                                                 AggregateSchema.ATTRIBUTE_FIELDS)
    item_collection = MockBaseItemCollection(schema_collection, EvaluationContext())
    item_collection.run_evaluate()
    assert item_collection.event_count == 0


def test_evaluate_needs_evaluation_true(item_collection: MockBaseItemCollection) -> None:
    item_collection.run_evaluate()
    assert item_collection.event_count == 5


def test_reset(item_collection: MockBaseItemCollection) -> None:
    item_collection.run_evaluate()
    assert item_collection.event_count == 5
    item_collection.run_reset()
    assert item_collection.event_count == 0


def test_evaluate_needs_evaluation_error_does_not_evaluate(
        collection_schema_spec: Dict[str, Any]) -> None:
    schema_loader = SchemaLoader()
    collection_schema_spec['When'] = '1/0'
    name = schema_loader.add_schema_spec(collection_schema_spec)
    schema_collection = MockBaseSchemaCollection(name, schema_loader,
                                                 AggregateSchema.ATTRIBUTE_FIELDS)
    item_collection = MockBaseItemCollection(schema_collection, EvaluationContext())
    item_collection.run_evaluate()
    assert item_collection.event_count == 0


def test_evaluate_invalid(item_collection: MockBaseItemCollection,
                          mock_nested_items: contextmanager) -> None:
    # Test nested items not specified
    with mock_nested_items:
        with raises(Exception):
            item_collection.run_evaluate()


def test_snapshot_valid(item_collection: MockBaseItemCollection) -> None:
    assert item_collection._snapshot == {'event_count': 0}

    item_collection.run_evaluate()
    assert item_collection._snapshot == {'event_count': 5}


def test_snapshot_invalid(collection_schema_spec: Dict[str, Any],
                          mock_nested_items: contextmanager) -> None:
    schema_loader = SchemaLoader()
    name = schema_loader.add_schema_spec(collection_schema_spec)
    schema_collection = MockBaseSchemaCollection(name, schema_loader,
                                                 AggregateSchema.ATTRIBUTE_FIELDS)

    # Test nested items not specified
    with mock_nested_items:
        with raises(SnapshotError):
            item_collection = MockBaseItemCollection(schema_collection, EvaluationContext())
            assert item_collection._snapshot


def test_restore_valid(item_collection: MockBaseItemCollection) -> None:
    item_collection.run_restore({'event_count': 5})
    assert item_collection._snapshot == {'event_count': 5}


def test_restore_invalid_snapshot_field(item_collection: MockBaseItemCollection) -> None:
    with raises(SnapshotError):
        invalid_snapshot = {'event': 5}
        item_collection.run_restore(invalid_snapshot)


def test_restore_invalid_snapshot_dict(collection_schema_spec: Dict[str, Any],
                                       mock_nested_items: contextmanager) -> None:
    schema_loader = SchemaLoader()
    name = schema_loader.add_schema_spec(collection_schema_spec)
    schema_collection = MockBaseSchemaCollection(name, schema_loader,
                                                 AggregateSchema.ATTRIBUTE_FIELDS)

    # Test nested items not specified
    with mock_nested_items:
        with raises(SnapshotError):
            item_collection = MockBaseItemCollection(schema_collection, EvaluationContext())
            snapshot = {'event_count: 5'}
            item_collection.run_restore(snapshot)


def test_get_attribute(collection_schema_spec: Dict[str, Any]) -> None:
    schema_loader = SchemaLoader()
    name = schema_loader.add_schema_spec(collection_schema_spec)
    schema_collection = MockBaseSchemaCollection(name, schema_loader,
                                                 AggregateSchema.ATTRIBUTE_FIELDS)
    item_collection = MockBaseItemCollection(schema_collection, EvaluationContext())
    # Check nested items access
    assert item_collection.event_count == 0
    # make sure normal properties are not broken
    assert item_collection._schema == schema_collection


def test_get_attribute_invalid(collection_schema_spec: Dict[str, Any],
                               mock_nested_items: contextmanager) -> None:
    schema_loader = SchemaLoader()
    name = schema_loader.add_schema_spec(collection_schema_spec)
    schema_collection = MockBaseSchemaCollection(name, schema_loader,
                                                 AggregateSchema.ATTRIBUTE_FIELDS)

    with raises(Exception):
        item_collection = MockBaseItemCollection(schema_collection, EvaluationContext())
        assert item_collection.event_counts

    # Test nested items not specified
    with mock_nested_items:
        with raises(Exception):
            item_collection = MockBaseItemCollection(schema_collection, EvaluationContext())
            mock_nested_items.return_value = None
            assert item_collection.event_count
