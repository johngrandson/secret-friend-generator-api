import logging
from typing import Any

log = logging.getLogger(__name__)


class InstanceManager:
    """Dynamic class loader for plugin-style module instantiation."""

    def __init__(
        self,
        class_list: list[str] | None = None,
        instances: bool = True,
    ) -> None:
        if class_list is None:
            class_list = []
        self.instances: bool = instances
        self.cache: list[Any] | None = None
        self.class_list: list[str] = []
        self.update(class_list)

    def get_class_list(self) -> list[str]:
        return self.class_list

    def add(self, class_path: str) -> None:
        self.cache = None
        if class_path not in self.class_list:
            self.class_list.append(class_path)

    def remove(self, class_path: str) -> None:
        self.cache = None
        self.class_list.remove(class_path)

    def update(self, class_list: list[str]) -> None:
        self.cache = None
        self.class_list = class_list

    def all(self) -> list[Any]:
        class_list = list(self.get_class_list())
        if not class_list:
            self.cache = []
            return []

        if self.cache is not None:
            return self.cache

        results: list[Any] = []
        for cls_path in class_list:
            module_name, class_name = cls_path.rsplit(".", 1)
            try:
                module = __import__(module_name, {}, {}, class_name)
                cls = getattr(module, class_name)
                if self.instances:
                    results.append(cls())
                else:
                    results.append(cls)
            except Exception as e:
                log.exception(f"Unable to import {cls_path}. Reason: {e}")
                continue

        self.cache = results
        return results
