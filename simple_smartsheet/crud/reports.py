import logging
from typing import cast, Dict, Any

from simple_smartsheet.crud.base import CRUDAttrs, CRUDRead, AsyncCRUDRead
from simple_smartsheet.models import Report

logger = logging.getLogger(__name__)


class ReportCRUDMixin(CRUDAttrs):
    base_url = "/reports"
    get_params = {"pageSize": "10000", "level": "2", "include": "objectValue"}


class ReportCRUD(ReportCRUDMixin, CRUDRead[Report]):
    factory = Report

    def _get_by_id(self, id: int) -> Report:
        endpoint = self.get_url.format(id=id)
        page = 1
        data = cast(
            Dict[str, Any],
            self.smartsheet._get(endpoint, path=None, params=self.get_params),
        )
        full_data = data
        while data["totalRowCount"] != len(full_data["rows"]):
            page += 1
            params = {"page": str(page)}
            if self.get_params:
                params.update(self.get_params)
            data = cast(
                Dict[str, Any], self.smartsheet._get(endpoint, path=None, params=params)
            )
            full_data["rows"].extend(data["rows"])
        return self._create_obj_from_data(full_data)


class AsyncReportCRUD(ReportCRUDMixin, AsyncCRUDRead[Report]):
    factory = Report

    async def _get_by_id(self, id: int) -> Report:
        endpoint = self.get_url.format(id=id)
        page = 1
        data = cast(
            Dict[str, Any],
            await self.smartsheet._get(endpoint, path=None, params=self.get_params),
        )
        full_data = data
        while data["totalRowCount"] != len(full_data["rows"]):
            page += 1
            params = {"page": str(page)}
            if self.get_params:
                params.update(self.get_params)
            data = cast(
                Dict[str, Any],
                await self.smartsheet._get(endpoint, path=None, params=params),
            )
            full_data["rows"].extend(data["rows"])
        return self._create_obj_from_data(full_data)
