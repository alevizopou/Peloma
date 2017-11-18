from __future__ import division
import collections
import statistics
from scipy import spatial
from article_profile import ArticleInterface


class UserInterface(object):
    def __init__(self, connection=None):
        self.connection = connection
        self.art_profile = ArticleInterface()

    # -------------------------------------------------------------------------------------------------
    def query(self, query):
        return self.connection.cursor.execute(query)

    # -------------------------------------------------------------------------------------------------
    def get_user(self):
        self.query('SELECT userName FROM users')
        users = self.connection.cursor.fetchall()
        return users

    # -------------------------------------------------------------------------------------------------
    def show_articles(self):
        self.query('SELECT category_id, id FROM article INNER JOIN article_tags ON '
                   'article.id=article_tags.article_id')
        articles = self.connection.cursor.fetchall()

        category_id = []
        for art in articles:
            if art[0] not in category_id:
                category_id.append(art[0])

        big_zip = []
        for cat_id in category_id:
            self.query("SELECT id, title FROM article INNER JOIN article_tags ON article.id=article_tags.article_id "
                       "WHERE article_tags.category_id = '%s'" % cat_id)
            results = self.connection.cursor.fetchall()

            article_list = [item[0] for item in results]
            title_list = [item[1] for item in results]
            big_zip.append(list(zip(article_list, title_list)))
        return category_id, big_zip

    def old_view_articles(self, final_list):
        articles = []
        for article_id in final_list:
            self.query("SELECT id, title FROM article WHERE id = '%s'" % article_id)
            article = self.connection.cursor.fetchone()
            articles.append(article)
        return articles

    # -------------------------------------------------------------------------------------------------
    def view_articles(self, final_list_of_lists):
        # final_list_of_lists = [[34, 39], [83, 92, 89, 87], [119, 117, 118]]

        bigger_list = []
        for item_list in final_list_of_lists:
            small_list = []
            for article_id in item_list:
                self.query("SELECT category_id, id, title FROM article INNER JOIN article_tags ON "
                           "article.id=article_tags.article_id WHERE id = '%s'" % article_id)
                results = self.connection.cursor.fetchall()

                id_list = [item[1] for item in results]
                title_list = [item[2] for item in results]
                small_list.append(list(zip(id_list, title_list)))
                small_flatlist = [item for slist in small_list for item in slist]
            bigger_list.append(small_flatlist)

        return bigger_list

    # -------------------------------------------------------------------------------------------------
    def create_user(self, uname):
        self.query('SELECT MAX(userId) from users')
        maxid = self.connection.cursor.fetchone()
        # print "Auto Increment ID: %s" % cur.lastrowid
        self.connection.cursor.execute('INSERT INTO users (userId, userName) VALUES (%s, %s)', (maxid[0] + 1, uname))
        self.connection.connection.commit()
        return "Done"

    # -------------------------------------------------------------------------------------------------
    def insert_articles(self, article_id, uname):
        # COALESCE(MAX(id), 0): get the first non-null thing from the list, so if your max is null, it'll give you 0
        self.connection.cursor.execute('SELECT COALESCE(MAX(id), 0) FROM reading_history')
        (maxid,) = self.connection.cursor.fetchone()

        self.connection.cursor.execute('INSERT INTO reading_history(id, user_name, article_id) VALUES (%s, %s, %s)',
                                       (maxid + 1, uname, article_id))
        self.connection.connection.commit()
        return "Done"

    # -------------------------------------------------------------------------------------------------
    def view_text(self, article_id):
        self.query("SELECT id, title, body FROM article INNER JOIN article_text ON article.id=article_text.article_id "
                   "WHERE article.id = '%s'" % article_id)
        (article,) = self.connection.cursor.fetchall()
        self.connection.connection.commit()
        return article

    # -------------------------------------------------------------------------------------------------
    def view_history(self, uname):
        self.query("SELECT article.id, title, reading_history.article_id FROM article INNER JOIN reading_history "
                   "ON article.id=reading_history.article_id WHERE reading_history.user_name = '%s'" % uname)
        articles = self.connection.cursor.fetchall()
        return articles

    # -------------------------------------------------------------------------------------------------
    def user_history(self, uname):
        self.query("SELECT article_id FROM reading_history WHERE reading_history.user_name = '%s'" % uname)
        articles_id = self.connection.cursor.fetchall()
        return articles_id

    # -------------------------------------------------------------------------------------------------
    def user_unique_history(self, uname):
        self.query("SELECT DISTINCT(article_id) FROM reading_history WHERE reading_history.user_name = '%s'"
                   "ORDER BY article_id ASC" % uname)
        articles_id = self.connection.cursor.fetchall()
        return articles_id

    # -------------------------------------------------------------------------------------------------
    # to which cluster each article belongs
    def user_unique_history_cluster(self, uname):
        self.query("SELECT DISTINCT(clusterId) FROM group_lemmas INNER JOIN reading_history ON "
                   "group_lemmas.articleId=reading_history.article_id WHERE reading_history.user_name = '%s' "
                   "ORDER BY clusterId ASC" % uname)
        clusters_id = self.connection.cursor.fetchall()

        for (cluster_id,) in clusters_id:
            self.query("SELECT COUNT(DISTINCT(reading_history.article_id)) FROM reading_history "
                       "INNER JOIN article_tags ON "
                       "reading_history.article_id=article_tags.article_id WHERE article_tags.category_id = '%s' "
                       "AND reading_history.user_name = '%s' ORDER BY reading_history.article_id ASC"
                       % (cluster_id, uname))
            (article_id,) = self.connection.cursor.fetchone()
            print("Accessed cluster #%s: %s articles read in this cluster" % (cluster_id, article_id))
        return

    # -------------------------------------------------------------------------------------------------
    def user_profile_construction(self, uname):
        topics, diction = self.topics_of_accessed_articles(uname)
        full_vocabulary = self.create_complete_topic_vocabulary(topics)
        similar_users = self.compute_user_similarity(uname)
        entities_list = self.named_entities_of_accessed_articles(uname)

        user_weight = self.compute_user_topics_weight(full_vocabulary, diction)

        return user_weight, full_vocabulary

    # ##############################################################################
    # ####### 5.1 topic distribution of given user's accessed articles (LDA) #######
    # ##############################################################################

    # topic distribution of user's accessed articles (LDA)
    def lemmas_of_accessed_articles(self, uname):
        self.query("SELECT * FROM article_text a INNER JOIN reading_history b ON a.article_id = b.article_id WHERE "
                   "b.user_name = '%s'" % uname)

        listofaccessedlemmas = []
        accessed_articles_id = []
        user_topic_words = []
        diction = []

        # LOOP FOR EVERY ACCESSED ARTICLE
        for row in self.connection.cursor:
            # keep only unique article ids (in case an article is read twice)
            if row[0] not in accessed_articles_id:
                accessed_articles_id.append(row[0])
                # A list of lists containing each accessed_article's lemmas
                listofaccessedlemmas.append(self.connection.ldarun.get_article_lemmas(row))

        # LDA model of session_user's accessed_articles
        user_tup = self.connection.ldarun.print_model_per_article(self.connection.tp.lda_function(listofaccessedlemmas))
        user_topic_list = [item[0] for item in user_tup]
        user_weight_list = [item[1] for item in user_tup]

        diction.append(dict(zip(user_topic_list, user_weight_list)))

        # Create user's topic vocabulary
        user_topic_words.append(user_tup)
        topic_list = [item[0] for sublist in user_topic_words for item in sublist]
        topics = list(collections.OrderedDict.fromkeys(topic_list))

        # print("User's topic vocabulary:", topics, len(topics))

        return topics, diction

    # -------------------------------------------------------------------------------------------------
    def topics_of_accessed_articles(self, uname):
        user_topic_lists = []
        user_topic_words = []
        diction = []

        # ids of UNIQUE accessed articles (in case an article is read twice)
        accessed_ids = self.user_unique_history(uname)
        sessionuser_article_ids = [art[0] for art in accessed_ids]
        print("%s's reading history:" % uname, sessionuser_article_ids)

        for art_id in sessionuser_article_ids:
            self.query("SELECT topicName FROM article_topics WHERE articleId= '%s' " % art_id)
            # A list of lists containing each accessed_article's topics
            topic_list = [row[0] for row in self.connection.cursor]
            user_topic_lists.append(topic_list)
        # print(user_topic_lists, len(user_topic_lists))

        # LDA model of session_user's accessed_articles
        user_tup = self.connection.ldarun.print_model_per_article(self.connection.tp.lda_function(user_topic_lists))

        user_topic_list = [item[0] for item in user_tup]
        user_weight_list = [item[1] for item in user_tup]

        diction.append(dict(zip(user_topic_list, user_weight_list)))

        # Create user's topic vocabulary
        user_topic_words.append(user_tup)
        topic_list = [item[0] for sublist in user_topic_words for item in sublist]
        topics = list(collections.OrderedDict.fromkeys(topic_list))

        return topics, diction

    # -------------------------------------------------------------------------------------------------
    def create_complete_topic_vocabulary(self, topic_l):
        with open("topics/topic_vocabulary.txt", "r+") as file:
            full_vocabulary = []
            all_lines = set(file)

            for line in all_lines:
                line = line.strip()
                full_vocabulary.append(line)

            for t in topic_l:
                if (t + '\n') not in all_lines:
                    file.write("{0}\n".format(t))
                    full_vocabulary.append(t)

            return full_vocabulary

    # ##############################################################################
    # ##### 5.2 List of users with similar access patterns with the given user #####
    # ##############################################################################

    # calculate similarity with other users
    def compute_user_similarity(self, uname):

        similarity_matrix = []
        threshold = 0.2

        # session_user's history
        results = self.user_history(uname)
        sessionuser_article_ids = [art[0] for art in results]
        # print("%s's reading history:" % uname, sessionuser_article_ids)

        results = self.get_user()
        users = [u[0] for u in results]
        others = [user for user in users if user != uname]
        similar_users = []

        # calculate pairwise user similarities
        for user in others:
            results = self.user_history(user)
            user_article_ids = [art[0] for art in results]
            similarity = self.jaccard_similarity(sessionuser_article_ids, user_article_ids)
            similarity_matrix.append(similarity)

            if similarity >= threshold:
                self.store_similar_users(uname, user)
                similar_users.append(user)
        print("List of similar users:", similar_users)
        # print("List of similarities with other users (threshold = 0.3):", similarity_matrix)

        return similar_users

    # ####################################################################################
    # #### 5.3 List of named entities extracted from the given user's reading history ####
    # ####################################################################################

    # user's named entities
    def named_entities_of_accessed_articles(self, uname):
        articles_id = self.user_history(uname)
        entities_list = []
        entities_seen = []

        for art_id in articles_id:
            self.query("SELECT entity_name FROM named_entities WHERE article_id = '%s'" % art_id)
            for row in self.connection.cursor:
                if row[0] not in entities_seen:
                    entities_seen.append(row[0])
                    entities_list.append(row[0])
        # print("%s's entities list:" % uname, entities_list, len(entities_list))
        return entities_list

    # -------------------------------------------------------------------------------------------------
    # returns the jaccard similarity between two lists
    def jaccard_similarity(self, x, y):
        intersection = len(set.intersection(*[set(x), set(y)]))
        union = len(set.union(*[set(x), set(y)]))
        return intersection/float(union)

    # -------------------------------------------------------------------------------------------------
    def compute_user_topics_weight(self, full_voc, diction):
        user_weight = [dic[i] if i in dic else 0 for dic in diction for i in full_voc]
        # print(user_weight, len(user_weight))

        return user_weight

    # ###################################################################################
    # ########################## 6.1a User - Cluster Similarity #########################
    # ###################################################################################

    # calculate similarity between topic distributions of each cluster and the user's reading history
    def compute_cluster_similarity(self, user_weight, full_vocab, username):
        similarity_matrix = []

        # LOOP FOR EVERY CATEGORY/CLUSTER
        for x in range(1, 8):
            cluster_weight = []
            self.query("SELECT topicName, weight FROM cluster_topics WHERE clusterId = (%x)" % x)
            t_name = [row[0] for row in self.connection.cursor]
            # print(t_name, len(t_name))

            f = open("topics/cluster_topics.txt", 'r')
            answer = {}
            for line in f:
                k, v, i = line.strip().split(',')
                answer[k.strip()] = v.strip()
            f.close()

            # c_w = [dic[word] if word in t_name else 0 for word in full_vocab]
            # print("c_w:", c_w, len(c_w))
            for word in full_vocab:
                if word in t_name:
                    cluster_weight.append(float(answer[word]))
                else:
                    cluster_weight.append(0)
            # print("Cluster #%x:" % x, cl, len(cl))
            # print("\n")

            similarity = 1 - spatial.distance.cosine(cluster_weight, user_weight)
            similarity_matrix.append(similarity)
        print("%s's similarity with each cluster:" % username, similarity_matrix)

        return similarity_matrix

    # -------------------------------------------------------------------------------------------------
    def articles_inside_selected_cluster(self, selected_cluster_id):

        self.connection.cursor.execute("SELECT article_id FROM article_tags WHERE category_id = (%x)"
                                       % selected_cluster_id)
        cluster_articles = [row[0] for row in self.connection.cursor]

        return cluster_articles

    # -------------------------------------------------------------------------------------------------
    def find_similar_clusters(self, user_weight, full_vocab, accessed_ids, username):
        clusters_ids = []
        cluster_ids_and_weights = {}
        # {3: 0.1, 4: 0.2, 6: 0.5}
        budget_dict = {}

        similarity_matrix = self.compute_cluster_similarity(user_weight, full_vocab, username)

        # dynamic_threshold: median of all similarity scores with respect to a specific user's profile
        dynamic_threshold = statistics.median(similarity_matrix)
        print("Threshold:", dynamic_threshold)
        print("\n")

        insert_query = 'INSERT INTO similar_clusters(cluster_id, cluster_weight) VALUES(%s, %s)'
        # we choose the clusters with the similarity greater than the dynamic threshold
        for index, sim in enumerate(similarity_matrix):
            if sim > dynamic_threshold:
                index += 1
                # --- Cluster 1: [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
                selected_cluster_articles = self.articles_inside_selected_cluster(index)

                var = any(i in selected_cluster_articles for i in accessed_ids)
                if not var:  # don't choose this category. Not this type of articles in user's reading history
                    print("nothing in common!")
                    continue
                else:  # at least one article from this category in user's reading history
                    clusters_ids.append(index)
                self.connection.cursor.execute(insert_query, (index, float(sim)))
                cluster_ids_and_weights[index] = sim
        self.connection.connection.commit()

        print("Selected clusters:", clusters_ids)
        print("Similarity with each selected cluster:", cluster_ids_and_weights)

        return clusters_ids, cluster_ids_and_weights

    # -------------------------------------------------------------------------------------------------
    def dictionary_with_budget_per_cluster(self, cluster_ids_and_weights, budget):
        # budget: maximum number of recommended items in each news group
        # budget = 4

        for k in sorted(cluster_ids_and_weights, key=cluster_ids_and_weights.get, reverse=True):
            cluster_ids_and_weights[k] = budget
            budget -= 1
        # dictionary with the budget for every selected cluster/group
        print(cluster_ids_and_weights)  # {3: 3, 4: 5, 6: 4}

        return cluster_ids_and_weights

    # ###################################################################################
    # ########################## 6.1b User - Group Similarity ###########################
    # ###################################################################################

    def find_similar_groups(self, user_weight, full_vocab, clusters_ids, accessed_ids, username):

        # similar_groups = self.compute_group_similarity(user_weight, full_vocab, clusters_ids)
        similar_groups = []

        # FOR EVERY SIMILAR CLUSTER
        for cl_id in clusters_ids:
            self.query("SELECT DISTINCT groupId FROM group_topics WHERE clusterId = (%x)" % cl_id)
            group_ids = [row[0] for row in self.connection.cursor]
            group_similarities_matrix = []

            # LOOP FOR EVERY GROUP IN THE CLUSTER
            for g_id in group_ids:
                group_weight = []

                self.query("SELECT topicName, weight FROM group_topics WHERE groupId = (%x) "
                           "AND clusterId = (%x)" % (g_id, cl_id))
                t_name = [row[0] for row in self.connection.cursor]
                # print("Topics of group %s of cluster %s:" % (g_id, cl_id), t_name)

                f = open("topics/article_topics.txt", 'r')
                answerdic = {}
                for line in f:
                    k, v, i = line.strip().split(',')
                    answerdic[k.strip()] = v.strip()
                f.close()

                for word in full_vocab:
                    if word in t_name:
                        group_weight.append(float(answerdic[word]))
                    else:
                        group_weight.append(0)

                similarity = 1 - spatial.distance.cosine(group_weight, user_weight)
                # print("%s's similarity with group %s of selected cluster %s:" % (username, g_id, cl_id), similarity)
                group_similarities_matrix.append(similarity)
            print("\n")
            print("Similarity with each group in the selected cluster #%s:" % cl_id, group_similarities_matrix)

            # 3 k-means groups
            best_group = group_similarities_matrix.index(sorted(group_similarities_matrix, reverse=True)[0])
            second_best_group = group_similarities_matrix.index(sorted(group_similarities_matrix, reverse=True)[1])
            third_best_group = group_similarities_matrix.index(sorted(group_similarities_matrix, reverse=True)[2])
            print("Best group:", best_group)
            print("Second best group:", second_best_group)
            print("Third best group:", third_best_group)
            # ______________________________________________________________________________________
            print("Selected group id:", group_similarities_matrix.index(max(group_similarities_matrix)))

            # articles inside selected group  e.g. [61, 62, 63, 67]
            selected_bestgroup_articles = self.articles_inside_selected_group(cl_id, best_group)
            selected_secondbestgroup_articles = self.articles_inside_selected_group(cl_id, second_best_group)
            selected_thirdbestgroup_articles = self.articles_inside_selected_group(cl_id, third_best_group)

            # check if articles in selected group are all already read
            # In this case, we must select the next most similar group
            # so that we won't miss the whole category from the suggested list

            if set(selected_bestgroup_articles) == set(accessed_ids):
                print("Pure match! All read! Let's go to the next more similar group.")
                # similar_groups.append(second_best_group)
                if set(selected_secondbestgroup_articles) < set(accessed_ids):
                    print("Pure match with the second one! All read! Let's go to the third more similar group.")
                    similar_groups.append(third_best_group)
                else:
                    # append second best group
                    similar_groups.append(second_best_group)
            elif set(selected_bestgroup_articles) < set(accessed_ids):
                if set(selected_secondbestgroup_articles) < set(accessed_ids):
                    print("Pure match with the second one! All read! Let's go to the third more similar group.")
                    similar_groups.append(third_best_group)
                else:
                    # append second best group
                    similar_groups.append(second_best_group)
            else:
                similar_groups.append(best_group)

        print("\n")
        print("Selected groups (one for each of the selected clusters):", similar_groups)

        return similar_groups

    # -------------------------------------------------------------------------------------------------
    def articles_inside_selected_groups(self, selected_clusters_ids, selected_groups_ids):
        # list of lists
        selected_groups_articles = []
        i = j = 0
        print("Articles inside selected groups:")
        for selected_groups_ids[j] in selected_groups_ids:
            self.connection.cursor.execute("SELECT DISTINCT(articleId) FROM group_lemmas "
                                           "WHERE groupId = (%x) AND clusterId = (%x)"
                                           % (selected_groups_ids[j], selected_clusters_ids[i]))
            group_articles = [row[0] for row in self.connection.cursor]
            selected_groups_articles.append(group_articles)
            # print("--- Cluster %s Group %s:" % (selected_clusters_ids[i], selected_groups_ids[i]), group_articles)
            # print(group_articles)
            j += 1
            i += 1
        print("\n")

        # [[42, 43], [68, 83, 84], [98, 100, 106]]
        return selected_groups_articles

    # -------------------------------------------------------------------------------------------------
    def articles_inside_selected_group(self, selected_cluster_id, selected_group_id):

        self.connection.cursor.execute("SELECT DISTINCT(articleId) FROM group_lemmas "
                                       "WHERE groupId = (%x) AND clusterId = (%x)"
                                       % (selected_group_id, selected_cluster_id))
        group_articles = [row[0] for row in self.connection.cursor]
        # print("--- Cluster %s Group %s:" % (selected_cluster_id, selected_group_id), group_articles)

        # [68, 83, 84]
        return group_articles

    # -------------------------------------------------------------------------------------------------
    def unread_user_articles(self, selected_clusters_ids, selected_groups_ids, selected_groups_articles, accessed_ids):
        # FOR EACH SELECTED GROUP
        i = j = 0
        rest_ids_per_group = []
        for group_id in selected_groups_ids:
            # rest of group's articles (excluding those already read)
            rest_ids = [x for x in selected_groups_articles[j] if x not in accessed_ids]
            rest_ids_per_group.append(rest_ids)
            # print("Cluster #%s - Unread group #%s articles:" % (selected_clusters_ids[i], group_id), rest_ids)
            j += 1
            i += 1
        print("Unread articles from each selected group:", rest_ids_per_group)

        return rest_ids_per_group

    def store_similar_users(self, uname, otherusername):
        self.connection.cursor.execute("SELECT userId FROM users WHERE userName='%s'" % uname)
        (user_id,) = self.connection.cursor.fetchone()

        self.connection.cursor.execute("SELECT userId FROM users WHERE userName='%s'" % otherusername)
        (otheruser_id,) = self.connection.cursor.fetchone()

        self.connection.cursor.execute("INSERT IGNORE INTO similar_users(userId, similaruserId, similaruserName) "
                                       "VALUES (%s, %s, %s)", (user_id, otheruser_id, otherusername))
        self.connection.connection.commit()
