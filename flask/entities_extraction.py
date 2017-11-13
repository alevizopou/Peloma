import os
import mysql.connector
from bs4 import BeautifulSoup

NUM_OF_ARTICLES = 148
# NUM_OF_ARTICLES = 160
userhome = os.path.expanduser('~')
DIR = os.path.join(userhome, "PycharmProjects/out")


class ExtractEntities(object):
    def __init__(self, db_host='localhost', db_user='root', db_password='root', db_database='news_db2'):
        self.host = db_host
        self.user = db_user
        self.password = db_password
        self.database = db_database
        self.connection = mysql.connector.connect(host=self.host, user=self.user, password=self.password,
                                                  database=self.database)
        self.cursor = self.connection.cursor()

    def extract_named_entities(self):
        for art_id in range(1, NUM_OF_ARTICLES+1):
            file = "article{}.txt.xml".format(art_id)

            organization, t1_list, person, t2_list, location, t3_list = ([] for i in range(6))

            soup = BeautifulSoup(open(os.path.join(DIR, file)).read(), "lxml")

            print("\n", "#", art_id, "xml file:", os.path.join(DIR, file))

            for message in soup.findAll('organization'):
                # print(message.string)
                organization.append(message.string)
                t1_list.append('organization')
            print(list(set(organization)))

            for message in soup.findAll('person'):
                # print(message.string)
                person.append(message.string)
                t2_list.append('person')
            print(list(set(person)))

            for message in soup.findAll('location'):
                # print(message.string)
                location.append(message.string)
                t3_list.append('location')
            print(list(set(location)))

            entities_list = organization + person + location
            type_list = t1_list + t2_list + t3_list

            self.entities_to_file(entities_list, type_list, art_id)

        self.unique_entities_to_file()
        self.entities_to_database()

    def entities_to_file(self, entities_list, type_list, art_id):
        # write each article's entities to file
        with open("entities.txt", "a") as f:
            for (t, w) in zip(entities_list, type_list):
                f.write("{0}\t{1}\t{2}\n".format(t, w, art_id))

    def unique_entities_to_file(self):
        lines_seen = set()  # holds lines already seen
        outfile = open("unique_entities.txt", "w")
        for line in open("entities.txt", "r"):
            if line not in lines_seen:  # not a duplicate
                outfile.write(line)
                lines_seen.add(line)
        outfile.close()

    def entities_to_database(self):
        self.cursor.execute("LOAD DATA LOCAL INFILE '/home/afro/PycharmProjects/flask/myweb/unique_entities.txt' "
                            "INTO TABLE named_entities FIELDS TERMINATED BY '\t' LINES TERMINATED BY '\n' "
                            "(@col1,@col2,@col3) set entity_name=@col1, entity_type=@col2, article_id=@col3")
        self.connection.commit()
