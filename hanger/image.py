from hanger.abc import HangupsObject


class Image(HangupsObject):
    def __init__(self, _client, file, filename=None):
        self._client = _client
        self.file = file
        self.filename = filename

    async def _build_hangups_object(self):
        return await self._client._hangups_client.upload_image(
            self.file, filename=self.filename, return_uploaded_image=True
        )
