# -*- coding: utf-8 -*-
"""
Building graph part
"""
import argparse
from tqdm import tqdm

import spacy
import numpy as np
from pyvis.network import Network
import networkx.algorithms.community as nx_comm

def ent_to_uri(ent: spacy.tokens.Span) -> str:
    """ From entity return DBpedia URI """
    return ent._.dbpedia_raw_result["@URI"]



def build_adjacency_matrix(docs: list[spacy.tokens.doc], vocab: dict) -> np.array:
    """
    docs: list of documents preprocessed with spacy pipeline
    vocab: keys = numbers, values = DBpedia entities

    Builds an adjacency matrix of DBpedia entities that co-occur
    in the documents
    """
    matrix = np.zeros((len(vocab), len(vocab)))
    name_to_index = {v: k for k, v in vocab.items()}

    for i in tqdm(range(len(docs))):
        doc = docs[i]
        dbpedia_entities = [ent for ent in doc.ents if ent._.dbpedia_raw_result]
        dbpedia_entities = list(set([ent_to_uri(ent) for ent in dbpedia_entities]))
        # if len(dbpedia_entities) == 1:  # only one DBpedia entity -> self co-occurrence
        #     uri =ent_to_uri(dbpedia_entities[0]) 
        #     if uri in name_to_index:
        #         index = int(name_to_index[uri])
        #         matrix[index, index] += 1
        if len(dbpedia_entities) > 1:  # at least two dbpedia entities co-occurring
            for i, uri_1 in enumerate(dbpedia_entities):
                for uri_2 in dbpedia_entities[i+1:]:
                    if uri_1 in name_to_index and uri_2 in name_to_index:
                        index_1 = int(name_to_index[uri_1])
                        index_2 = int(name_to_index[uri_2])
                        matrix[index_1, index_2] += 1
                        matrix[index_2, index_1] += 1

    return matrix


if __name__ == '__main__':
    # python src/graph.py -p ./sample_data/docs_spacy_ukraine_russia.pkl -v ./sample_data/vocab_ukraine_russia.json
    ap = argparse.ArgumentParser()
    ap.add_argument('-p', "--pkl", required=True,
                    help=".pkl file containing the spacy pipeline data in bytes format")
    ap.add_argument('-v', "--vocab", required=True,
                    help=".csv output file with main results")
    ap.add_argument('-o', '--o', required=True,
                    help="output .txt file to save the results")
    args_main = vars(ap.parse_args())

    import json
    import pickle
    import networkx as nx
    from spacy.tokens import DocBin, Span

    nlp = spacy.blank("en")
    with open(args_main["pkl"], "rb") as openfile:
        bytes_data = pickle.load(openfile)
    doc_bin = DocBin().from_bytes(bytes_data)
    DOCS = list(doc_bin.get_docs(nlp.vocab))
    # Span.set_extension("dbpedia_raw_result", default=None)

    with open(args_main["vocab"], 'r', encoding='utf-8') as openfile:
        VOCAB = json.load(openfile)
    MATRIX = build_adjacency_matrix(docs=DOCS, vocab=VOCAB)
    print(MATRIX)

    graph = nx.from_numpy_array(MATRIX)
    graph = nx.relabel_nodes(graph, {int(k): v for k, v in VOCAB.items()})
    ordered_edges = sorted(graph.edges(data=True),key= lambda x: x[2]['weight'],reverse=True)
    print([x for x in ordered_edges if x[2]["weight"] > 10])
    print(len([x for x in ordered_edges if x[2]["weight"] > 10]))

    f_log = open(args_main["output"], "w+")
    for edge in [x for x in ordered_edges]:
        f_log.write(f"{edge[0]}\t{edge[1]}\t{edge[2]['weight']}\n")
    f_log.close()


    # louvain = nx_comm.louvain_communities(graph, seed=23)

    # print(len(louvain))
    # print([len(x) for x in louvain])
    # print(graph.number_of_nodes())

    # for cluster in [x for x in louvain if len(x) > 10]:
    #     print(cluster)
    #     print("=====")
    
    # nt = Network('2000px', '2000px')
    # nt.from_nx(graph)
    # nt.repulsion(node_distance=600, spring_length=340,
    #              spring_strength=0.4)
    # nt.show("nx.html")