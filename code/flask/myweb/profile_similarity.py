from __future__ import division
from scipy import spatial
import math


class ProfileInterface(object):
    def __init__(self, connection=None, u_profile=None, a_profile=None):
        self.connection = connection
        self.user_profile = u_profile
        self.article_profile = a_profile

    # ###################################################################################
    # ################## 6.2.1 User - Article Profile Similarity ########################
    # ###################################################################################

    # evaluate how the news item cam satisfy the user's reading preference

    # cosine similarity
    def compute_user_article_content_similarity(self, uname, article_id):
        art_weight = []

        # topic distribution of user's accessed articles (LDA)
        topics, diction = self.user_profile.lemmas_of_accessed_articles(uname)

        full_vocab = self.user_profile.create_complete_topic_vocabulary(topics)

        user_weight = self.user_profile.compute_user_topics_weight(full_vocab, diction)

        self.connection.cursor.execute("SELECT topicName, weight FROM article_topics "
                                       "WHERE articleId = '%s' " % article_id)
        article_t_name = [row[0] for row in self.connection.cursor]

        f = open("topics/article_topics.txt", 'r')
        answer = {}
        for line in f:
            k, v, i = line.strip().split(',')
            answer[k.strip()] = v.strip()
        f.close()

        for word in full_vocab:
            if word in article_t_name:
                art_weight.append(float(answer[word]))
            else:
                art_weight.append(0)

        tn_tu = 1 - spatial.distance.cosine(art_weight, user_weight)

        return tn_tu

    # jaccard similarity
    def compute_user_article_pattern_similarity(self, uname, article_id):
        accessed_users = self.article_profile.get_accessed_users_by_name(article_id)
        users = self.user_profile.compute_user_similarity(uname)

        pn_pu = self.user_profile.jaccard_similarity(accessed_users, users)

        return pn_pu

    # jaccard similarity
    def compute_user_article_entities_similarity(self, uname, article_id):
        user_entities = self.user_profile.named_entities_of_accessed_articles(uname)
        art_entities = self.article_profile.get_article_named_entities(article_id)

        en_eu = self.user_profile.jaccard_similarity(user_entities, art_entities)

        return en_eu

    def compute_user_article_similarity(self, uname, article_id):
        a = b = c = 1
        sim_tn_tu = self.compute_user_article_content_similarity(uname, article_id)
        sim_pn_pu = self.compute_user_article_pattern_similarity(uname, article_id)
        sim_en_eu = self.compute_user_article_entities_similarity(uname, article_id)

        summary = math.pow(a, 2) + math.pow(b, 2) + math.pow(c, 2)
        sim_fn_fu = ((a*sim_tn_tu) + (b*sim_pn_pu) + (c*sim_en_eu)) / math.sqrt(summary)
        # print("Overall similarity between %s and article #%s:" % (uname, article_id), sim_fn_fu)

        return sim_fn_fu

    # ####################################################################################
    # #################### 6.2.1 Article - Article Profile Similarity ####################
    # ####################################################################################

    # compare two news article

    # cosine similarity
    def compute_articles_content_similarity(self, art1_id, art2_id):
        art1_weight = []
        art2_weight = []

        # article's topic distribution (LDA)
        self.connection.cursor.execute("SELECT topicName, weight FROM article_topics "
                                       "WHERE articleId = '%s' " % art1_id)
        art1_t_name = [row[0] for row in self.connection.cursor]

        self.connection.cursor.execute("SELECT topicName, weight FROM article_topics "
                                       "WHERE articleId = '%s' " % art2_id)
        art2_t_name = [row[0] for row in self.connection.cursor]

        f = open("topics/article_topics.txt", 'r')
        answer = {}
        for line in f:
            k, v, i = line.strip().split(',')
            answer[k.strip()] = v.strip()
        f.close()

        for word in answer.keys():
            if word in art1_t_name:
                art1_weight.append(float(answer[word]))
            else:
                art1_weight.append(0)
        # print(len(art1_weight))

        for word in answer.keys():
            if word in art2_t_name:
                art2_weight.append(float(answer[word]))
            else:
                art2_weight.append(0)
        # print(len(art2_weight))

        tn_tn = 1 - spatial.distance.cosine(art1_weight, art2_weight)

        return tn_tn

    # jaccard similarity
    def compute_articles_pattern_similarity(self, art1_id, art2_id):
        acc1_users = self.article_profile.get_accessed_users_by_name(art1_id)
        # print("Acc1_users:", acc1_users)
        acc2_users = self.article_profile.get_accessed_users_by_name(art2_id)
        # print("Acc2_users:", acc2_users)

        pn_pn = self.user_profile.jaccard_similarity(acc1_users, acc2_users)
        return pn_pn

    # jaccard similarity
    def compute_articles_entities_similarity(self, art1_id, art2_id):
        art1_entities = self.article_profile.get_article_named_entities(art1_id)
        art2_entities = self.article_profile.get_article_named_entities(art2_id)

        en_en = self.user_profile.jaccard_similarity(art1_entities, art2_entities)

        return en_en

    def compute_articles_profile_similarity(self, art1_id, art2_id):
        a = b = c = 1
        sim_tn_tn = self.compute_articles_content_similarity(art1_id, art2_id)
        sim_pn_pn = self.compute_articles_pattern_similarity(art1_id, art2_id)
        sim_en_en = self.compute_articles_entities_similarity(art1_id, art2_id)

        summary = math.pow(a, 2) + math.pow(b, 2) + math.pow(c, 2)
        sim_fn_fn = ((a * sim_tn_tn) + (b * sim_pn_pn) + (c * sim_en_en)) / math.sqrt(summary)
        # print("Overall similarity between articles #%s and #%s:" % (art1_id, art2_id), sim_fn_fn)

        return sim_fn_fn
