# Research brief: transformer

## Question
transformer

## Search log

arXiv returned 5 record(s) for this question.

tavily_search was called. Key present: no. HTTP status: 200. Mode: keyless. Tavily returned 5 page(s), separate from arXiv.

These searches are not limited to the reference shelf. The shelf is used later, only to compare prose.


Tavily page: What is a Transformer | Schneider Electric United States — https://www.se.com/us/en/work/featured-articles/what-is-a-transformer

Tavily page: Everything You Need to Know About Transformers | Step-Up, Step-Down & How They Work #transformers — https://www.youtube.com/watch?v=nmFABcXboTI&vl=en

Tavily page: Transformer - Wikipedia — https://en.wikipedia.org/wiki/Transformer

Tavily page: 9 Transformers – 6.390 - Intro to Machine Learning — https://introml.mit.edu/notes/transformers.html

Tavily page: Transformer Basics — https://www.electronics-tutorials.ws/transformer/transformer-basics.html

## Sources

[1] PyramidTNT: Improved Transformer-in-Transformer Baselines with Pyramid Architecture
Type: arXiv
Authors: Kai Han, Jianyuan Guo, Yehui Tang, Yunhe Wang
Date: 2022-01-04
URL: https://arxiv.org/abs/2201.00978v1
Excerpt: Transformer networks have achieved great progress for computer vision tasks. Transformer-in-Transformer (TNT) architecture utilizes inner transformer and outer transformer to extract both local and global representations. In this work, we present new TNT baselines by introducing two advanced designs: 1) pyramid architecture, and 2) convolutional stem. The new "PyramidTNT" significantly improves the original TNT by establishing hierarchical representations. PyramidTNT achieves better performances than the previous state-of-the-art vision transformers such as Swin Transformer. We hope this new baseline will be helpful to the further research and application of vision transformer. Code will be available at https://github.com/huawei-noah/CV-Backbones/tree/master/tnt_pytorch.

[2] Learning to Cluster Faces via Transformer
Type: arXiv
Authors: Jinxing Ye, Xioajiang Peng, Baigui Sun, Kai Wang, Xiuyu Sun, Hao Li, Hanqing Wu
Date: 2021-04-23
URL: https://arxiv.org/abs/2104.11502v1
Excerpt: Face clustering is a useful tool for applications like automatic face annotation and retrieval. The main challenge is that it is difficult to cluster images from the same identity with different face poses, occlusions, and image quality. Traditional clustering methods usually ignore the relationship between individual images and their neighbors which may contain useful context information. In this paper, we repurpose the well-known Transformer and introduce a Face Transformer for supervised face clustering. In Face Transformer, we decompose the face clustering into two steps: relation encoding and linkage predicting. Specifically, given a face image, a \textbf{relation encoder} module aggregates local context information from its neighbors and a \textbf{linkage predictor} module judges whether a pair of images belong to the same cluster or not. In the local linkage graph view, Face Transformer can generate more robust node and edge representations compared to existing methods. Experiments on both MS-Celeb-1M and DeepFashion show that our method achieves state-of-the-art performance, e.g., 91.12\% in pairwise F-score on MS-Celeb-1M.

[3] MLP Can Be A Good Transformer Learner
Type: arXiv
Authors: Sihao Lin, Pumeng Lyu, Dongrui Liu, Tao Tang, Xiaodan Liang, Andy Song, Xiaojun Chang
Date: 2024-04-08
URL: https://arxiv.org/abs/2404.05657v1
Excerpt: Self-attention mechanism is the key of the Transformer but often criticized for its computation demands. Previous token pruning works motivate their methods from the view of computation redundancy but still need to load the full network and require same memory costs. This paper introduces a novel strategy that simplifies vision transformers and reduces computational load through the selective removal of non-essential attention layers, guided by entropy considerations. We identify that regarding the attention layer in bottom blocks, their subsequent MLP layers, i.e. two feed-forward layers, can elicit the same entropy quantity. Meanwhile, the accompanied MLPs are under-exploited since they exhibit smaller feature entropy compared to those MLPs in the top blocks. Therefore, we propose to integrate the uninformative attention layers into their subsequent counterparts by degenerating them into identical mapping, yielding only MLP in certain transformer blocks. Experimental results on ImageNet-1k show that the proposed method can remove 40% attention layer of DeiT-B, improving throughput and memory bound without performance compromise. Code is available at https://github.com/sihaoevery/lambda_vit.

