from abc import ABC, abstractmethod
from typing import List, Dict
import hashlib


class BaseParser(ABC):
    SOURCE_NAME: str = ""
    SOURCE_TYPE: str = "credit_card"

    @abstractmethod
    def parse(self, file_path: str) -> List[Dict]:
        pass

    @staticmethod
    def make_dedup_hash(source: str, date_str: str, amount: str, description: str) -> str:
        raw = f"{source}|{date_str}|{amount}|{description}"
        return hashlib.md5(raw.encode()).hexdigest()
