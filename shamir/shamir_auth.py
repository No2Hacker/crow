import shamir
import sqlite3
import time
import settings

#Grabs user data from shares database and passes it to the validator
def auth_user(username, conn):
    
    #Grab share from db
    c = conn.cursor()
    c.execute("SELECT * FROM shares WHERE id = \""+ username +"\"")
    share = c.fetchone()
    
    #pass to validator
    validate(share, conn)

#Validates the db entry of a given user, if they provide correct shares then they are authenticated
def validate(share, share_conn):

    #quit if the user is attempting to authorize more than 5 seconds after submitting their third share
    if time.time() - int(share["timeout"]) > 5:
        print("No auth for you, timeout!")
        return
    
    #quit if an innapropriate number of shares has been sumbitted, log the number stored currently
    if not share["num_shares"] == settings.THRESH:
        print(share["id"] + " has submitted " + str(share["num_shares"]) + " shares!")
        return
    
    #create object holding the shares within tuples (nessecary for shamir library)
    s = []
    s.append((int(share["x1"]), int(share["y1"])))
    s.append((int(share["x2"]), int(share["y2"])))
    s.append((int(share["x3"]), int(share["y3"])))

    #recover the secret from the shares list
    secret = shamir.recover_secret(s)

    #open connection to secrets database and set up cursor
    conn = sqlite3.connect("secrets.db")
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    #select user's secret by ID
    c.execute("SELECT * FROM secrets WHERE id = \""+ share["id"] +"\"")
    res = c.fetchone()

    #if the secret recovered from the shares db matches the stored secret the user is authenticated
    if res["secret"] == str(secret):

        #delete shares information so that users cannot auth twoce for free
        share_conn.cursor.execute("DELETE FROM shares WHERE id = ?", [share['id']])
        share_conn.commit()
        #authorize the user (this is where the "door open", or "ssh successful" code would be in the real world)
        print(res["name"] + " is Authorized!")
    else:
        #deny user authentication
        print("No auth for you!")
    
    #close db connections
    conn.close()
    share_conn.close()
    return
