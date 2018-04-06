from typing import Any, Dict, List, Tuple

from datetime import datetime, timezone

from blurr.core.schema_loader import SchemaLoader
from blurr.core.store import Store, Key


class MemoryStore(Store):
    """
    In-memory store implementation
    """

    def __init__(self, fully_qualified_name: str, schema_loader: SchemaLoader) -> None:
        super().__init__(fully_qualified_name, schema_loader)
        self._cache: Dict[Key, Any] = dict()

    def load(self):
        pass

    def get(self, key: Key) -> Any:
        return self._cache.get(key, None)

    def get_all(self) -> Dict[Key, Any]:
        return self._cache

    def get_range(self, start: Key, end: Key = None, count: int = 0) -> List[Tuple[Key, Any]]:
        if end and count:
            raise ValueError('Only one of `end` or `count` can be set')

        if end is not None and end < start:
            start, end = end, start

        if not count:
            # TODO: Come up with a better way of getting this range for instances where key
            # does not have a timestamp.
            items_in_range = []
            for key, item in self._cache.items():
                if start < key < end:
                    items_in_range.append((key, item))
                elif key.timestamp is None:
                    item_ts = item.get('_start_time', datetime.min)
                    item_ts = item_ts if  item_ts.tzinfo else item_ts.replace(
                        tzinfo=timezone.utc)
                    if start.timestamp < item_ts < end.timestamp:
                        items_in_range.append((key, item))
                        continue
            return items_in_range
        else:
            filter_condition = (lambda i: i[0] > start) if count > 0 else (lambda i: i[0] < start)

            items = sorted(filter(filter_condition, list(self._cache.items())))

            if abs(count) > len(items):
                count = MemoryStore._sign(count) * len(items)

            if count < 0:
                return items[count:]
            else:
                return items[:count]

    @staticmethod
    def _sign(x: int) -> int:
        return (1, -1)[x < 0]

    def save(self, key: Key, item: Any) -> None:
        self._cache[key] = item

    def delete(self, key: Key) -> None:
        self._cache.pop(key, None)

    def finalize(self) -> None:
        pass
