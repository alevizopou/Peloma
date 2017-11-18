from __future__ import division
from decimal import Decimal


class ArticleRanking(object):
    def __init__(self, connection=None, art_profile=None):
        self.connection = connection
        self.article_profile = art_profile

    def compute_article_ranking(self, final_list):
        scores = []
        for article_id in final_list:
            self.connection.cursor.execute("SELECT popularity FROM article WHERE id = '%s' " % article_id)
            (n_pop,) = self.connection.cursor.fetchone()
            n_pop = round(Decimal(n_pop), 3)

            self.connection.cursor.execute("SELECT MAX(popularity) AS n_pop_max, MIN(popularity) AS n_pop_min "
                                           "FROM article")
            for row in self.connection.cursor:
                n_pop_max = row[0]
                n_pop_min = row[1]

            self.connection.cursor.execute("SELECT recency FROM article WHERE id = '%s' " % article_id)
            (n_inst,) = self.connection.cursor.fetchone()
            n_inst = round(Decimal(n_inst), 3)

            self.connection.cursor.execute("SELECT MAX(recency) AS n_inst_max, MIN(recency) AS n_inst_min "
                                           "FROM article")
            for row in self.connection.cursor:
                n_inst_max = row[0]
                n_inst_min = row[1]

            # nf: combination of popularity and recency
            np = (n_pop - n_pop_min) / (n_pop_max - n_pop_min)
            # print("np:", round(Decimal(np), 3))
            ni = (n_inst - n_inst_min) / (n_inst_max - n_inst_min)
            # print("ni:", round(Decimal(ni), 3))

            nf = np - ni
            scores.append(float(nf))

        z = list(zip(final_list, scores))
        out = sorted(z, key=lambda x: x[1], reverse=True)
        # print(out)
        # print(list(reversed(out)))

        new_list, new_scores = zip(*out)
        print("Final adjusted list:", list(new_list))

        return new_list
