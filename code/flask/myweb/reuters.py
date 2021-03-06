import os
from nltk.corpus import reuters

reuters_file = "/home/afroditi/PycharmProjects/flask/myweb/reuters.txt"


def collection_stats():
    # List of documents
    documents = reuters.fileids()
    print(str(len(documents)) + " documents")

    train_docs = list(filter(lambda doc: doc.startswith("train"), documents))
    print(str(len(train_docs)) + " total train documents")

    test_docs = list(filter(lambda doc: doc.startswith("test"), documents))
    print(str(len(test_docs)) + " total test documents")

    # List of categories
    categories = reuters.categories()
    print("Categories:", categories)
    print(str(len(categories)) + " categories")

    # Documents in a category
    category_docs = reuters.fileids("acq")

    # Words for a document
    document_id = category_docs[0]
    document_words = reuters.words(category_docs[0])
    print(document_words)
    # print(len(document_words))

    # Raw document
    # print(reuters.raw(document_id))


def raw_to_file():
    category_docs = reuters.fileids("sugar")
    # print(len(category_docs))
    # print(category_docs[0:20])
    # document_id = category_docs[0]
    for doc_id in category_docs[0:30]:
        # print(reuters.raw(doc_id))
        with open("reuters.txt", "a") as f:
            f.write(reuters.raw(doc_id))
            f.write("***********************************************************************")
    category_docs = reuters.fileids("coffee")
    for doc_id in category_docs[0:30]:
        with open("reuters.txt", "a") as f:
            f.write(reuters.raw(doc_id))
            f.write("***********************************************************************")
    category_docs = reuters.fileids("housing")
    for doc_id in category_docs[0:30]:
        with open("reuters.txt", "a") as f:
            f.write(reuters.raw(doc_id))
            f.write("***********************************************************************")


def delete_file(file):
    if os.path.exists(file):
        os.remove(file)


def main():
    train_docs = []
    test_docs = []

    for doc_id in reuters.fileids():
        if doc_id.startswith("train"):
            train_docs.append(reuters.raw(doc_id))
        else:
            test_docs.append(reuters.raw(doc_id))
    # print(train_docs)


if __name__ == '__main__':
    # main()
    # collection_stats()
    delete_file(reuters_file)
    raw_to_file()



