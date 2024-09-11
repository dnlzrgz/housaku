# Housaku (豊作)

Housaku is a powerful yet simple personal search engine that allows you to index and search a wide range of documents and posts.

## Features

- **Multi-Format Support**: Index and search files in various formats, including:
  - Plain Text Files.
  - Markdown.
  - PDF.
  - EPUB.
  - DOCX.
- **Feed Integration**: Index content from your favorite RSS and Atom feeds.
- **Fast search times**: Optimized search algorithm for fast results.
- **Incremental indexing**: Housaku skips already indexed documents, allowing you to gradually build your corpus without having to worry about redundancy.

## WIP

Housaku is an ongoind project, and several major features are in the pipeline, including:

- A user-friendly Web UI.
- A TUI for command-line enthusiasts.
- Document and post update functionality for already indexed items.
- Optimizations tweaks for faster indexing times.
- A better sorting algorithm for search results (maybe the BM25 algorithm).
- A query language for advanced search capabilities.

## Motivation

As someone who stores a wealth of documents on my hard drive—ranging from academic PDFs to personal notes in Obsidian—I often found it challenging to search across multiple applications and file types. I wanted a solution that would allow me to search not only my notes but also important books in my Calibre library and blog posts from my favorite feeds. This inspired me to build Housaku.

## Install

### Via `pip`

```bash
pip install housaku
```

### Via `pipx`

```bash
pipx install housaku
```

### Via `uv`

```bash
uv tool add housaku

# Or

uvx housaku
```

## Usage

### Configuration

To start using Housaku, the first step is to edit the `config.toml` file located at `$XDG_CONFIG_HOME/housaku/config.toml`. This file is generated the first time you run `housaku` and will look something like this:

```toml
# Welcome! This is the configutation file for housaku.

[files]
# Directories to include for indexing.
# Example: include = ["/home/<user>/documents/notes"]
include = []

# Patterns to exclude from the indexing
# Example: exclude = ["*.tmp", "backup", "*.png"]
exclude = []

[feeds]
# List of RSS/Atom feeds to index
# Example: urls = ["https://example.com/feed", "https://anotherexample.com/rss"]
urls = []
```

> Notes: This folder will also contain the SQLite database where all the indexed data will be stored.

To open your `config.toml` file, you can just run the following command:

```bash
housaku config
```

### Indexing

Once you have configured your directories and/or feeds, run the following command to start the indexing process.

```bash
housaku index
```

If you want to specify directories for indexing when running the `index` command, use the `-i` option. For example:

```bash
housaku index -i "/home/<user>/Documents/notes" -i "/home/<user>/Documents/vault/"
```

> Note: Indexing may vary from a few seconds to several minutes, depending on the size and type of files being indexed. You can begin searching as soon as some documents have been indexed, but it's advisable to allow some time for the initial indexing process. Housaku will skip documents and posts that have already been indexed, allowing you to build your corpus gradually.

### Search

Currently, Housaku does not support a query language. It just matches keywords in your search terms with those saved in the database. To perform a search then, use the following command:

```bash
housaku search --query "search engine"

# You can also limit the number of results
housaku search --query "search engine" --limit 5
```

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, feel free to open an issue.
