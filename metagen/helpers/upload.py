
from s3transfer.manager import TransferManager


class CosmosIdTransferManager(TransferManager):
    def __init__(self, client, config=None, osutil=None, executor_cls=None):
        super(CosmosIdTransferManager, self).__init__(
            client, config=None, osutil=None, executor_cls=None)

    def _register_handlers(self):
        pass