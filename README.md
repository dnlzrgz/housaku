# Housaku (豊作)

Housaku is a powerful yet simple personal search engine built on top of SQLite's FTS5.

## Features

- **Support for multiple file formats**: Index files in a variety of formats, including:
  - Plain text tiles.
  - Markdown.
  - PDF.
  - EPUB.
  - DOCX.
- **Basic Web Scraping**: In addition to personal files, you can also index posts from your favorite RSS/Atom feeds.
- **Parallel File Processing**: Housaku utilizes multi-threading to process files simultaneously, making the indexing process incredibly fast.
- **Powered by SQLite's FTS5**: Built on the advanced full-text search capabilities of SQLite's FTS5 extension.
- **Relevant Results with BM25**: Search results are sorted using the BM25 algorithm, ensuring the most relevant results.

## WIP

Housaku is an ongoind project, and several major features are in the pipeline, including:

- A user-friendly Web interface.
- A TUI for command-line enthusiasts.

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
# Welcome! This is the configuration file for housaku.

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

### Search

To perform a search, you just need to use the following command:

```bash
housaku search --query "search engine"

# By default the limit is 20
housaku search --query "search engine" --limit 5
```

## Contributing

Contributions are welcome! If you have suggestions for improvements or new features, feel free to open an issue.
