#!/usr/bin/python

import mysql.connector
from random import randint

MAX_ARTICLE_ID = 149

# Open database connection (If database is not created, don't give dbname)
cnx = mysql.connector.connect(host='localhost', user='root', password='root')

# prepare a cursor object using cursor() method
cursor = cnx.cursor()

cursor.execute("DROP DATABASE IF EXISTS news_db2")

try:
    cursor.execute("CREATE DATABASE news_db2 DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci")
except mysql.connector.Error as err:
    print('Error:', err)

cursor.execute("USE news_db2")
cursor.execute("DROP TABLE IF EXISTS article, category, article_text, article_tags, users, reading_history, "
               "cluster_topics, article_topics, group_lemmas, group_topics, similar_clusters")

cursor.execute("CREATE TABLE article ( \
id SMALLINT(3) NOT NULL AUTO_INCREMENT, \
title VARCHAR(150) NOT NULL, \
author VARCHAR(40), \
released DATE, \
popularity DECIMAL(4,3) DEFAULT 0, \
recency SMALLINT(3) DEFAULT 0, \
PRIMARY KEY(id) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("CREATE TABLE article_text ( \
article_id SMALLINT(3) NOT NULL AUTO_INCREMENT, \
body TEXT, \
PRIMARY KEY(article_id) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("CREATE TABLE category ( \
category_id SMALLINT(3) NOT NULL AUTO_INCREMENT, \
category_name VARCHAR(100) NOT NULL, \
PRIMARY KEY(category_id) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("CREATE TABLE article_tags ( \
article_id SMALLINT(3) NOT NULL, \
category_id SMALLINT(3) NOT NULL, \
CONSTRAINT TCAT \
FOREIGN KEY (article_id) REFERENCES article(id) \
ON DELETE CASCADE ON UPDATE CASCADE, \
CONSTRAINT TACAT \
FOREIGN KEY (category_id) REFERENCES category(category_id) \
ON DELETE CASCADE ON UPDATE CASCADE \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("CREATE TABLE users ( \
userId SMALLINT(3) NOT NULL AUTO_INCREMENT, \
userName VARCHAR(40) NOT NULL, \
PRIMARY KEY(userId) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("CREATE TABLE reading_history ( \
id int(100) NOT NULL AUTO_INCREMENT, \
user_name VARCHAR(40) NOT NULL, \
article_id SMALLINT(3) NOT NULL, \
PRIMARY KEY(id) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("CREATE TABLE similar_users ( \
userId SMALLINT(3) NOT NULL, \
similaruserId SMALLINT(3), \
similaruserName VARCHAR(40), \
CONSTRAINT TID \
FOREIGN KEY (userId) REFERENCES users(userId) \
ON DELETE CASCADE ON UPDATE CASCADE, \
CONSTRAINT TSID \
FOREIGN KEY (similaruserId) REFERENCES users(userId) \
ON DELETE CASCADE ON UPDATE CASCADE \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("CREATE TABLE cluster_topics ( \
topicId SMALLINT(3) NOT NULL AUTO_INCREMENT, \
topicName VARCHAR(40), \
weight DECIMAL(21,20), \
clusterId SMALLINT(3) NOT NULL, \
PRIMARY KEY(topicId), \
FOREIGN KEY(clusterId) REFERENCES category(category_id) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("ALTER TABLE cluster_topics AUTO_INCREMENT=1")

cursor.execute("CREATE TABLE article_topics ( \
topicId SMALLINT(3) NOT NULL AUTO_INCREMENT, \
topicName VARCHAR(40), \
weight DECIMAL(21,20), \
articleId SMALLINT(3) NOT NULL, \
PRIMARY KEY(topicId), \
FOREIGN KEY(articleId) REFERENCES article(id) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("ALTER TABLE article_topics AUTO_INCREMENT=1")

cursor.execute("CREATE TABLE group_lemmas ( \
topicId int(100) NOT NULL AUTO_INCREMENT, \
topicName VARCHAR(40), \
weight DECIMAL(21,20), \
articleId SMALLINT(3) NOT NULL, \
groupId SMALLINT(3) NOT NULL, \
clusterId SMALLINT(3) NOT NULL, \
PRIMARY KEY(topicId), \
FOREIGN KEY(clusterId) REFERENCES category(category_id) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("ALTER TABLE group_lemmas AUTO_INCREMENT=1")

cursor.execute("CREATE TABLE group_topics ( \
topicId int(100) NOT NULL AUTO_INCREMENT, \
topicName VARCHAR(40), \
weight DECIMAL(21,20), \
groupId SMALLINT(3) NOT NULL, \
clusterId SMALLINT(3) NOT NULL, \
PRIMARY KEY(topicId), \
FOREIGN KEY(clusterId) REFERENCES category(category_id) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("ALTER TABLE group_topics AUTO_INCREMENT=1")

cursor.execute("CREATE TABLE named_entities ( \
entity_id SMALLINT(3) NOT NULL AUTO_INCREMENT, \
entity_name VARCHAR(40) NOT NULL, \
entity_type VARCHAR(40) NOT NULL, \
article_id SMALLINT(3) NOT NULL, \
PRIMARY KEY(entity_id) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

cursor.execute("ALTER TABLE named_entities AUTO_INCREMENT=1")

cursor.execute("CREATE TABLE similar_clusters ( \
id SMALLINT(3) NOT NULL AUTO_INCREMENT, \
cluster_id SMALLINT(3) NOT NULL, \
cluster_weight DECIMAL(21,20) NOT NULL, \
PRIMARY KEY(id) \
)ENGINE=innoDB DEFAULT CHARACTER SET=utf8 COLLATE=utf8_unicode_ci")

# article id, title, author, date
# LOAD DATA LOCAL INFILE '/media/afro/True Dat/Thesis/mysql/article_info.txt'
cursor.execute("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/create_db/text/article_info.txt' "
               "INTO TABLE article LINES TERMINATED BY '\n'")

# categories
cursor.execute("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/create_db/text/categories.txt' "
               "INTO TABLE category FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' (@col1) set category_name=@col1")

# article tag
cursor.execute("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/create_db/text/article_tags.txt' "
               "INTO TABLE article_tags FIELDS TERMINATED BY ',' "
               "LINES TERMINATED BY '\n' (@col1,@col2) set article_id=@col1, category_id=@col2")

# article text
# LOAD DATA LOCAL INFILE '~/Thesis/mysql/keim.txt' INTO TABLE article_text LINES TERMINATED BY '\n' (body);
# CATEGORY 1: SCIENCE/TECHNOLOGY (20 articles)
cursor.execute("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/create_db/text/article_text1.txt' "
               "INTO TABLE article_text "
               "LINES TERMINATED BY '***********************************************************************' (body)")

cursor.execute("ALTER TABLE article_text AUTO_INCREMENT=21")

# CATEGORY 2: POLITICS (20 articles)
cursor.execute("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/create_db/text/article_text2.txt' "
               "INTO TABLE article_text "
               "LINES TERMINATED BY '***********************************************************************' (body)")

cursor.execute("ALTER TABLE article_text AUTO_INCREMENT=41")

# CATEGORY 3: SPORTS (20 articles)
cursor.execute("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/create_db/text/article_text3.txt' "
               "INTO TABLE article_text "
               "LINES TERMINATED BY '***********************************************************************' (body)")

cursor.execute("ALTER TABLE article_text AUTO_INCREMENT=61")

# CATEGORY 4: LIFE & STYLE (20 articles)
cursor.execute("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/create_db/text/article_text4.txt' "
               "INTO TABLE article_text "
               "LINES TERMINATED BY '***********************************************************************' (body)")

cursor.execute("ALTER TABLE article_text AUTO_INCREMENT=70")
# cursor.execute("ALTER TABLE article_text AUTO_INCREMENT=81")

# CATEGORIES FROM REUTERS (#5 SUGAR, #6 COFFEE, #7 HOUSING)
cursor.execute("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/flask/myweb/reuters.txt' "
               "INTO TABLE article_text "
               "LINES TERMINATED BY '***********************************************************************' (body)")

cursor.execute("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/create_db/text/users.txt' "
               "INTO TABLE users FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n' (@col1) set username=@col1")

cursor.execute(
    "UPDATE article SET released = DATE_FORMAT(FROM_UNIXTIME(RAND() * "
    "(UNIX_TIMESTAMP('2017-08-01') - UNIX_TIMESTAMP('2017-09-01')) + "
    "UNIX_TIMESTAMP('2017-08-01')), '%Y-%m-%d')")

cursor.execute("UPDATE article SET author='Reuters' WHERE author IS NULL")

cursor.execute("LOAD DATA LOCAL INFILE '/home/afroditi/PycharmProjects/create_db/text/createhistory.txt' "
               "INTO TABLE reading_history FIELDS TERMINATED BY ' ' LINES TERMINATED BY '\n' (@col1,@col2) "
               "set user_name=@col1, article_id=@col2")

# #####################################################
# generate random reading history for all stored users
# #####################################################

cursor.execute('SELECT COALESCE(MAX(id), 0) FROM reading_history')
(maxid, ) = cursor.fetchone()
# print("Max id:", maxid)

generated_ids = []

insert_query = 'INSERT INTO reading_history(id, user_name, article_id) VALUES(%s, %s, %s)'
select_query = 'SELECT userName FROM users'

num_of_articles_read = randint(10, 20)
cursor.execute(select_query)
results = cursor.fetchall()

for (username,) in results:
    print(username)
    for i in [randint(1, MAX_ARTICLE_ID) for _ in range(num_of_articles_read)]:
        maxid += 1
        cursor.execute(insert_query, (maxid, username, i))
        generated_ids.append(i)

cnx.commit()
cursor.close()
cnx.close()
