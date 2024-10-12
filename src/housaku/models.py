class Doc:
    def __init__(
        self,
        uri: str,
        title: str,
        doc_type: str,
        body: str,
    ) -> None:
        self.uri = uri
        self.title = title
        self.doc_type = doc_type
        self.body = body