[4] Music Transformer
Type: arXiv
Authors: Cheng-Zhi Anna Huang, Ashish Vaswani, Jakob Uszkoreit, Noam Shazeer, Ian Simon, Curtis Hawthorne, Andrew M. Dai, Matthew D. Hoffman, Monica Dinculescu, Douglas Eck
Date: 2018-09-12
URL: https://arxiv.org/abs/1809.04281v3
Excerpt: Music relies heavily on repetition to build structure and meaning. Self-reference occurs on multiple timescales, from motifs to phrases to reusing of entire sections of music, such as in pieces with ABA structure. The Transformer (Vaswani et al., 2017), a sequence model based on self-attention, has achieved compelling results in many generation tasks that require maintaining long-range coherence. This suggests that self-attention might also be well-suited to modeling music. In musical composition and performance, however, relative timing is critically important. Existing approaches for representing relative positional information in the Transformer modulate attention based on pairwise distance (Shaw et al., 2018). This is impractical for long sequences such as musical compositions since their memory complexity for intermediate relative information is quadratic in the sequence length. We propose an algorithm that reduces their intermediate memory requirement to linear in the sequence length. This enables us to demonstrate that a Transformer with our modified relative attention mechanism can generate minute-long compositions (thousands of steps, four times the length modeled in Oore et al., 2018) with compelling structure, generate continuations that coherently elaborate on a given motif, and in a seq2seq setup generate accompaniments conditioned on melodies. We evaluate the Transformer with our relative attention mechanism on two datasets, JSB Chorales and Piano-e-Competition, and obtain state-of-the-art results on the latter.

[5] Transformer Transformer: A Unified Model for Motion-Conditioned Robot Co-design
Type: arXiv
Authors: Huy Ha, C. Karen Liu, Shuran Song
Date: 2026-07-28
URL: https://arxiv.org/abs/2607.25798v1
Excerpt: An often overlooked factor of robot manipulation performance is the embodiment of the robot itself. Motivated by this problem, we study motion-conditioned robot co-design, where the goal is to generate complete robot designs that track target end-effector trajectories (from human demonstrations) while optimizing user-defined rewards. We introduce Transformer Transformer, a diffusion transformer trained on RoboTokens, a unified tokenization of robot embodiments, states, and actions. The same architecture can be used across embodiment spaces (e.g., wheeled bimanual, quadrupeds, humanoids) and use cases (embodiment generation, cross embodiment controller). Rather than overfitting to one reward function, Transformer Transformer is a dynamics model, whose reward-agnostic state and action predictions can be converted into reward-specific value predictions. These value predictions are used to steer embodiment diffusion towards high value robot designs, through a procedure we call Dynamics Self-Guidance. Experiments across multiple design spaces show zero-shot optimization of unseen rewards and trajectories, improving performance and runtime over the evolutionary baseline. Finally, we fabricated an optimized ALOHA design, which reduced tracking error by over 70% compared to the original design.

[6] What is a Transformer | Schneider Electric United States
Type: Tavily
Authors: Author not listed
Date: date not listed
URL: https://www.se.com/us/en/work/featured-articles/what-is-a-transformer
Excerpt: A transformer is an electrical device that transfers energy from one electric circuit to another using the process of electromagnetic induction. The main purpose of an electrical transformer is to adjust the voltage levels up or down between two circuits without changing the frequency, which makes controlling and delivering power much easier and more energy-friendly. [...] ## A transformer is an electrical device that transfers energy from one electric circuit to another using the process of electromagnetic induction. The main purpose of an electrical transformer is to adjust the voltage levels up or down between two circuits without changing the frequency, which makes controlling and delivering power much easier and more energy-friendly. [...] Choose a video # What is a transformer? ## A transformer is an electrical device that transfers energy from one electric circuit to another using the process of electromagnetic induction. The main purpose of an electrical transformer is to adjust the voltage levels up or down between two circuits without changing the frequency, which makes controlling and delivering power much easier and more energy-friendly.

[7] Everything You Need to Know About Transformers | Step-Up, Step-Down & How They Work #transformers
Type: Tavily
Authors: Author not listed
Date: date not listed
URL: https://www.youtube.com/watch?v=nmFABcXboTI&vl=en
Excerpt: [0:25] how does it work? A transformer is an electrical device that uses electromagnetic induction to [0:32] change the voltage of an alternating current AC without changing its frequency. It's important [0:37] to note that transformers do not work for direct current DC applications. Unlike motors, [0:43] it has no moving parts. Instead, it relies on two separated coils of copper wire wrapped

