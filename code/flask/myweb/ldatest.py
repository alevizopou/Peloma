#!/usr/bin/python
import os
from ldarunner import LDARunner
from entities_extraction import ExtractEntities

# CATEGORIES: Science/Technology, Politics, Sports, Life & Style
userhome = os.path.expanduser('~')
testdir = os.path.join(userhome, "PycharmProjects/out")
filter_file = os.path.join(userhome, "PycharmProjects/out/filtertagged.txt")
cluster_topics_file = os.path.join(userhome, "PycharmProjects/flask/myweb/topics/cluster_topics.txt")
article_topics_file = os.path.join(userhome, "PycharmProjects/flask/myweb/topics/article_topics.txt")
group_topics_file = os.path.join(userhome, "PycharmProjects/flask/myweb/topics/group_topics.txt")
group_lemmas_file = os.path.join(userhome, "PycharmProjects/flask/myweb/topics/group_lemmas.txt")
entities_file = os.path.join(userhome, "PycharmProjects/flask/myweb/entities.txt")
tokensDestination = ""
TRUE_K = 3


def run_per_article():
    runner = LDARunner()
    runner.topics_per_article()


def run_per_category():
    runner = LDARunner()
    runner.topics_per_category()


def entities_per_article():
    extraction = ExtractEntities()
    extraction.extract_named_entities()


def delete_file(file):
    if os.path.exists(file):
        os.remove(file)


def main():
    delete_file(filter_file)
    delete_file(cluster_topics_file)
    delete_file(article_topics_file)
    delete_file(group_lemmas_file)
    delete_file(group_topics_file)
    delete_file(entities_file)

    run_per_article()
    run_per_category()
    entities_per_article()


if __name__ == '__main__':
    main()
