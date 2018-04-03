from datetime import datetime
from typing import Dict, Any

from collections import defaultdict

from blurr.core.base import BaseSchema, BaseItem
from blurr.core.evaluation import Expression, EvaluationContext
from blurr.core.schema_loader import SchemaLoader
from blurr.core.block_data_group import BlockDataGroup


class AnchorSchema(BaseSchema):
    """
    Represents the schema for the Anchor specified in a window DTC.
    """
    ATTRIBUTE_CONDITION = 'Condition'
    ATTRIBUTE_MAX = 'Max'

    def __init__(self, fully_qualified_name: str,
                 schema_loader: SchemaLoader) -> None:
        super().__init__(fully_qualified_name, schema_loader)

        self.condition = Expression(self._spec[self.ATTRIBUTE_CONDITION])
        self.max = self._spec[
            self.ATTRIBUTE_MAX] if self.ATTRIBUTE_MAX in self._spec else None


class Anchor(BaseItem):
    def __init__(self, schema: AnchorSchema,
                 evaluation_context: EvaluationContext):
        super().__init__(schema, evaluation_context)
        self.condition_met: Dict[datetime, int] = defaultdict(int)
        self.anchor_block = None

    def evaluate_anchor(self, block: BlockDataGroup) -> bool:
        self.anchor_block = block
        if self.max_condition_met(block):
            return False

        if self.evaluate():
            return True

        return False

    def add_condition_met(self):
        self.condition_met[self.anchor_block.start_time.date()] += 1

    def evaluate(self) -> bool:
        return self.schema.condition.evaluate(self.evaluation_context)

    def max_condition_met(self, block: BlockDataGroup) -> bool:
        if self.schema.max is None:
            return False
        return self.condition_met[block.start_time.date()] >= self.schema.max

    def restore(self, snapshot: Dict[str, Any]) -> BaseItem:
        pass

    @property
    def snapshot(self):
        pass