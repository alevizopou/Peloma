from __future__ import division
from datetime import date


class ArticleInterface(object):
    def __init__(self, connection=None, u_profile=None):
        self.connection = connection
        self.user_profile = u_profile

    # ######################################################################################
    #  6.2.1 News Profile Construction (accessed users, popularity, recency, named entities)
    # ######################################################################################

    def article_profile_construction(self, article_id):
        accessed_users = self.get_accessed_users_by_name(article_id)
        article_popularity = self.compute_article_popularity(article_id)
        article_recency = self.compute_article_recency(article_id)
        entities_list = self.get_article_named_entities(article_id)

    # accessed_users
    def count_accessed_users(self, article_id):
        self.connection.cursor.execute("SELECT COUNT(DISTINCT user_name) FROM reading_history "
                                       "WHERE article_id = '%s' " % article_id)

        (acc_users,) = self.connection.cursor.fetchone()
        self.connection.connection.commit()
        return acc_users

    # accessed_users by name
    def get_accessed_users_by_name(self, article_id):
        self.connection.cursor.execute("SELECT DISTINCT user_name FROM reading_history "
                                       "WHERE article_id = '%s' " % article_id)

        accessed_users = [row[0] for row in self.connection.cursor]
        return accessed_users

    # popularity
    def compute_article_popularity(self, article_id):
        # no. of users accessing to the article
        print("Article ID:", article_id)
        accessed_users = self.count_accessed_users(article_id)
        print("Accessed Users:", accessed_users)

        # calculate users' pool
        # self.connection.cursor.execute("SELECT COUNT(Distinct user_name) FROM reading_history")
        self.connection.cursor.execute("SELECT COUNT(userName) FROM users")
        (users_pool,) = self.connection.cursor.fetchone()
        self.connection.connection.commit()
        print("Users' pool:", users_pool)

        # calculate article's popularity
        article_popularity = accessed_users/users_pool
        print("Article popularity:", article_popularity)

        self.connection.cursor.execute("UPDATE article SET popularity = '%s' "
                                       "WHERE id = '%s'" % (article_popularity, article_id))
        self.connection.connection.commit()

        return article_popularity

    # recency = (CurrentTime - PublishedTime)/(24*60)
    def compute_article_recency(self, article_id):
        current_date = date.today()

        self.connection.cursor.execute("SELECT released FROM article WHERE id = '%s'" % article_id)
        (published_date,) = self.connection.cursor.fetchone()

        article_recency = (current_date - published_date).days

        print("Days passed between {} and {}: {}".format(published_date.strftime("%d-%m-%Y"),
                                                         current_date.strftime("%d-%m-%Y"),
                                                         article_recency))

        self.connection.cursor.execute("UPDATE article SET recency = '%s' "
                                       "WHERE id = '%s'" % (article_recency, article_id))
        self.connection.connection.commit()

        return article_recency

        # article's named entities
    def get_article_named_entities(self, article_id):
        entities_list = []
        self.connection.cursor.execute("SELECT entity_name FROM named_entities WHERE article_id = '%s'" % article_id)
        for row in self.connection.cursor:
            entities_list.append(row[0])
        return entities_list
