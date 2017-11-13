from __future__ import division
from decimal import Decimal

# given a list of articles for each topic category
# Cluster 1: [1, 5, 9]
# Cluster 2: [21, 30]
# Cluster 3: [42, 45, 48]


class ArticleRanking(object):
    def __init__(self, connection=None, art_profile=None):
        self.connection = connection
        self.article_profile = art_profile

    def compute_article_ranking(self, final_list):
        scores = []
        for article_id in final_list:
            self.connection.cursor.execute("SELECT popularity FROM article WHERE id = '%s' " % article_id)
            (n_pop,) = self.connection.cursor.fetchone()
            # n_pop = self.article_profile.compute_article_popularity(article_id)
            n_pop = round(Decimal(n_pop), 3)

            self.connection.cursor.execute("SELECT MAX(popularity) AS n_pop_max, MIN(popularity) AS n_pop_min "
                                           "FROM article")
            for row in self.connection.cursor:
                n_pop_max = row[0]
                n_pop_min = row[1]

            self.connection.cursor.execute("SELECT recency FROM article WHERE id = '%s' " % article_id)
            (n_inst,) = self.connection.cursor.fetchone()
            # n_inst = self.article_profile.compute_article_recency(article_id)
            n_inst = round(Decimal(n_inst), 3)

            self.connection.cursor.execute("SELECT MAX(recency) AS n_inst_max, MIN(recency) AS n_inst_min "
                                           "FROM article")
            for row in self.connection.cursor:
                n_inst_max = row[0]
                n_inst_min = row[1]

            # print("max, min, pop:", n_pop_max, n_pop_min, n_pop)
            # print("max, min, pop:", n_inst_max, n_inst_min, n_inst)

            # nf: combination of popularity and recency
            np = (n_pop - n_pop_min) / (n_pop_max - n_pop_min)
            # print("np:", round(Decimal(np), 3))
            ni = (n_inst - n_inst_min) / (n_inst_max - n_inst_min)
            # print("ni:", round(Decimal(ni), 3))

            nf = np - ni
            # print("nf:", round(Decimal(nf), 3))
            # print("\n")
            scores.append(float(nf))
        # print("Scores:", scores)

        z = list(zip(final_list, scores))
        out = sorted(z, key=lambda x: x[1], reverse=True)
        # print(out)
        # print(list(reversed(out)))

        new_list, new_scores = zip(*out)
        print("Final adjusted list:", list(new_list))
        # print("Final adjusted scores list:", list(new_scores))

        return new_list
