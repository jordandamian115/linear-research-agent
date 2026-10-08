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

Rerun with `PYTHONPATH=/workspace python3 evals/run.py` from the repo root. Pass inquiry strings to rerun a subset. The sentence-length set is `PYTHONPATH=/workspace python3 evals/run.py --long`.

## Sentence-length questions

Each question is 5 to 30 words. The first one is the inquiry Jordan ran. The others cover health, history, how things work, people, and ordinary objects. Word counts are the question itself, then the final paper from the abstract through the notes.

### What went wrong on the B12 question

The search worked. Tavily returned HTTP 200 and five pages on vitamin B12 (Healthline, MedPark, a review of natural and synthetic forms, GoodRx, and a clinic page). arXiv’s keyword fallback used the first content words, including “tell”, and returned “Back to the Moon” because that abstract says “much to tell us about”.

The writer then required every content word of the sentence in the title, and “tell” was one of those words. No health title contains “tell”, “consistent”, and “usage” together, so every page was set aside, including the five that are about vitamin B12. The paper was 328 words and did not teach a claim. This is the same class of bug as the “revolutionary” stem filter and the early stop: the subject match was too strict, and it was not a vitamin special case.

The bad passage, from the abstract and again from “What the records support”:

> This note records the search for tell me about the medicinal benefits of consistent vitamin B12 usage. The search returned records, but none of them is a page about this subject. Nothing was invented to fill the gap.

The introduction asked “what tell me about the medicinal benefits of consistent vitamin B12 usage is”. The limits named the five vitamin B12 pages and the moon paper together, as if none of them were the subject.

The shared repair does not add a medical rule. An opening verb such as “tell” is not a search term. A question of four or more content words is matched on the two words its records share (here, vitamin and B12), and those words have to occur together. A question of three content words or fewer is unchanged, so “the revolutionary war” is still both words. Claims stay inside the retrieved sentences, including the GoodRx limit that a supplement is not a proven treatment when levels are not low. The rerun opens on vitamin B12 as a water-soluble vitamin that forms red blood cells, and it sets unrelated records aside.

### Results

18 worked. 0 fell through. Five had fallen through on the first pass of this set (two nights without sleep, the compass bearing, eyeglasses, the cast-iron skillet, and the bicycle gear). They were rerun after the shared repair.

| Inquiry | Question words | Result | Paper words | Failure |
| --- | --- | --- | --- | --- |
| tell me about the medicinal benefits of consistent vitamin B12 usage | 11 | worked | 1773 | |
| how does a daily walk of thirty minutes affect blood pressure in adults | 13 | worked | 1196 | |
| what happens in the body when someone has not slept for two nights | 13 | worked | 782 | |
| why do some people get seasonal allergies every spring and others do not | 13 | worked | 1724 | |
| how do vaccines train the immune system to recognize a virus later | 12 | worked | 1770 | |
| how did the printing press change the way ideas spread across early modern Europe | 14 | worked | 1343 | |
| what led ordinary colonists to dump tea into Boston harbor in 1773 | 12 | worked | 986 | |
| why did the Berlin Wall fall in November 1989 and what changed afterward | 13 | worked | 1307 | |
| how did Cleopatra keep her throne while Rome was expanding into Egypt | 12 | worked | 1324 | |
| what did Marie Curie actually discover and why did that work matter to medicine | 14 | worked | 997 | |
| how did Ada Lovelace describe the analytical engine and what could it do | 13 | worked | 981 | |
| why is Sun Tzu still read by people who are not fighting a war | 14 | worked | 1296 | |
| how does a pin tumbler lock keep a door shut until the right key is used | 16 | worked | 912 | |
| how does a kitchen refrigerator move heat out of the food compartment | 12 | worked | 1198 | |
| what does a magnetic compass needle do and how do you take a bearing with it | 16 | worked | 1370 | |
| how does a pair of eyeglasses correct blurry vision for a nearsighted person | 13 | worked | 1036 | |
| why does a cast iron skillet hold heat longer than a thin steel pan | 14 | worked | 1032 | |
| how does a bicycle gear let a rider climb a hill without standing up | 14 | worked | 893 | |
