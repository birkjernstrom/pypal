# -*- coding: utf-8 -*-

from pypal.ipn import Response


STATUS_CREATED = 'CREATED'
STATUS_COMPLETED = 'COMPLETED'
STATUS_INCOMPLETE = 'INCOMPLETE'
STATUS_ERROR = 'ERROR'
STATUS_REVERSALERROR = 'REVERSALERROR'
STATUS_PROCESSING = 'PROCESSING'
STATUS_PENDING = 'PENDING'

class Response(Response):
    def get_status(self):
        status = getattr(self, '_status', None)
        if status:
            return status

        status = self.get('status').upper()
        setattr(self, '_status', status)
        return status

    status = property(get_status)

    @property
    def is_status_created(self):
        return self.status == STATUS_CREATED

    @property
    def is_status_completed(self):
        return self.status == STATUS_COMPLETED

    @property
    def is_status_incomplete(self):
        return self.status == STATUS_INCOMPLETE

    @property
    def is_status_error(self):
        return self.status == STATUS_ERROR

    @property
    def is_status_reversal_error(self):
        return self.status == STATUS_REVERSALERROR

    @property
    def is_status_processing(self):
        return self.status == STATUS_PROCESSING

    @property
    def is_status_pending(self):
        return self.status == STATUS_PENDING

    def get_utc_request_date(self):
        timestamp = self.get('payment_request_date', None)
        if not timestamp:
            return None

        from pypal.util import convert_timestamp_into_utc
        return convert_timestamp_into_utc(timestamp)
