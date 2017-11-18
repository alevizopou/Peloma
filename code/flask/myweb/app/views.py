from app import app
from flask import render_template, session, request, redirect
from flaskext.mysql import MySQL
from itertools import combinations
from db_connection import DBConnection
from user_profile import UserInterface
from article_profile import ArticleInterface
from profile_similarity import ProfileInterface
from ranking_adjustment import ArticleRanking
from quality_function import QualityEvaluation
import random
MAX_BUDGET = 4

mysql = MySQL()
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'root'
app.config['MYSQL_DATABASE_DB'] = 'news_db2'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

connx = DBConnection()
nl = UserInterface(connx)
art = ArticleInterface(connx, nl)
prof = ProfileInterface(connx, nl, art)
rank = ArticleRanking(connx, art)
qual = QualityEvaluation(connx, prof)


@app.route('/')
@app.route('/start', methods=['GET', 'POST'])
def start_button():
    # nl.drop_table_with_similar_clusters()
    return render_template('start.html')


@app.route('/createprofiles', methods=['GET', 'POST'])
def create_profiles():
    users = nl.get_user()
    for (username,) in users:
        print("==========================")
        print(username)
        articles_id = nl.user_history(username)
        nl.user_profile_construction(username)
        for (art_id,) in articles_id:
            art.article_profile_construction(art_id)
    return redirect('/login')


@app.route('/login')
def logged_users():
    users = nl.get_user()
    return render_template('users.html', uslist=users)


@app.route('/logout')
def logout():
    # remove the username from the session if it's there
    session.pop('username', None)
    return redirect('/login')


@app.route('/articles', methods=['GET', 'POST'])
def get_article():
    if request.method == 'POST':
        if request.form['users'] == "Create new user":
            username = request.form['username']
            # Insert new user into database
            nl.create_user(username)
        else:
            username = request.form['users']

        session['my_user'] = username

    username = session['my_user']
    categories, big_zip_list = nl.show_articles()
    return render_template('articles.html', catlist=categories, ziplist=big_zip_list, user_selected=username)


@app.route('/show_article/<article>', methods=['GET', 'POST'])
def one_article(article):
    username = session['my_user']
    # insert the new article in user's reading history
    nl.insert_articles(article, username)
    # View article's text
    article_text = nl.view_text(article)

    nl.user_profile_construction(username)
    art.article_profile_construction(article)

    return render_template('article_text.html', text=article_text, user_selected=username)


@app.route('/history')
def view_history():
    username = session['my_user']
    articles_in_history = nl.view_history(username)
    return render_template('history.html', artlist=articles_in_history, user_selected=username)


@app.route('/recommend', methods=['GET', 'POST'])
def check_quality():
    username = session['my_user']

    articles_in_history = nl.user_unique_history(username)

    if not articles_in_history:
        return render_template('empty.html', user_selected=username)
    else:
        user_weight, full_vocabulary = nl.user_profile_construction(username)

        nl.user_unique_history_cluster(username)
        accessed_ids = [article[0] for article in articles_in_history]
        print("%s's reading history:" % username, accessed_ids)

        selected_clusters_ids, cluster_ids_and_weights = nl.find_similar_clusters(user_weight, full_vocabulary,
                                                                                  accessed_ids, username)
        # Selected groups inside selected clusters
        selected_groups_ids = nl.find_similar_groups(user_weight, full_vocabulary, selected_clusters_ids,
                                                     accessed_ids, username)
        # [3, 1, 0]

        selected_groups_articles = nl.articles_inside_selected_groups(selected_clusters_ids, selected_groups_ids)
        # [[46, 47], [60, 63, 64, 65, 67, 68, 69], [126, 128]]

        # unread article from the final selected groups (one group per selected Cluster)
        rest_ids_per_group = nl.unread_user_articles(selected_clusters_ids, selected_groups_ids,
                                                     selected_groups_articles, accessed_ids)

        # qualities = []
        budget_list = []
        f_list = []

        # budget: maximum number of recommended items in each news cluster
        cluster_ids_and_budget = nl.dictionary_with_budget_per_cluster(cluster_ids_and_weights, MAX_BUDGET)

        for i in cluster_ids_and_budget:
            budget_list.append(cluster_ids_and_budget[i])
        print("Full budget list:", budget_list)  # Budget list: [3, 5, 4]

        # [[], [27, 29, 34, 40], [41, 42, 47, 59]]
        for num, group in enumerate(rest_ids_per_group):
            print("---------------------------")
            print("Group #{}:".format(num+1, group))
            print("---------------------------")
            print("BUDGET:", budget_list[num])
            subset_list = []

            if len(group) < budget_list[num]:
                print("Help! More articles needed!")
                budget = len(group)
                if budget == 0:
                    i = 0
                    print("Forever empty!")
                for subset in combinations(group, budget):
                    subset_list.append(list(subset))
            else:
                for subset in combinations(group, budget_list[num]):
                    subset_list.append(list(subset))
            print("Subset list:", subset_list)
            chosen_subset = random.choice(subset_list)
            print("Random choice of a subset:", chosen_subset)

            # quality = qual.quality_function(chosen_subset, rest_ids_per_group[num], username)
            # qualities.append(quality)
            f_list.append(chosen_subset)

        # it may include an empty sublist
        # f_list: [[], [29, 34, 40], [42, 59]]
        # del category with no articles to protect recommendation form's shape
        print("f_list:", f_list)
        for index, val in enumerate(f_list):
            if len(val) == 0:
                del selected_clusters_ids[index]
        print(selected_clusters_ids)

        final_list = []
        for sublist in f_list:
            if len(sublist) == 0:
                continue
            else:
                final_mini_list = rank.compute_article_ranking(sublist)
                final_list.append(final_mini_list)

        final_list_of_lists = [list(elem) for elem in final_list]
        final_zip = nl.view_articles(final_list_of_lists)

        return render_template('recommend.html', catlist=selected_clusters_ids, ziplist=final_zip, user_selected=username)


@app.route('/feedback', methods=['GET', 'POST'])
def give_feedback():
    username = session['my_user']
    shopping_list = []

    if request.method == 'POST':
        checked = len(request.form.getlist('check'))
        allboxes = len(request.form.getlist('uncheck'))
        unchecked = allboxes - checked

        listdiv = request.form["radiocheck1"]
        listord = request.form["radiocheck2"]

        shopping_list.append(request.form['radiocheck1'])
        shopping_list.append(request.form['radiocheck2'])
    print(shopping_list)
    return render_template('feedback.html', user_selected=username, check_selected=checked, all=allboxes,
                           diver=listdiv, ord=listord)
