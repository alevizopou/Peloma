#!/usr/bin/python

import nltk
import os
from nltk.tokenize import RegexpTokenizer
from nltk.stem.porter import *
import treetaggerwrapper
from gensim import corpora, models
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans

userhome = os.path.expanduser('~')
NUM_TOPICS = 1
TRUE_K = 3


class TextProcessor(object):
    def __init__(self, language="english"):
        self.language = language
        # self.tokenizer = RegexpTokenizer("[\w’]+", flags=re.UNICODE)
        self.tokenizer = RegexpTokenizer(r'\w+|[^\w\s]|\s+', flags=re.UNICODE)
        self.stopwords = nltk.corpus.stopwords.words(self.language)
        self.stemmer = PorterStemmer()

    def remove_stopwords(self, list):
        return [word for word in list if word not in self.stopwords]

    def get_tokens(self, data):
        return self.tokenizer.tokenize(data)

    def tokens_to_file(self, tok, tokensdestination):
        # All tokens in one file -> Append
        # out = open(tokensdestination, 'a')
        out = open(tokensdestination, 'w')
        out_str = ""

        for t in tok:
            if not t[0].isalpha():
                pass
            else:
                out_str += t + "\n"
        # file contains only alphabetic tokens, free of stop words, with len(tokens) > 2
        out.write(out_str)
        out.close()

    # Use of TreeTagger and tagged tokens saved to file
    def tag_tokens(self, tokensdestination, taggerdestination):
        tagger = treetaggerwrapper.TreeTagger(TAGLANG='en')
        tags = tagger.tag_file_to(tokensdestination, taggerdestination, encoding="utf-8")

    # lemma dictionary
    def filter_tagger_output(self, taggerdestination, filtertaggerdestination):
        tagged = open(taggerdestination, 'r')
        cnt = 0
        lemma_dict = {}
        lemma_list = []
        out = open(filtertaggerdestination, 'w')
        out_str = ""

        for line in tagged:
            # remove newline '\n' and split based on tabs
            a = line.strip().split('\t')

            stem = self.stemmer.stem(a[2])
            lemma_list.append(stem)

            if stem not in lemma_dict:
                lemma_dict[stem] = 1
            else:
                lemma_dict[stem] += 1
            cnt += 1

            # out_str += a[2] + "\n"
            out_str += stem + "\n"
        out.write(out_str)
        out.close()

        return lemma_list

    def freq(self, word, tok):
        return tok.count(word)

    # remove duplicates from token list
    def remove_duplicates(self, seq):
        # order preserving
        checked = []
        for e in seq:
            if e not in checked:
                checked.append(e)
        return checked

    def term_freq(self, word, filtertok, totaltok):
        # tf: the number of times a word appears in a document, divided by the total number of words in that document
        howmanytimes = filtertok.count(word)
        tf = howmanytimes/totaltok
        return tf

    def num_docs_containing(self, word, list_of_articles):
        count = 0
        for article in list_of_articles:
            if self.freq(word, article) > 0:
                count += 1
        return count

    def tokenize_and_stem(self, text):
        # first tokenize by sentence, then by word to ensure that punctuation is caught as it's own token
        tokens = [word for sent in nltk.sent_tokenize(text) for word in nltk.word_tokenize(sent)]
        filtered_tokens = []
        # filter out any tokens not containing letters (e.g., numeric tokens, raw punctuation)
        for token in tokens:
            if re.search('[a-zA-Z]', token):
                filtered_tokens.append(token)
        stems = [self.stemmer.stem(t) for t in filtered_tokens]
        return stems

    def kmeans_function(self, listofcategoryart):
        tfidf_vectorizer = TfidfVectorizer(stop_words=self.stopwords, tokenizer=self.tokenize_and_stem,
                                           sublinear_tf=True)
        tfidf_matrix = tfidf_vectorizer.fit_transform(listofcategoryart)

        print(tfidf_matrix.shape)

        terms = tfidf_vectorizer.get_feature_names()
        # print("Terms: ", terms)

        kmeansmodel = KMeans(n_clusters=TRUE_K, init='k-means++', max_iter=100, n_init=1)

        kmeansmodel.fit(tfidf_matrix)
        # print(kmeansmodel.labels_)
        # e.g [0 0 0 0 0 0 1 1 1] = First six documents in Cluster0, rest of them in Cluster1

        # Predict the closest cluster each sample in X belongs to.
        # ClusterIndices
        labels = kmeansmodel.predict(tfidf_matrix)
        # print(labels)

        return labels

    # LDA is a probabilistic topic model that assumes documents are a mixture of topics
    # and that each word in the document is attributable to the document's topics.
    def lda_function(self, listofart):
        dictionary = corpora.Dictionary(listofart)
        # print(dictionary.token2id)  # mapping between words and their ids

        # convert tokenized documents into a document-term matrix
        corpus = [dictionary.doc2bow(article) for article in listofart]

        tfidf = models.TfidfModel(corpus, normalize=True)
        # CORPUS TF IDF ****************
        corpus_tfidf = tfidf[corpus]
        # generate LDA model
        ldamodel = models.LdaModel(corpus_tfidf, num_topics=NUM_TOPICS, id2word=dictionary, alpha='auto', passes=20)
        # corpus_lda = ldamodel[corpus_tfidf]
        return ldamodel
