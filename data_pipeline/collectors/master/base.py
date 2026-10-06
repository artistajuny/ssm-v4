from abc import ABC, abstractmethod
from datetime import date

from data_pipeline.collectors.master.models import SecurityMasterRecord


class SecurityMasterCollector(ABC):
    @abstractmethod
    def collect(
        self,
        start_date: date,
        end_date: date,
    ) -> list[SecurityMasterRecord]:
        raise NotImplementedError
