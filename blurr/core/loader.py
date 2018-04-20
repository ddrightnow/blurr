from typing import Any

import importlib

import blurr.core.constants as constants
from blurr.core.errors import InvalidSchemaError

ITEM_MAP = {
    constants.BLURR_TRANSFORM_STREAMING: 'blurr.core.transformer_streaming.StreamingTransformer',
    constants.BLURR_TRANSFORM_WINDOW: 'blurr.core.transformer_window.WindowTransformer',
    constants.BLURR_AGGREGATE_BLOCK: 'blurr.core.aggregate_block.BlockAggregate',
    constants.BLURR_AGGREGATE_LABEL: 'blurr.core.aggregate_label.LabelAggregate',
    constants.BLURR_AGGREGATE_ACTIVITY: 'blurr.core.aggregate_activity.ActivityAggregate',
    constants.BLURR_AGGREGATE_IDENTITY: 'blurr.core.aggregate_identity.IdentityAggregate',
    constants.BLURR_AGGREGATE_VARIABLE: 'blurr.core.aggregate_variable.VariableAggregate',
    constants.BLURR_AGGREGATE_WINDOW: 'blurr.core.aggregate_window.WindowAggregate',
    'day': 'blurr.core.window.Window',
    'hour': 'blurr.core.window.Window',
    'count': 'blurr.core.window.Window',
    'string': 'blurr.core.field.Field',
    'integer': 'blurr.core.field.Field',
    'boolean': 'blurr.core.field.Field',
    'datetime': 'blurr.core.field.Field',
    'float': 'blurr.core.field.Field',
    'map': 'blurr.core.field.Field',
    'list': 'blurr.core.field.Field',
    'set': 'blurr.core.field.Field',
}
ITEM_MAP_LOWER_CASE = {k.lower(): v for k, v in ITEM_MAP.items()}

SCHEMA_MAP = {
    constants.BLURR_TRANSFORM_STREAMING: 'blurr.core.transformer_streaming.StreamingTransformerSchema',
    constants.BLURR_TRANSFORM_WINDOW: 'blurr.core.transformer_window.WindowTransformerSchema',
    constants.BLURR_AGGREGATE_BLOCK: 'blurr.core.aggregate_block.BlockAggregateSchema',
    constants.BLURR_AGGREGATE_LABEL: 'blurr.core.aggregate_label.LabelAggregateSchema',
    constants.BLURR_AGGREGATE_ACTIVITY: 'blurr.core.aggregate_activity.ActivityAggregateSchema',
    constants.BLURR_AGGREGATE_IDENTITY: 'blurr.core.aggregate_identity.IdentityAggregateSchema',
    constants.BLURR_AGGREGATE_VARIABLE: 'blurr.core.aggregate_variable.VariableAggregateSchema',
    constants.BLURR_AGGREGATE_WINDOW: 'blurr.core.aggregate_window.WindowAggregateSchema',
    constants.BLURR_STORE_MEMORY: 'blurr.store.memory_store.MemoryStore',
    'anchor': 'blurr.core.anchor.AnchorSchema',
    'day': 'blurr.core.window.WindowSchema',
    'hour': 'blurr.core.window.WindowSchema',
    'count': 'blurr.core.window.WindowSchema',
    'string': 'blurr.core.field_simple.StringFieldSchema',
    'integer': 'blurr.core.field_simple.IntegerFieldSchema',
    'boolean': 'blurr.core.field_simple.BooleanFieldSchema',
    'datetime': 'blurr.core.field_simple.DateTimeFieldSchema',
    'float': 'blurr.core.field_simple.FloatFieldSchema',
    'map': 'blurr.core.field_complex.MapFieldSchema',
    'list': 'blurr.core.field_complex.ListFieldSchema',
    'set': 'blurr.core.field_complex.SetFieldSchema'
}
SCHEMA_MAP_LOWER_CASE = {k.lower(): v for k, v in SCHEMA_MAP.items()}

# TODO Build dynamic type loader from a central configuration rather than reading a static dictionary


class TypeLoader:
    @staticmethod
    def load_schema(type_name: str):
        return TypeLoader.load_type(type_name, SCHEMA_MAP_LOWER_CASE)

    @staticmethod
    def load_item(type_name: str):
        return TypeLoader.load_type(type_name, ITEM_MAP_LOWER_CASE)

    @staticmethod
    def load_type(type_name: str, type_map: dict) -> Any:
        lower_type_name = type_name.lower()
        if lower_type_name not in type_map:
            raise InvalidSchemaError('Unknown schema type {}'.format(type_name))
        return TypeLoader.import_class_by_full_name(type_map[lower_type_name])

    @staticmethod
    def import_class_by_full_name(name):
        components = name.rsplit('.', 1)
        mod = importlib.import_module(components[0])
        if len(components) == 1:
            return mod
        loaded_class = getattr(mod, components[1])
        return loaded_class
