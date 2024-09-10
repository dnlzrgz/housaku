# Sagasu (探す)

Sagasu is a powerful yet simple personal search engine that allows you to index and search a wide range of documents and posts.

## Features

- **Multi-Format Support**: Index and search files in various formats, including:
  - Plain Text Files.
  - Markdown.
  - PDF.
  - EPUB.
  - DOCX.
- **Feed Integration**: Index content from your favorite RSS and Atom feeds.
- **Fast search times**: Optimized search algorithm for fast results.
- **Incremental indexing**: Sagasu skips already indexed documents, allowing you to gradually build your corpus without having to worry about redundancy.

## WIP

Sagasu is an ongoind project, and several major features are in the pipeline, including:

- A user-friendly Web UI.
- A TUI for command-line enthusiasts.
- Document and post update functionality for already indexed items.
- Optimizations tweaks for faster indexing times.
- A better sorting algorithm for search results (maybe the BM25 algorithm).
- A query language for advanced search capabilities.

## Motivation

As someone who stores a wealth of documents on my hard drive—ranging from academic PDFs to personal notes in Obsidian—I often found it challenging to search across multiple applications and file types. I wanted a solution that would allow me to search not only my notes but also important books in my Calibre library and blog posts from my favorite feeds. This inspired me to build Sagasu.

## Install

### Via `pip`

```bash
pip install sagasu
```

### Via `pipx`

```bash
pipx install sagasu
```

### Via `uv`

```bash
uv tool add sagasu

# Or

uvx sagasu
```

## Usage

### Configuration

To start using Sagasu, the first step is to create a `config.toml` file located at `$XDG_CONFIG_HOME/sagasu/config.toml`. This folder will also contain the SQLite database where all the indexed data will be stored.

You configuration file should look something like this:

```config.toml
[files]
include = [
  "/home/<your-username>/Documents/",
]

exclude = [
  ".git",
  ".obsidian",
  ".stfolder",
  ".stversions",
  ".trash",
  "*.mobi"
]

[feeds]
urls = [
  "http://blog.golang.org/feeds/posts/default",
  "http://www.theverge.com/rss/full.xml",
  "https://adrianroselli.com/feed",
  "https://chriscoyier.net/feed/",
  "https://dnlzrgz.com/rss/",
  "https://textual.textualize.io/feed_rss_created.xml",
]
```

### Indexing

Once you have configured your directories and/or feeds, run the following command to start the indexing process.

```bash
sagasu index
```

Indexing may vary from a few seconds to several minutes, depending on the size and type of files being indexed. You can begin searching as soon as some documents have been indexed, but it's advisable to allow some time for the initial indexing process. Sagasu will skip documents and posts that have already been indexed, allowing you to build your corpus gradually.

### Search

Currently, Sagasu does not support a query language. It just matches keywords in your search terms with those saved in the database. To perform a search then, use the following command:

```bash
sagasu search --query "search engine"

# You can also limit the number of results
sagasu search --query "search engine" --limit 5
```

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, feel free to open an issue.
