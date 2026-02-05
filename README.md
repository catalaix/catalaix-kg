# Catalaix Knowledge Graph

This repository contains the demo for the Catalaix knowledge graph (KG):

1. the [reactions](curation/reactions.tsv) including the substrates, products,
   and literature references describing the reactions
2. the [reactions hierarchy](curation/reaction_hierarchy.tsv) which connects
   reactions with different levels of abstraction
3. a chemical ontology, including hierarchical categorization of molecules by
   structure and role (based on ChEBI) such as plasticizers and dyes
4. the [conditions](curation/conditions.tsv) including experimental information
   like the catalyst/microbe, byproducts, conditions and provenance information
   like the group that ran the reactions and literature references where the
   conditions were used
5. the [labs](curation/labs.tsv) within the consortium and their
   [members](curation/memberships.tsv)
6. literature published by labs in the consortium and important to members of
   the consortium, and an induced citation network

![](output/PET.png)


This repository constructs bibliographic knowledge graph of articles and
citations (added in [#6](https://github.com/catalaix/catalaix-kg/pull/6)).
The following is an example subgraph from the citation graph.

```mermaid
flowchart LR
	28524364["Biofunctional Microgel-Based Fertilizers for Controlled Foliar Delivery of Nutrients to Plants.
Pich, Schwaneberg (2017)"]
	26802344["Mechanism-specific and whole-organism ecotoxicity of mono-rhamnolipids.
Blank (2016)"]
	33195133["Genetic Cell-Surface Modification for Optimized Foam Fractionation.
Blank (2020)"]
	34492827["The Green toxicology approach: Insight towards the eco-toxicologically safe development of benign catalysts.
Herres-Pawlis (2021)"]
	34865895["A plea for the integration of Green Toxicology in sustainable bioeconomy strategies - Biosurfactants and microgel-based pesticide release systems as examples.
Pich, Blank, Schwaneberg (2022)"]
	30758389["Tuning a robust system: N,O zinc guanidine catalysts for the ROP of lactide.
Pich, Herres-Pawlis (2019)"]
	28779508["Highly Active N,O Zinc Guanidine Catalysts for the Ring-Opening Polymerization of Lactide.
Herres-Pawlis (2017)"]
	30811863["New Kids in Lactide Polymerization: Highly Active and Robust Iron Guanidine Complexes as Superior Catalysts.
Pich, Herres-Pawlis (2019)"]
	32974309["Integration of Genetic and Process Engineering for Optimized Rhamnolipid Production Using 
Jupke, Blank (2020)"]
	32449840["Robust Guanidine Metal Catalysts for the Ring-Opening Polymerization of Lactide under Industrially Relevant Conditions.
Herres-Pawlis (2020)"]
	34492827 --> 30811863
	34492827 --> 30758389
	34492827 --> 28779508
	34492827 --> 32449840
	34865895 --> 26802344
	34865895 --> 32974309
	34865895 --> 28524364
	34865895 --> 34492827
	32974309 --> 33195133
```