[8] Transformer - Wikipedia
Type: Tavily
Authors: Author not listed
Date: date not listed
URL: https://en.wikipedia.org/wiki/Transformer
Excerpt: From Wikipedia, the free encyclopedia Device to couple energy between circuits This article is about the electrical component. For other uses, see Transformer (disambiguation) "Transformer (disambiguation)"). TransformerImage 4: A transformer consisting of two coils of copper wire wrapped around an oval magnetic core [...] a single lamp (or other electric device) affected the voltage supplied to all others on the same circuit. Many adjustable transformer designs were introduced to compensate for this problematic characteristic of the series circuit, including those employing methods of adjusting the core or bypassing the magnetic flux around part of a coil.( Efficient, practical transformer designs did not appear until the 1880s, but within a decade, the transformer would be instrumental in the war of the [...] An O-core transformer consisting of two coils of copper wire wrapped around a magnetic core Component typePassive "Passivity (engineering)") Working principleElectromagnetic induction InventorMichael Faraday( Invention year 1831 Electronic symbol Image 5Image 6 Transformer with iron core (left) and Transformer IEC form 1 (right)

[9] 9 Transformers – 6.390 - Intro to Machine Learning
Type: Tavily
Authors: Author not listed
Date: date not listed
URL: https://introml.mit.edu/notes/transformers.html
Excerpt: Transformers are a very recent family of architectures that were originally introduced in the field of natural language processing (NLP) in 2017, as an approach to process and understand human language. Since then, they have revolutionized not only NLP but also other domains such as image processing and multi-modal generative AI. Their scalability and parallelizability have made them the backbone of large-scale foundation models, such as GPT, BERT, and Vision Transformers (ViT), powering many [...] A notable strength of transformers is their capacity for parallel processing. Transformers process entire sequences simultaneously rather than sequentially token-by-token. This parallelization significantly boosts computational efficiency and makes it feasible to train larger and deeper models. [...] processed one after another. Transformers offer many advantages over RNNs, including their ability to process all items in a sequence in a _parallel_ fashion (as do CNNs).

[10] Transformer Basics
Type: Tavily
Authors: Author not listed
Date: date not listed
URL: https://www.electronics-tutorials.ws/transformer/transformer-basics.html
Excerpt: Then to summarise this transformer basics tutorial. A Transformer changes the voltage level (or current level) on its input winding to another value on its output winding using a magnetic field. A transformer consists of two electrically isolated coils and operates on Faraday’s principal of “mutual induction”, in which an EMF is induced in the transformers secondary coil by the magnetic flux generated by the voltages and currents flowing in the primary coil winding. [...] In other words, for a transformer there is no direct electrical connection between the two coil windings, thereby giving it the name also of an Isolation Transformer. Generally, the primary winding of a transformer is connected to the input voltage supply and converts or transforms the electrical power into a magnetic field. While the job of the secondary winding is to convert this alternating magnetic field into electrical power producing the required output voltage as shown. [...] The transformer does this by linking together two or more electrical circuits using a common oscillating magnetic circuit which is produced by the transformer itself. A transformer basics operate on the principals of “electromagnetic induction”, in the form of Mutual Induction.

## Reading notes
[1] The retrieved text says: Transformer networks have achieved great progress for computer vision tasks. Transformer-in-Transformer (TNT) architecture utilizes inner transformer and outer transformer to extract both local and global representations.
[2] The retrieved text says: Face clustering is a useful tool for applications like automatic face annotation and retrieval. The main challenge is that it is difficult to cluster images from the same identity with different face poses, occlusions, and image quality.
[3] The retrieved text says: Self-attention mechanism is the key of the Transformer but often criticized for its computation demands. Previous token pruning works motivate their methods from the view of computation redundancy but still need to load the full network and require same memory costs.
[4] The retrieved text says: Music relies heavily on repetition to build structure and meaning. Self-reference occurs on multiple timescales, from motifs to phrases to reusing of entire sections of music, such as in pieces with ABA structure.
[5] The retrieved text says: An often overlooked factor of robot manipulation performance is the embodiment of the robot itself. Motivated by this problem, we study motion-conditioned robot co-design, where the goal is to generate complete robot designs that track target end-effector trajectories (from human demonstrations) while optimizing user-defined rewards.
[6] The retrieved text says: A transformer is an electrical device that transfers energy from one electric circuit to another using the process of electromagnetic induction. The main purpose of an electrical transformer is to adjust the voltage levels up or down between two circuits without changing the frequency, which makes controlling and delivering power much easier and more energy-friendly.
[7] The retrieved text says: A transformer is an electrical device that uses electromagnetic induction to [0:32] change the voltage of an alternating current AC without changing its frequency. It's important [0:37] to note that transformers do not work for direct current DC applications.
[8] The retrieved text says: From Wikipedia, the free encyclopedia Device to couple energy between circuits This article is about the electrical component. For other uses, see Transformer (disambiguation) "Transformer (disambiguation)").
[9] The retrieved text says: Transformers are a very recent family of architectures that were originally introduced in the field of natural language processing (NLP) in 2017, as an approach to process and understand human language. Since then, they have revolutionized not only NLP but also other domains such as image processing and multi-modal generative AI.
[10] The retrieved text says: Then to summarise this transformer basics tutorial. A Transformer changes the voltage level (or current level) on its input winding to another value on its output winding using a magnetic field.

## Fallthrough
These notes stay inside the excerpts. They do not describe methods, samples, or results that the excerpts omit.

[^1]: Several records may be abstracts or search snippets. Depth is limited to that text.