# File type preferences and caps

ALLOWED_EXTS = {
    ".py", ".ts", ".tsx", ".js", ".jsx", ".go", ".rs", ".java", ".kt",
    ".cs", ".rb", ".php"
}
SECONDARY_EXTS = {
    ".md", ".yml", ".yaml", ".toml", ".json"
}
IGNORE_DIRS = {
    "node_modules/", "dist/", "build/", ".venv/", ".git/", "__pycache__/"
}

MAX_FILE_BYTES = 120_000       # skip files larger than ~120 KB
MAX_TOTAL_BYTES = 500_000      # cap total text included (~0.5 MB)
MAX_FILES = 50                 # max files per run
PREVIEW_LINES = 80             # first N lines per file
DEFAULT_REF = "HEAD"

