from aiohttp.web import StaticResource


class NoCacheStaticResource(StaticResource):
    """
    A static resource handler that prevents caching for HTML and CSS files.

    Inherits from aiohttp.web.StaticResource and overrides the _handle method
    to add a 'Cache-Control: no-cache' header to responses for files ending
    with the endings provided in the constructor.
    This ensures that browsers always fetch the latest version of these files.
    """

    def __init__(
        self,
        prefix,
        directory,
        name=None,
        expect_handler=None,
        chunk_size=256 * 1024,
        show_index=False,
        follow_symlinks=False,
        append_version=False,
        file_endings=None,
    ):
        super().__init__(
            prefix,
            directory,
            name=name,
            expect_handler=expect_handler,
            chunk_size=chunk_size,
            show_index=show_index,
            follow_symlinks=follow_symlinks,
            append_version=append_version,
        )
        self.file_endings = file_endings

    async def _handle(self, request):
        resp = await super()._handle(request)
        if self.file_endings is not None and request.path.lower().endswith(
            self.file_endings
        ):
            resp.headers["Cache-Control"] = "no-cache"
        return resp
