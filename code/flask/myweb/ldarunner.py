#!/usr/bin/python
import collections
import mysql.connector
import os
from textprocessor import TextProcessor

userhome = os.path.expanduser('~')
testdir = os.path.join(userhome, "PycharmProjects/out")
tokensDestination = ""
NUM_OF_CATEGORIES = 7
NUM_WORDS = 40


class LDARunner(object):
    def __init__(self, db_host='localhost', db_user='root', db_password='root', db_database='news_db2'):
        self.host = db_host
        self.user = db_user
        self.password = db_password
        self.database = db_database
        self.connection = mysql.connector.connect(host=self.host, user=self.user, password=self.password,
                                                  database=self.database)
        self.cursor = self.connection.cursor()
        self.tp = TextProcessor()

    def query(self, query):
        return self.cursor.execute(query)

    def get_text_processor(self):
        return self.tp

    # each article's tokens, tagging, lemmas --> to file
    def get_article_lemmas(self, row):

        # print("-- Article # ", rowcount)
        tokens = self.tp.get_tokens(row[1])
        tokens = [token.lower() for token in tokens if len(token) > 2]
        stopped_tokens = self.tp.remove_stopwords(tokens)

        create_path = lambda x, y: os.path.join(testdir, "{}{}.txt".format(x, y))

        tokens_destination = create_path("tokens", row[0])
        tagger_destination = create_path("tagged", row[0])
        filtertagger_destination = create_path("filtertagged", row[0])
        # filtertagger_destination = os.path.join(testdir, "filtertagged" + '.txt')

        self.tp.tokens_to_file(stopped_tokens, tokens_destination)
        self.tp.tag_tokens(tokens_destination, tagger_destination)
        # Lemmas of each article
        keys = self.tp.filter_tagger_output(tagger_destination, filtertagger_destination)
        return keys

    def topics_per_article(self):

        article_topic_words = []
        dicts = []

        self.query('SELECT * FROM article_text a INNER JOIN article b on a.article_id = b.id')

        # LOOP FOR EVERY ARTICLE
        for row in self.cursor:
            print("------------------------")
            print("Article #", row[0], "- Title:", row[3])
            print("------------------------")

            articletext = []
            listofarticlelemmas = []

            articletext.append(row[1])

            # write each article's text in a file
            create_path = lambda x, y: os.path.join(testdir, "{}{}.txt".format(x, y))
            article_text_destination = create_path("article", row[0])

            with open(article_text_destination, 'w') as f:
                f.write(row[1])

            # tokenize/tag/lemmatize each article
            listofarticlelemmas.append(self.get_article_lemmas(row))

            # ###################################
            # LDA model PER ARTICLE
            # ###################################

            # EDO EINAI H ALLAGH ********************************************
            if row[0] <= 68:
                article_topic_list, article_weight_list = self.lda_per_article(listofarticlelemmas)
            elif row[0] >= 69:
                article_topic_list, article_weight_list = self.lda_per_reuters_article(listofarticlelemmas)
            else:
                print("EP!")

            # article_topic_list, article_weight_list = self.lda_per_article(listofarticlelemmas)
            dicts.append(dict(zip(article_topic_list, article_weight_list)))

            # append each article's topics to file
            self.article_topics_to_file(article_topic_list, article_weight_list, row[0])

            # Create a topic vocabulary of all articles
            article_topic_words.append(article_topic_list)

        topic_list = [item for sublist in article_topic_words for item in sublist]
        article_topics = list(collections.OrderedDict.fromkeys(topic_list))

        # save each article's topics to database
        self.article_topics_to_database()

        print("\n")
        print("Articles' topic vocabulary:", article_topics, len(article_topics))
        self.article_vocabulary_to_file(article_topics)
        return article_topics

    def topics_per_category(self):
        """ ARTICLE TEXT PER CATEGORY """

        topic_words = []
        dicts = []

        # LOOP FOR EVERY CATEGORY/CLUSTER
        for x in range(1, NUM_OF_CATEGORIES+1):
            self.query('SELECT * FROM article_text a INNER JOIN article_tags b on a.article_id = b.article_id '
                       '    INNER JOIN category c on b.category_id = c.category_id WHERE b.category_id = (%x)' % x)
            results = self.cursor.fetchall()

            print("\n")
            print("------------------------")
            print("Processing: Category #", x, "-", results[0][5])
            print("------------------------")

            categorytext = []
            articleidlist = []
            listofcategorylemmas = []
            # listofgroupslemmas = []
            cluster_id = x

            # loop for every category's article
            for row in results:
                articleidlist.append(row[0])
                categorytext.append(row[1])
                # tokenize/tag/lemmatize each category's articles
                # A list of lists containing each category's articles' lemmas
                listofcategorylemmas.append(self.get_article_lemmas(row))

            # ######################################################################
            # K-MEANS PER CATEGORY(CLUSTER) for grouping articles inside the cluster
            # ######################################################################
            groups = self.kmeans_grouping(categorytext, articleidlist, cluster_id)

            # ###################################
            # LDA model PER CATEGORY
            # ###################################
            cluster_topic_list, cluster_weight_list = self.lda_per_category(listofcategorylemmas)
            dicts.append(dict(zip(cluster_topic_list, cluster_weight_list)))

            # append each cluster's topics to file
            self.cluster_topics_to_file(cluster_topic_list, cluster_weight_list, cluster_id)

            # Create a topic vocabulary of all categories/clusters
            topic_words.append(cluster_topic_list)
            topic_list = [item for sublist in topic_words for item in sublist]
            topics = list(collections.OrderedDict.fromkeys(topic_list))

            # ################################################################
            # LDA model PER GROUP (INSIDE EACH CLUSTER/CATEGORY)
            # ################################################################
            for group_id in groups:
                listofgrouplemmas = []

                g_lemmas = self.lemmas_per_group(cluster_id, group_id)
                # A list of lists containing each category's groups' lemmas
                listofgrouplemmas.append(g_lemmas)

                if cluster_id <= 4:
                    group_topic_list, group_weight_list = self.lda_per_group(listofgrouplemmas)
                else:
                    group_topic_list, group_weight_list = self.lda_per_reuters_group(listofgrouplemmas)

                dicts.append(dict(zip(group_topic_list, group_weight_list)))

                print("Group %d of category #%d topic list :" % (group_id, cluster_id), group_topic_list)
                print("\n")

                self.group_topics_to_file(group_topic_list, group_weight_list, group_id, cluster_id)

        self.group_topics_to_database()
        self.cluster_topics_to_database()  # save each cluster's topics to database
        print("\n")
        self.cluster_vocabulary_to_file(topics)  # Clusters' topic vocabulary

        return topics

    def lemmas_per_group(self, cluster_id, group_id):

        # loop for every group's article
        self.query("SELECT topicName, weight FROM group_lemmas WHERE groupId = '%s' AND clusterId = '%s' "
                   % (group_id, cluster_id))
        list_of_group_lemmas = [row[0] for row in self.cursor]

        return list_of_group_lemmas

    def lda_per_article(self, listofarticlelemmas):
        article_tup = self.print_model_per_article(self.tp.lda_function(listofarticlelemmas))
        article_topic_list = [item[0] for item in article_tup]
        article_weight_list = [item[1] for item in article_tup]

        return article_topic_list, article_weight_list

    def lda_per_reuters_article(self, listofarticlelemmas):
        article_tup = self.print_model_per_reuters_article(self.tp.lda_function(listofarticlelemmas))
        article_topic_list = [item[0] for item in article_tup]
        article_weight_list = [item[1] for item in article_tup]

        return article_topic_list, article_weight_list

    def lda_per_group(self, listofgrouplemmas):
        tup = self.print_model_per_group(self.tp.lda_function(listofgrouplemmas))
        group_topic_list = [item[0] for item in tup]
        group_weight_list = [item[1] for item in tup]

        return group_topic_list, group_weight_list

    def lda_per_reuters_group(self, listofgrouplemmas):
        tup = self.print_model_per_reuters_group(self.tp.lda_function(listofgrouplemmas))
        group_topic_list = [item[0] for item in tup]
        group_weight_list = [item[1] for item in tup]

        return group_topic_list, group_weight_list

    def kmeans_grouping(self, categorytext, articleidlist, cluster_id):
        labels = self.tp.kmeans_function(categorytext)

        groups = {}
        n = 0
        for item in labels:
            if item in groups:
                groups[item].append(articleidlist[n])
            else:
                groups[item] = [articleidlist[n]]
            n += 1

        # group lemmas
        for group_id in groups:
            print("Group %d:" % group_id)

            # art_id = article's id in this group
            for art_id in groups[group_id]:
                print(art_id)
                self.group_lemmas_to_file(art_id, group_id, cluster_id)
        self.group_lemmas_to_database()

        return groups

    def lda_per_category(self, listofcategorylemmas):
        tup = self.print_model_per_category(self.tp.lda_function(listofcategorylemmas))
        cluster_topic_list = [item[0] for item in tup]
        cluster_weight_list = [item[1] for item in tup]

        return cluster_topic_list, cluster_weight_list

    def lda_per__reuters_category(self, listofcategorylemmas):
        tup = self.print_model_per_reuters_category(self.tp.lda_function(listofcategorylemmas))
        cluster_topic_list = [item[0] for item in tup]
        cluster_weight_list = [item[1] for item in tup]

        return cluster_topic_list, cluster_weight_list

    def print_model_per_article(self, model):

        # print("LDA model:")
        # Each topic has a set of words that defines it, along with a certain probability
        # Within each topic are the NUM_WORDS most probable words to appear in that topic

        topics_matrix = model.show_topics(formatted=False, num_words=140)
        # print([tup for x in topics_matrix for tup in x[1]])
        # print("\n")

        return [tup for x in topics_matrix for tup in x[1]]

    def print_model_per_reuters_article(self, model):

        # print("LDA model:")
        # Each topic has a set of words that defines it, along with a certain probability
        # Within each topic are the NUM_WORDS most probable words to appear in that topic

        topics_matrix = model.show_topics(formatted=False, num_words=NUM_WORDS)
        # print([tup for x in topics_matrix for tup in x[1]])
        # print("\n")

        return [tup for x in topics_matrix for tup in x[1]]

    def print_model_per_group(self, model):

        # print("LDA model:")
        # Each topic has a set of words that defines it, along with a certain probability
        # Within each topic are the NUM_WORDS most probable words to appear in that topic

        topics_matrix = model.show_topics(formatted=False, num_words=240)
        # print([tup for x in topics_matrix for tup in x[1]])
        # print("\n")

        return [tup for x in topics_matrix for tup in x[1]]

    def print_model_per_reuters_group(self, model):

        # print("LDA model:")
        # Each topic has a set of words that defines it, along with a certain probability
        # Within each topic are the NUM_WORDS most probable words to appear in that topic

        topics_matrix = model.show_topics(formatted=False, num_words=80)
        # print([tup for x in topics_matrix for tup in x[1]])
        # print("\n")

        return [tup for x in topics_matrix for tup in x[1]]

    def print_model_per_category(self, model):

        # print("LDA model:")
        # Each topic has a set of words that defines it, along with a certain probability
        # Within each topic are the NUM_WORDS most probable words to appear in that topic

        topics_matrix = model.show_topics(formatted=False, num_words=700)
        # print([tup for x in topics_matrix for tup in x[1]])
        # print("\n")

        return [tup for x in topics_matrix for tup in x[1]]

    def print_model_per_reuters_category(self, model):

        # print("LDA model:")
        # Each topic has a set of words that defines it, along with a certain probability
        # Within each topic are the NUM_WORDS most probable words to appear in that topic

        topics_matrix = model.show_topics(formatted=False, num_words=400)
        # print([tup for x in topics_matrix for tup in x[1]])
        # print("\n")

        return [tup for x in topics_matrix for tup in x[1]]

    # 40 topics per article
    def article_topics_to_file(self, topic_list, weight_list, a_id):
        # append each cluster's topics to file
        with open("topics/article_topics.txt", "a") as f:
            for (t, w) in zip(topic_list, weight_list):
                f.write("{0}, {1}, {2}\n".format(t, w, a_id))

    def article_vocabulary_to_file(self, art_topic_list):
        # write each cluster's topics to file (remove duplicates)
        with open("topics/topic_vocabulary.txt", "w") as f:
            for t in art_topic_list:
                f.write("{0}\n".format(t))

    # cluster_topics.txt: 40 words with their weight for each cluster
    def cluster_topics_to_file(self, topic_list, weight_list, c_id):
        # append each cluster's topics to file
        with open("topics/cluster_topics.txt", "a") as f:
            for (t, w) in zip(topic_list, weight_list):
                f.write("{0}, {1}, {2}\n".format(t, w, c_id))

    def cluster_vocabulary_to_file(self, topic_list):
        # append each article's topics to file
        with open("topics/topic_vocabulary.txt", "r+") as f:
            all_lines = set(f)

            for t in topic_list:
                if (t + '\n') not in all_lines:
                    f.write("{0}\n".format(t))

    def group_lemmas_to_file(self, article_id, group_id, cluster_id):
        # append each group's topics to file
        with open("topics/article_topics.txt", "r") as f:
            with open("topics/group_lemmas.txt", "a") as f1:
                for line in f:
                    parts = line.split(",")
                    # if article in group, write all its topics to group_lemmas.txt file
                    # along with the group and cluster infos for this article
                    if int(parts[2]) == article_id:
                        output = "%s, %s, %s" % (line.strip(), group_id, cluster_id)
                        f1.write("".join(output + "\n"))

    def group_topics_to_file(self, group_topic_list, group_weight_list, g_id, cluster_id):
        # append each cluster's topics to file
        with open("topics/group_topics.txt", "a") as f:
            for (t, w) in zip(group_topic_list, group_weight_list):
                f.write("{0}, {1}, {2}, {3}\n".format(t, w, g_id, cluster_id))

    def article_topics_to_database(self):
        # save each article's topics to database
        self.query("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/flask/myweb/topics/article_topics.txt' "
                   "INTO TABLE article_topics FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' "
                   "(@col1, @col2, @col3) set topicName=@col1, weight=@col2, articleId=@col3")
        self.connection.commit()

    def cluster_topics_to_database(self):
        # save each cluster's topics to database
        self.query("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/flask/myweb/topics/cluster_topics.txt' "
                   "INTO TABLE cluster_topics FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' "
                   "(@col1, @col2, @col3) set topicName=@col1, weight=@col2, clusterId=@col3")
        self.connection.commit()

    def group_lemmas_to_database(self):
        # save each group's topics to database
        self.query("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/flask/myweb/topics/group_lemmas.txt' "
                   "INTO TABLE group_lemmas FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' "
                   "(@col1, @col2, @col3, @col4, @col5) set topicName=@col1, weight=@col2, articleId=@col3, "
                   "groupId=@col4, clusterId=@col5")
        self.connection.commit()

    def group_topics_to_database(self):
        # save each group's topics to database
        self.query("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/flask/myweb/topics/group_topics.txt' "
                   "INTO TABLE group_topics FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' "
                   "(@col1,@col2, @col3, @col4) set topicName=@col1, weight=@col2, groupId=@col3, clusterId=@col4")
        self.connection.commit()

