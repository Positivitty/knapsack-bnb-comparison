from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Item:
    weight: int
    value: int

    @property
    def ratio(self) -> float:
        return self.value / self.weight


@dataclass(frozen=True)
class Instance:
    items: tuple[Item, ...]
    capacity: int

    @property
    def n(self) -> int:
        return len(self.items)

    @classmethod
    def from_items(cls, items, capacity: int) -> "Instance":
        sorted_items = tuple(sorted(items, key=lambda it: it.ratio, reverse=True))
        return cls(items=sorted_items, capacity=capacity)
