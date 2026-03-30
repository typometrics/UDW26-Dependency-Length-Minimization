# AI Disclosure

## Full disclosure of AI use in this research

This paper was conceived, written, and coded entirely by an AI system, with a human operator providing prompts and accepting or rejecting the proposed work. We believe full transparency about this process is essential.

### The prompt

This project was inspired by [David Yanagizawa-Drott's experiment](https://x.com/YanagizawaD/status/2022034189395407093), in which he prompted Claude Code with:

> "I always dreamed of becoming a macroeconomist one day. I need a job market paper. Desperately. Since I only know applied micro, I need your help. Find a novel angle, I don't know what macro does these days."

This UDW 2026 paper started with a similar prompt, given to **Claude Opus 4.6** in VS Code (GitHub Copilot Chat, agent mode):

> *I always dreamt of becoming a syntactician and a typologist one day.
> I want to submit a paper to the UDW workshop, deadline next monday. https://universaldependencies.org/udw26/cfp.html
> Can you help me?*

### How the paper was made

- **The idea came from Claude.** The central research question — separating functional from lexical dependency length minimization across Universal Dependencies — was proposed by the AI, not by the human operator.
- **The human's role was verification and editorial oversight.** At each step, Claude proposed a direction, wrote the code, ran the analysis, and drafted the text. The human operator reviewed, prompted for revisions, and accepted or rejected proposed work, but did not originate ideas, write code, or draft prose. The code, analyses, and results were checked by the author.
- **The idea evolved during development.** The functional vs. lexical opposition that became the core of the paper was not part of the initial plan. It emerged as Claude wrote and tested different analysis scripts, explored the data, and iteratively refined the research question.
- **Prior art was searched by the human.** Once the idea and a first draft were in place, the human used [Google Scholar Labs](https://scholar.google.com/scholar_labs) to search for related work. The results were given to Claude, who integrated them into the paper.
- **Many hours of prompting and rereading were invested**, but the principle remained throughout: **no central idea by the human, no line of code written by the human, no single word typed by the human** (beyond the prompts themselves).
- **Anonymous reviewers and a colleague were crucial.** The reviews by anonymous UDW 2026 reviewers and by Sylvain Kahane were essential for improving the final version. Their feedback was given to Claude, which implemented the revisions. Both the author and the reviewers judged the findings scientifically interesting enough to merit revision and discussion.

### Why disclose this?

As Yanagizawa-Drott wrote about his own experiment:

> *"We live in one of two worlds right now:*
>
> *1. This is real research, but it has nothing to do with my expertise (I am not a macroeconomist) and so some other human expert needs to verify it is real*
>
> *2. This is not real research, and I just had a negative externality by polluting the information environment*
>
> *In a world of machine-speed generated papers, which is real, we have a problem either way.*
>
> *And what happens to matching in the academic labor market, I'm not smart enough to figure out (I am not a labor economist).*
>
> *But it seems to me it could be a problem too."*

This is an interesting experiment. We make no claims about whether machine-generated research is "real" research. We do believe that the community deserves to know exactly how a paper was produced, and we hope this disclosure contributes to an honest conversation about the role of AI in scientific work.

An open question is whether AI-generated hypotheses and text, curated and verified by a human, should count as a scientific result, and whether this may become a standard category of research output. More broadly, this raises an old question about novelty: can LLMs create genuinely new ideas, can humans, or are both primarily recombining from a finite space of possibilities, as in Borges' "Library of Babel"? We do not claim to resolve this question here, but we consider it central for future norms of authorship, credit, and evaluation.

### Tools used

- **LLM**: Claude Opus 4.6 (Anthropic), via GitHub Copilot Chat in VS Code (agent mode)
- **Literature search**: Google Scholar Labs
- **Data**: Universal Dependencies v2.17, Surface-Syntactic Universal Dependencies v2.17
