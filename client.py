import socket, sys, boto3, datetime

target_host = sys.argv[1]
target_port = int(sys.argv[2])

# create socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# client connect
client.connect((target_host, target_port))

###create amazon s3 resource###
s3 = boto3.resource('s3')
school_num = '0516066'

responce = True
client_input = ''
login_bucket = ''
login_name = ''
while responce:
    responce = client.recv(1024).decode()
    
    
    if ('Register successfully.\n' in responce):
        name =  client_input.split(' ')[1] 
        bk = school_num + '-' + name.lower() + '-' + ''.join(str(ord(c)) for c in name)
        s3.create_bucket(Bucket=bk)

    if ('Welcome, ' in responce):
        name = client_input.split(' ')[1]
        login_name = name
        bk = school_num + '-' + name.lower() + '-' + ''.join(str(ord(c)) for c in name)
        target_bucket = s3.Bucket(bk)

    if ('Create post successfully.\n' in responce):
        title = client_input[client_input.index('--title')+8:client_input.index('--content')-1]
        content = client_input[client_input.index('--content')+10:-1]
        date = datetime.datetime.today().strftime("%Y/%m/%d")
        output = '{:<10}:'.format('Author') + login_name + '\n'
        output += '{:<10}:'.format('Title') + title + '\n'
        output += '{:<10}:'.format('Date') + date.replace("/","-") + '\n'
        output += '--\n'
        for row in content.split('<br>'):
            output += row + '\n'
        output += "--\n"
        with open('.tmp.txt', 'w') as f:
            f.write(output)
        ID = responce.split('\n')[1]
        responce = responce.split('\n')[0] + '\n' + responce.split('\n')[2]
        tb_name = title + '-' + ID + '-' + ''.join(str(ord(c)) for c in login_name)
        target_bucket.upload_file('.tmp.txt', tb_name)

    if ('Read successfully.\n' in responce):
        resp = responce.split('\n')
        name = resp[1]
        title = resp[2]
        bk = school_num + '-' + name.lower() + '-' + ''.join(str(ord(c)) for c in name)
        read_bucket = s3.Bucket(bk)
        tb_name = title + '-' + client_input.split(" ")[1].rsplit()[0] + '-' + ''.join(str(ord(c)) for c in name)
        read_obj = read_bucket.Object(tb_name)
        obj_content = read_obj.get()['Body'].read().decode()
        responce = obj_content + resp[3]

    if ('Delete successfully.\n' in  responce):
        resp = responce.split('\n')
        name = resp[1]
        title = resp[2]
        bk = school_num + '-' + name.lower() + '-' + ''.join(str(ord(c)) for c in name)
        read_bucket = s3.Bucket(bk)
        tb_name = title + '-' + client_input.split(" ")[1].rsplit()[0] + '-' + ''.join(str(ord(c)) for c in name)
        read_obj = read_bucket.Object(tb_name)
        read_obj.delete()
        responce = 'Delete successfully.\n' + resp[3]

    if ('Update successfully.\n' in  responce):
        resp = responce.split('\n')
        name = resp[1]
        title = resp[2]
        bk = school_num + '-' + name.lower() + '-' + ''.join(str(ord(c)) for c in name)
        read_bucket = s3.Bucket(bk)
        tb_name = title + '-' + client_input.split(" ")[1].rsplit()[0] + '-' + ''.join(str(ord(c)) for c in name)
        read_obj = read_bucket.Object(tb_name)
        obj_content = read_obj.get()['Body'].read().decode()
        if ('title=' in resp[3]):
            new_title = resp[3][6:]
            tb_name = new_title + '-' + client_input.split(" ")[1].rsplit()[0] + '-' + ''.join(str(ord(c)) for c in name)
            obj_content = obj_content.replace(title, new_title, 1)
        else:
            new_content = resp[3][8:]
            output = ""
            for row in new_content.split('<br>'):
                output += row + '\n'
            sp_obj = obj_content.split('--\n')
            sp_obj[1] = output
            obj_content = '--\n'.join(sp_obj)

        with open('.tmp.txt', 'w') as f:
            f.write(obj_content)

        read_obj.delete()
        read_bucket.upload_file('.tmp.txt', tb_name)
        responce = 'Update successfully.\n' + resp[4]

    if ('Comment successfully.\n' in responce):
        resp = responce.split('\n')
        name = resp[1]
        title = resp[2]
        comment = resp[3]
        bk = school_num + '-' + name.lower() + '-' + ''.join(str(ord(c)) for c in name)
        read_bucket = s3.Bucket(bk)
        tb_name = title + '-' + client_input.split(" ")[1].rsplit()[0] + '-' + ''.join(str(ord(c)) for c in name)
        read_obj = read_bucket.Object(tb_name)
        obj_content = read_obj.get()['Body'].read().decode()
        
        sp_obj = obj_content.split('--\n')
        sp_obj[2] += comment + '\n'
        obj_content = '--\n'.join(sp_obj)
        with open('.tmp.txt', 'w') as f:
            f.write(obj_content)

        read_obj.delete()
        read_bucket.upload_file('.tmp.txt', tb_name)

        responce = 'Comment successfully.\n' + resp[4]

    if ('Sent successfully.\n' in responce):
        cmd = client_input.split()
        username = cmd[1]
        subject = ' '.join(cmd[3:cmd.index("--content")])
        content = ' '.join(cmd[cmd.index("--content")+1:])
        bk = school_num + '-' + username.lower() + '-' + ''.join(str(ord(c)) for c in username)
        read_bucket = s3.Bucket(bk)
        tb_name = 'mail-' + subject + '-' + ''.join(str(ord(c)) for c in username)
        output = ""
        for row in content.split('<br>'):
            output += row + '\n'
        with open('.tmp.txt', 'w') as f:
            f.write(output)
        read_bucket.upload_file('.tmp.txt', tb_name)
        responce = 'Sent successfully.\n' + responce.split('\n')[2]

    elif ("Subject\t:" in responce):
        cmd = responce.split('\n')
        subject = cmd[0][cmd[0].index(':')+1:]
        bk = school_num + '-' + login_name.lower() + '-' + ''.join(str(ord(c)) for c in login_name)
        read_bucket = s3.Bucket(bk)
        mail_name = 'mail-' + subject + '-' + ''.join(str(ord(c)) for c in login_name)
        read_obj = read_bucket.Object(mail_name)
        obj_content = read_obj.get()['Body'].read().decode()
        responce += obj_content
    
    elif ('Mail deleted.\n' in responce):
        subject = responce.split('\n')[1]
        bk = school_num + '-' + login_name.lower() + '-' + ''.join(str(ord(c)) for c in login_name)
        read_bucket = s3.Bucket(bk)
        mail_name = 'mail-' + subject + '-' + ''.join(str(ord(c)) for c in login_name)
        read_obj = read_bucket.Object(mail_name)
        read_obj.delete()
        responce = 'Mail deleted.\n' + responce.split('\n')[2]


    print(responce, end='')

    if (responce[-2:] == '% '):
        client_input = input() + '\n'
        client.send(client_input.encode())

    
    
    
    

