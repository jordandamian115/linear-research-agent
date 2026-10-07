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

24 worked. 1 fell through. The eight that had fallen through were rerun after the writer was changed to keep every record that is about the subject and to write the overview from those sentences. A page that only borrows the name stays out. “the revolutionary way” still has no page about one subject.

| Inquiry | Result | Words | Failure |
| --- | --- | --- | --- |
| hypertrophy in bodybuilding | worked | 811 | |
| quantum physics | worked | 952 | |
| quantum computing | worked | 960 | |
| the revolutionary war | worked | 764 | |
| the revolutionary way | fell through | 304 | Search relevance. No retrieved title is a page about this subject, so the paper does not invent one. |
| ghengis khan | worked | 705 | |
| sun tzu | worked | 942 | |
| the wolf of wallstree | worked | 707 | |
| stock market | worked | 581 | |
| porche | worked | 551 | |
| the boston tea party | worked | 586 | |
| the silk road | worked | 1622 | |
| the fall of the berlin wall | worked | 1260 | |
| cleopatra | worked | 1514 | |
| ada lovelace | worked | 592 | |
| marie curie | worked | 1276 | |
| the printing press | worked | 649 | |
| a compass | worked | 1099 | |
| the telescope | worked | 661 | |
| how a refrigerator works | worked | 549 | |
| how vaccines work | worked | 897 | |
| how a lock and key works | worked | 977 | |
| transformer | worked | 711 | |
| diffusion | worked | 917 | |
| entropy | worked | 593 | |

Rerun with `PYTHONPATH=/workspace python3 evals/run.py` from the repo root. Pass inquiry strings to rerun a subset.
