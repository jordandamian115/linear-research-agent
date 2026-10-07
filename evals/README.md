# Inquiry evals

Each inquiry was run on the real agent path: Agent 1 calls arXiv and web search, then Agents 2, 3, the RAG agent, Agent 5, and Agent 6 run once each. The paper, the records Agent 1 kept, and a verdict are under `evals/inquiries/<slug>/`.

Word counts are the final paper from the abstract through the notes.

## Exact cause

“the revolutionary war” was reduced to the single stem “revolutionary”. The writer and the arXiv keyword fallback dropped every word of three letters, so “war” was not a term. The same-sense check ran only when two or more terms remained. Cultural-algorithm papers and an image de-rendering paper about “revolutionary artefacts” therefore counted as full matches. The writer joined those sentences to one real Revolutionary War page with the fixed line “The next record carries that idea one step further.” Two cues helped file them into one sequence: “by means of” was read as a definition, and “the course of human events” was read as a classroom.

The shared filter now keeps short content words, does not search a multi-word question as one leftover word, and does not teach a record that misses part of the question or does not share a concrete word with the sentence that says what the subject is. No inquiry is special-cased.

## RAG shelf

No RAG document was removed. The shelf text does not enter the claims. In the paper Jordan saw, the references were an arXiv paper on revolutionary algorithms, an arXiv paper on de-rendering artefacts, and the American Battlefield Trust page. The footnotes were the usual style notes (sentence length, piled modifiers, citation, specificity, index coverage). Lincoln, the King Institute page, Hyland, and the other indexed texts were not quoted as claims.

## What is working

- Search. Agent 1 still calls arXiv and Tavily for the typed question. A keyless Tavily call returns real pages and records the HTTP status. The shelf is not the search index.
- Writer. A paper that works starts from what the subject is and continues only with records that share that subject. “the revolutionary war” now opens on the war, then the colonial tensions and Lexington and Concord. It does not cite the algorithm papers.
- Shelf. It still runs once, after the revision, and only compares prose.
- Graphic. Agent 6 still draws five or six steps from that paper’s claims, in the paper’s order, each a concept and an example. It does not draw the agents or the search. A thin or off-topic paper still produces a picture of those sentences.

## Results

17 worked. 8 fell through.

| Inquiry | Result | Words | Failure |
| --- | --- | --- | --- |
| hypertrophy in bodybuilding | worked | 811 | |
| quantum physics | worked | 952 | |
| quantum computing | worked | 960 | |
| the revolutionary war | worked | 764 | |
| the revolutionary way | fell through | 759 | Search relevance. The only record that contains both words is a 3D-printing poster, so the paper is not an overview of one subject. |
| ghengis khan | worked | 705 | |
| sun tzu | worked | 942 | |
| the wolf of wallstree | worked | 707 | |
| stock market | worked | 581 | |
| porche | worked | 551 | |
| the boston tea party | worked | 586 | |
| the silk road | fell through | 540 | Writer stitching. The paper stops after two sentences about the maritime name and does not tell how the route worked. |
| the fall of the berlin wall | fell through | 614 | Writer stitching. Two sentences name the collapse and stop, which is a tidbit rather than an overview. |
| cleopatra | fell through | 617 | Writer stitching. Two sentences name the queen and the dynasty and then stop. |
| ada lovelace | worked | 592 | |
| marie curie | fell through | 535 | Writer stitching. Three sentences praise her and do not say what she discovered or how the work proceeded. |
| the printing press | worked | 649 | |
| a compass | fell through | 620 | Search relevance. The claims describe a particle-physics apparatus named COMPASS, not how a magnetic compass works. |
| the telescope | worked | 661 | |
| how a refrigerator works | worked | 549 | |
| how vaccines work | worked | 897 | |
| how a lock and key works | fell through | 548 | Writer stitching. Only two sentences survived, so the paper is a tidbit and does not walk through how a lock works. |
| transformer | worked | 711 | |
| diffusion | fell through | 462 | Writer stitching. The paper is a short tidbit (462 words), not an overview a person could talk through. |
| entropy | worked | 593 | |

Rerun with `PYTHONPATH=/workspace python3 evals/run.py` from the repo root. Pass inquiry strings to rerun a subset.
