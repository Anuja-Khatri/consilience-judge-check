"""Decode the agent submissions printed in the benchmark paper's appendix.

Input: the TeX source of arXiv 2605.26087v2 (download https://arxiv.org/e-print/2605.26087v2
and unpack it). Output: pilot/paper_examples.json, one record per printed
submission: the program exactly as printed, the fitted parameters, trajectory
error, explanation and judge score the paper prints beside it.

Nothing is retyped by hand. The only decoding is of two TeX escapes inside the
explanations (a unit vector and a square root), listed in ESCAPES.

Usage: python pilot/extract_paper_examples.py path/to/arxiv_version.tex
"""
import hashlib, json, os, re, sys

ESCAPES = {r"(*@$\hat{r}$@*)": "r_hat", r"(*@$\sqrt{p_1/p_2}$@*)": "sqrt(p1/p2)"}
BAR = "=" * 60

def main(tex_path):
    tex = open(tex_path, encoding="utf-8").read()
    sec = tex[tex.index(r"\section{Example outputs}"):tex.index(r"\section{Failure mode analysis")]
    out = []
    for m in re.finditer(r"\\begin\{lstlisting\}\[style=logstyle,caption=\{(.*?)\},label=\{(.*?)\}\]\n(.*?)\\end\{lstlisting\}", sec, re.S):
        caption, label, body = m.groups()
        parts = body.split(BAR)
        # parts: '', '\nDiscovered law:\n', code, '\nEvaluation:\n', eval, '\nExplanation evaluation:\n', expl
        assert parts[1].strip() == "Discovered law:" and parts[3].strip() == "Evaluation:", label
        code, evaluation, expl = parts[2].strip("\n") + "\n", parts[4], parts[6]
        world = re.findall(r"\\subsection\{\\texttt\{(.*?)\}\}", sec[:m.start()])[-1].replace("\\_", "_")
        fitted = {}
        fm = re.search(r"Fitted parameters: (.*)", evaluation)
        if fm:
            for kv in fm.group(1).split(","):
                k, v = kv.strip().split("=")
                fitted[k] = float(v)
        explanation = re.search(r"Agent explanation: (.*?)\n\n", expl, re.S).group(1).strip()
        for a, b in ESCAPES.items():
            explanation = explanation.replace(a, b)
        out.append({
            "world": world, "caption": caption, "source": code,
            "source_sha256": hashlib.sha256(code.encode()).hexdigest(),
            "printed_fitted_parameters": fitted,
            "printed_fit_note": (re.search(r"\[fit[^\]]*\]", evaluation) or [None])[0],
            "printed_mean_particle_mse": (lambda g: float(g.group(1)) if g else None)(re.search(r"Mean (?:particle|probe) MSE[^:\n]*:\s*([\d.]+|inf)", evaluation)),
            "printed_result": re.search(r"Result: (\w+)", evaluation).group(1),
            "explanation": explanation,
            "printed_judge_raw_score": int(float(re.search(r"\(raw ([\d.]+)/10\)", expl).group(1))),
        })
    here = os.path.dirname(os.path.abspath(__file__))
    json.dump({"paper": "arXiv:2605.26087v2, appendix 'Example outputs'",
               "tex_sha256": hashlib.sha256(tex.encode()).hexdigest(), "examples": out},
              open(os.path.join(here, "paper_examples.json"), "w"), indent=1, ensure_ascii=False)
    for e in out:
        print(e["world"], e["printed_result"], e["printed_mean_particle_mse"], e["printed_judge_raw_score"], e["printed_fitted_parameters"])

if __name__ == "__main__":
    main(sys.argv[1])
