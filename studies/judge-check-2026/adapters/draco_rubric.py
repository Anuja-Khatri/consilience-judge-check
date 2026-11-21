"""DRACO's rubrics as the plain table `consilience rubric scan` reads.

One row per criterion: id, group (the task), section, weight, criterion. The id is the
first 12 hex digits of sha256(task id + criterion id), as in the rest of this study.
The dataset is the reader's own copy (perplexity-ai/draco, MIT); nothing is stored here.

Usage: python adapters/draco_rubric.py /path/to/test.jsonl rubric.csv
"""
import csv, hashlib, json, sys


def main(src: str, dst: str) -> None:
    n = 0
    with open(dst, "w", newline="", encoding="utf-8") as f:
        f.write("# DRACO (perplexity-ai/draco, MIT): every rubric criterion, one per row.\n")
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["id", "group", "domain", "section", "weight", "criterion"])
        for line in open(src, encoding="utf-8"):
            task = json.loads(line)
            for sec in json.loads(task["answer"])["sections"]:
                for c in sec["criteria"]:
                    ident = hashlib.sha256((task["id"] + c["id"]).encode()).hexdigest()[:12]
                    w.writerow([ident, task["id"], task["domain"], sec["id"], c["weight"], c["requirement"]])
                    n += 1
    print(n, "criteria written to", dst)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
