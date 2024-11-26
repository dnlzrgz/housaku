class Doc:
    def __init__(
        self,
        uri: str,
        title: str,
        body: str,
        doc_type: str,
        last_modified: str | None = None,
    ) -> None:
        self.uri = uri
        self.title = title
        self.body = body
        self.doc_type = doc_type
        self.last_modified = last_modified
