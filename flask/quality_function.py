from __future__ import division
from scipy.special import comb
from itertools import combinations


class QualityEvaluation(object):
    def __init__(self, connection=None, profile_sim=None):
        self.connection = connection
        self.profile_similarity = profile_sim

    def difference(self, first, second):
        second = set(second)
        return [item for item in first if item not in second]

    def quality_function(self, s_set, n_group, username):

        f1 = self.first_component(s_set, n_group)
        f2 = self.second_component(s_set)
        f3 = self.third_component(s_set, username)
        f = f1 + f2 + f3
        print("Quality of selected set %s for user %s:" % (s_set, username), f)
        return f

    def first_component(self, s, n):
        s_len = len(s)
        diff = self.difference(n, s)
        diff_len = len(diff)
        if (diff_len == 0) or (s_len == 0):
            a = 0
        else:
            a = 1 / (diff_len * s_len)
        summary = 0

        for i in diff:
            for j in s:
                summary += self.profile_similarity.compute_articles_profile_similarity(i, j)

        return a * summary

    def second_component(self, s):
        s_len = len(s)
        combo = comb(s_len, 2, exact=False)
        a = 1 / combo
        summary = 0

        for i, j in combinations(s, 2):
            summary -= self.profile_similarity.compute_articles_profile_similarity(i, j)

        return a * summary

    def third_component(self, s, username):
        s_len = len(s)
        a = 1 / s_len
        summary = 0

        for i in s:
            summary += self.profile_similarity.compute_user_article_similarity(username, i)

        return a * summary
