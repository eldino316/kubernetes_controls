import mysql.connector


mydb = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="database"
)
mycursor = mydb.cursor()


def add_tracking(username, action):
    mycursor.execute('SELECT id FROM prs_info WHERE prs_name = %s', (username,))
    prs_info_id = mycursor.fetchall()[0][0]  

    mycursor.execute('SELECT cluster.id FROM cluster JOIN tracking ON cluster.id = tracking.cluster_id JOIN prs_info ON tracking.prs_info_id = prs_info.id WHERE prs_info.prs_name = %s', (username,))
    cluster_id = mycursor.fetchall()[0][0]

    mycursor.execute('INSERT INTO tracking (action, prs_info_id, cluster_id) VALUES (%s, %s, %s)', (action, prs_info_id, cluster_id))
    mydb.commit()

def get_clustername(username):

    mycursor.execute('SELECT cluster.name_cluster FROM cluster JOIN tracking ON cluster.id = tracking.cluster_id JOIN prs_info ON tracking.prs_info_id = prs_info.id WHERE prs_info.prs_name = %s', (username,))
    cluster_name = mycursor.fetchall()[0][0]

    return cluster_name  