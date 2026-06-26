from pathlib import Path

EXAMPLES_DIR = Path("data/bm25_examples")

def main() -> None:
    files = list(EXAMPLES_DIR.glob("*.txt"))
    print(f"BM25 examples found: {len(files)}")
    for file in files:
        print(f"- {file.stem}")

if __name__ == "__main__":
    main()
