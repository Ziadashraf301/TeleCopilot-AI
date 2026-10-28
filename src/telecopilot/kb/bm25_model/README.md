# BM25 model files (vendored)

Files from the Hugging Face repository [`Qdrant/bm25`](https://huggingface.co/Qdrant/bm25), revision
`22b8d2af71a76161e18dd432d2cee0eefa66e412`, licensed **Apache-2.0** by Qdrant. Only the files TeleCopilot uses are kept:
`config.json`, `english.txt` and `arabic.txt` (stopword lists). They are unchanged.

Why vendored: FastEmbed otherwise downloads them from the Hub on first use. Shipping them (7 KB) keeps tests, CI and
the Docker image offline and pins the stopword lists, so the same text always gives the same sparse vector.
