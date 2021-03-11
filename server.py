import socket, threading, sys, sqlite3, datetime, boto3, random

###create server###
HOST = '0.0.0.0'
PORT = int(sys.argv[1])

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(10)
print ("[*] Listening on %s:%d" % (HOST, PORT))

###create sqlite3###
conn = sqlite3.connect('register.db')
c = conn.cursor()

c.execute("CREATE TABLE if not exists USERS (UID INTEGER PRIMARY KEY AUTOINCREMENT, Username TEXT NOT NULL UNIQUE, Email TEXT NOT NULL, Password TEXT NOT NULL)")
c.execute("CREATE TABLE if not exists BOARD ('Index' INTEGER PRIMARY KEY AUTOINCREMENT, Name TEXT NOT NULL UNIQUE, Moderator TEXT NOT NULL)")
c.execute("CREATE TABLE if not exists POST (ID INTEGER PRIMARY KEY AUTOINCREMENT, Board TEXT NOT NULL, Title TEXT NOT NULL, Author TEXT NOT NULL, Date TEXT NOT NULL, Content TEXT NOT NULL, Comment TEXT)")
c.execute("CREATE TABLE if not exists MAIL (Username TEXT, ID INTERGER, Subject TEXT NOT NULL, ComeFrom TEXT NOT NULL, Date TEXT NOT NULL)")
conn.commit()

