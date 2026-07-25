import argparse

from app.services import ResumeRAG


def main() -> None:
    parser = argparse.ArgumentParser(description="Find resume evidence for a job description.")
    parser.add_argument("job_description", help="Quote the complete job description")
    args = parser.parse_args()
    answer, sources = ResumeRAG().answer(args.job_description)
    print(answer)
    print("\nRetrieved evidence:")
    for source in sources:
        print(f"- {source.source_file} (chunk {source.chunk_index}, {source.similarity:.3f})")


if __name__ == "__main__":
    main()