def run_command(command, login, login_user):   
    output = ""
    cmd = command.split()

    conn = sqlite3.connect('register.db')
    c = conn.cursor()
    #print(command)
    if command[0].isspace():
        output = "% Only one space after the prompt!\n"
    elif cmd[0] == "register":
        if len(cmd) != 4:
            output = "Usage: register <username> <email> <password>\n"
        else:
            c.execute("SELECT * FROM users WHERE username=?", [cmd[1]])
            
            if c.fetchone() is None:
                output = "Register successfully.\n" 
                c.execute("INSERT INTO users (username, email, password) values (?, ?, ?)", (cmd[1], cmd[2], cmd[3]))
                conn.commit()
        
            else:
                output = "Username is already used.\n"

    elif cmd[0] == "login":
        if len(cmd) != 3:
            output = "Usage: login <username> <password>\n"
        else:
            if login:
                output = "Please logout first.\n"
            else:
                c.execute("SELECT * FROM users WHERE (username=? AND password=?)",(cmd[1], cmd[2]))
                if c.fetchone() is None:
                    output = "Login failed.\n"
                else:
                    login = True
                    login_user = cmd[1]
                    output = "Welcome, %s.\n" % cmd[1]

    elif cmd[0] == "whoami":
        if login:
            output = "%s.\n" % login_user
        else:
            output = "Please login first.\n"

    elif cmd[0] == "logout":
        if login:
            output = "Bye, %s.\n" % login_user
            login = False
        else:
            output = "Please login first.\n"
    #HW2
    elif cmd[0] == "create-board":
        if len(cmd) != 2:
                output = "Usage: create-board <name>\n"
        else:
            if login:
                c.execute("SELECT * FROM board WHERE name=?", [cmd[1]])

                if c.fetchone() is None:
                    output = "Create board successfully. \n"
                    c.execute("INSERT INTO board (name, moderator) values (?, ?)", (cmd[1], login_user))
                    conn.commit()
                else:
                    output = "Board already exist.\n"

            else:
                output = "Please login first.\n"

    elif cmd[0] == "create-post":    
        if len(cmd) < 6 and command.find("--title")!=-1 and command.find("--content")!=-1:
                output = "Usage: create-post <board-name> --title <title> --content <content>\n"
        else:
            if login:
                c.execute("SELECT * FROM board WHERE name=?", [cmd[1]])
                
                if c.fetchone() is None:
                    output = "Board is not exist.\n"
                else:
                    title = command[command.index('--title')+8:command.index('--content')-1]
                    content = command[command.index('--content')+10:]
                    date = datetime.datetime.today().strftime("%Y/%m/%d")
                    output = "Create post successfully.\n"
                    c.execute("INSERT INTO post (board, title, author, date, content) values (?, ?, ?, ?, ?)", (cmd[1], title, login_user, date, content))
                    conn.commit()
                    c.execute("SELECT MAX(ID) FROM POST")
                    output += str(c.fetchone()[0]) + '\n'
            else:
                output = "Please login first.\n"

    elif cmd[0] == "list-board":
        if len(cmd) == 1:
            output = '{:<7} {:<10} {:<20}\n'.format('Index','Name','Moderator')
            for row in c.execute("SELECT * FROM board"):
                output += '{:<7} {:<10} {:<20}\n'.format(str(row[0]), row[1], row[2])

        elif len(cmd) == 2 and cmd[1].find("##") == 0:
            output = '{:<7} {:<10} {:<20}\n'.format('Index','Name','Moderator')
            for row in c.execute("SELECT * FROM board WHERE name LIKE ?", ['%'+cmd[1][2:]+'%']):
               output += '{:<7} {:<10} {:<20}\n'.format(str(row[0]), row[1], row[2])

        else:
            output = "Usage: list-board ##<key>\n"
            
    elif cmd[0] == "list-post":
        if len(cmd) == 1:
            output = "Usage: list-post <board-name> ##<key>\n"
        else:
            c.execute("SELECT * FROM board WHERE name=?", [cmd[1]])
            if c.fetchone() is None:
                    output = "Board is not exist.\n"
            else:
                if len(cmd) == 2:
                    output = '{:<5} {:<20} {:<10} {:<5}\n'.format('ID','Title','Author','Date')
                    for row in c.execute("SELECT id,title,author,date FROM post WHERE board=?", [cmd[1]]):
                        output += '{:<5} {:<20} {:<10} {:<5}\n'.format(str(row[0]),row[1],row[2],row[3][5:])
                elif cmd[2].find('##') == 0:
                    output = '{:<5} {:<20} {:<10} {:<5}\n'.format('ID','Title','Author','Date')
                    keyword = '%' + ' '.join(cmd[2:])[2:] + '%'
                    for row in c.execute("SELECT id,title,author,date FROM post WHERE board=? AND title LIKE ?", (cmd[1], keyword)):
                        output += '{:<5} {:<20} {:<10} {:<5}\n'.format(str(row[0]),row[1],row[2],row[3][5:])
                else:
                    output = "Usage: list-post <board-name> ##<key>\n"

    elif cmd[0] == "read":
        if len(cmd) == 2 and cmd[1].isdigit():
            c.execute("SELECT * FROM post WHERE id=?", [cmd[1]])
            if c.fetchone() is None:
                output = "Post is not exist.\n"
            else:
                output = "Read successfully.\n"
                c.execute("SELECT * FROM post WHERE id=?", [cmd[1]])
                post = c.fetchone()
                output += post[3] + '\n'
                output += post[2] + '\n'
                
        else:
            output = "Usage: read <post-id>\n"

    elif cmd[0] == "delete-post":
        if len(cmd) == 2 and cmd[1].isdigit():
            c.execute("SELECT * FROM post WHERE id=?", [cmd[1]])
            post = c.fetchone()
            if post is None:
                output = "Post is not exist.\n"
            elif login:
                post_owner = post[3]
                if login_user == post_owner:
                    output = "Delete successfully.\n"
                    output += post[3] + '\n'
                    output += post[2] + '\n'
                    c.execute("DELETE FROM post WHERE id=?", [cmd[1]])
                    conn.commit()
                else:
                    output = "Not the post owner.\n"
            else:
                output = "Please login first.\n"

        else:
            output = "Usage: delete-post <post-id>\n"
    elif cmd[0] == "update-post":
        if cmd[1].isdigit() and (command.find("--title") != -1 or command.find("--content") != -1):
            c.execute("SELECT * FROM post WHERE id=?", [cmd[1]])
            post = c.fetchone()
            if post is None:
                output = "Post is not exist.\n"
            elif login:
                post_owner = post[3]
                if login_user == post_owner:
                    output = "Update successfully.\n"
                    output += post[3] + '\n'
                    output += post[2] + '\n'
                    t_idx = command.find('--title')
                    c_idx = command.find('--content')
                    if t_idx == -1:
                        c.execute("UPDATE post SET content=? WHERE id=?", (command[c_idx+10:],cmd[1]))
                        output += "content=" + command[c_idx+10:]+'\n'
                    elif c_idx == -1:
                        c.execute("UPDATE post SET title=? WHERE id=?", (command[t_idx+8:],cmd[1]))
                        output += "title=" + command[t_idx+8:]+'\n'
                    elif t_idx < c_idx:
                        c.execute("UPDATE post SET content=? WHERE id=?", (command[t_idx+8:c_idx], cmd[1]))
                        output += "content=" + command[t_idx+8:c_idx]+'\n'
                    else:
                        c.execute("UPDATE post SET content=? WHERE id=?", (command[c_idx+10:t_idx], cmd[1]))
                        output += "content=" + command[c_idx+10:t_idx]+'\n'

                    conn.commit()
                else:
                    output = "Not the post owner.\n"
            else:
                output = "Please login first.\n"
            
        else:
            output = "Usage: update-post <post-id> --title/content <new>\n"

    elif cmd[0] == "comment":
        if len(cmd) == 1:
            output = "Usage: comment <post-id> <comment>\n"
        elif cmd[1].isdigit():
            c.execute("SELECT * FROM post WHERE id=?", [cmd[1]])
            if c.fetchone() is None:
                output = "Post is not exist\n"
            elif login:
                output = "Comment successfully.\n"
                c.execute("SELECT * FROM post WHERE id=?", [cmd[1]])
                post = c.fetchone()
                comment = post[6]
                if comment is None:
                    comment = login_user + ": " + ' '.join(cmd[2:]) + "<br>"
                elif comment[0] is None:
                    comment = login_user + ": " + ' '.join(cmd[2:]) + "<br>"
                else:
                    comment = comment[0] + login_user + ": " + ' '.join(cmd[2:]) + "<br>"
                output += post[3] + '\n'
                output += post[2] + '\n'
                output += comment[:-4] + '\n'
                c.execute("UPDATE post SET comment=? WHERE id=?", (comment, cmd[1]))
                conn.commit()
            else:
                output = "Please login first.\n"

        else:
            output = "Usage: comment <post-id> <comment>\n"
    ### HW3
    elif cmd[0] == "mail-to":
        if len(cmd) < 6 and command.find("--subject")!=-1 and command.find("--content")!=-1:
            output = "Usage: mail-to <username> --subject <subject> --content <content>\n"
        else:
            if login:
                username = cmd[1]
                subject = ' '.join(cmd[3:cmd.index("--content")])
                date = datetime.datetime.today().strftime("%m/%d")
                c.execute("SELECT * FROM USERS WHERE Username=?", [username])
                user_data = c.fetchone()
                if user_data is None:
                    output = username + " does not exist.\n"
                else:
                    c.execute("SELECT MAX(ID) From MAIL WHERE Username=?", [username])
                    MID = c.fetchone()[0]
                    if MID is None:
                        MID = 1
                    else:
                        MID += 1
                    c.execute("INSERT into MAIL(Username, ID, Subject, ComeFrom, Date) values (?, ?, ?, ?, ?)", (username, MID, subject, login_user, date))
                    output = "Sent successfully.\n" + str(MID) + '\n'
                    conn.commit()
            else:
                output = "Please login first.\n"

    elif cmd[0] == "list-mail":
        if len(cmd) != 1:
            output = "Usage: list-mail\n"
        else:    
            if login:
                output = 'ID\t'+'Subject\t'+'From\t'+'Date\n'
                ID = 1
                for row in c.execute("SELECT ID, Subject, ComeFrom, Date From MAIL where Username=?", [login_user]):
                    output += str(ID)+'\t'+row[1]+'\t'+row[2]+'\t'+row[3]+'\n'
                    ID += 1
            else:
                output = "Please login first.\n"
    elif cmd[0] == "retr-mail":
        if len(cmd) != 2 or not cmd[1].isdigit():
            output = "Usage: retr-mail <mail#>\n"
        else:
            if login:
                c.execute("SELECT Subject, ComeFrom, Date from MAIL where username=? AND ID=?", (login_user, int(cmd[1])))
                data = c.fetchone()
                if data is None:
                    output = "No such mail.\n"
                else:
                    output = "Subject\t:" + data[0] + '\n'
                    output += "From\t:" + data[1] + '\n'
                    output += "Date\t:" + data[2] + '\n'
                    output += '--\n'
            else:
                output = "Please login first.\n"

    elif cmd[0] == "delete-mail":
        if len(cmd) != 2 or not cmd[1].isdigit():
            output = "Usage: delete-mail <mail#>\n"
        else:
            if login:
                c.execute("SELECT Subject from MAIL where username=? AND ID=?", (login_user, int(cmd[1])))
                data = c.fetchone()
                if data is None:
                    output = "No such mail.\n"
                else:
                    c.execute("DELETE FROM MAIL WHERE username=? AND ID=?", (login_user, int(cmd[1])))
                    conn.commit()
                    output = "Mail deleted.\n" + data[0] + '\n'
                    
                    
            else:
                output = "Please login first.\n"

    else:
        output = "% command not found\n"              
    

    '''
    for row in c.execute("SELECT * FROM users"):
        print(row)
    conn.commit()
    '''
    return output, login, login_user



def handle_client(client_socket):
    Welcome = "********************************\n" + \
              "** Welcome to the BBS server. **\n" + \
              "********************************\n"
    client_socket.send(Welcome.encode())
    login = False
    login_user = ""

    while True:
        client_socket.send("% ".encode())
        cmd_buffer = ""
        while "\n" not in cmd_buffer:
            cmd_buffer += client_socket.recv(1024).decode()
        cmd_buffer = cmd_buffer.rstrip()
        print(cmd_buffer)
        if cmd_buffer == "exit":
            break
        elif len(cmd_buffer) is 0:
            continue
        response, login, login_user = run_command(cmd_buffer, login, login_user)
        client_socket.send(response.encode())

    client_socket.close()

    
    
while True:
    (client, addr) = server.accept()
    print("[*] New connection.")
    print ("[*] Accepted connection from %s:%d" % (addr[0],addr[1]))
    
    client_handler = threading.Thread(target=handle_client, args=(client,))
    client_handler.start()
    


