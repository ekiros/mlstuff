import webbrowser, os, imaplib, email, base64

from email.header import decode_header
from msal import ConfidentialClientApplication


# use your email provider's IMAP server, you can look for your provider's IMAP server on Google
# or check this page: https://www.systoolsgroup.com/imap/

imap_server_outlook = "imap-mail.outlook.com"
imap_server_o365 = "outlook.office365.com"
imap_server_hotmail = "outlook.office365.com"
imap_server_gmail = "imap.gmail.com"
imap_server_yahoo = "imap.mail.yahoo.com"
imap_server_yahoo_plus = "plus.imap.mail.yahoo.com"
imap_server_aol = "imap.aol.com"

#TODO Add all other IMAP servers

def main():
    # TODO Add info as to how to add App password for IMAP
    # https://www.mailjerry.com/imap-login-failed/#:~:text=Top%205%20Reasons%20Why%20Your,OAuth%20Required
    # account credentials
    
    user_name = 'eskinder@microproduct.app' #NOTE: an input
    # create an IMAP4 class with SSL 
    conn = imaplib.IMAP4_SSL(imap_server_o365)
    conn.debug = 4

    try:
        # authenticate
        tenant_id = ''

        token = get_access_token_outlook(tenant_id)
        
        s,r = conn.authenticate('XOAUTH2', lambda _: gen_auth_string(user_name,token))

        print(f'Successfully authenticated: {s} and {r}')
        process(conn)
    except imaplib.IMAP4.error as e:
        return f'Authenticaion failed: {e}'
    

def get_access_token_outlook(tenant_id):
    print("Getting access token for MS Outlook...")

    # TODO These will be stored in a secure location to be retrieved as needed
    authority = f'https://login.microsoftonline.com/{tenant_id}'
    client_id = '' #application ID
    client_secret = ''
    client_secret_val = ''
    app_id = ''
    scope = ['https://outlook.office365.com/.default']

    try:
        app = ConfidentialClientApplication(
            app_id,
            app_name='intellisearch', 
            client_credential=client_secret_val,
            authority=authority 
            )
        res = app.acquire_token_for_client(scopes=scope)
        #print("Access token is ", res)
        return res['access_token']
    except Exception as e:
        return f'Error: Failed to acquire access token: {e}'

def gen_auth_string(user_email, access_token):
    print("Generating auth string...")

    auth_str = 'user=%s\x01auth=Bearer %s\x01\x01' % (user_email, access_token)
    #auth_str = f'user={user_email}\\1auth=Bearer {access_token}\\1\\1'
    print(auth_str)
    
    return base64.b64encode(auth_str.encode()).decode()
    

def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)

def process(imap_conn):
    status, messages = imap_conn.select("INBOX")
    #TODO list all folders too

    print("Status = ", status)

    # number of top emails to fetch
    N = 3
    # total number of emails
    messages = int(messages[0])

    for i in range(messages, messages-N, -1):
        # fetch the email message by ID
        res, msg = imap_conn.fetch(str(i), "(RFC822)")

        for response in msg:
            if isinstance(response, tuple):
                # parse a bytes email into a message object
                msg = email.message_from_bytes(response[1])
                # decode the email subject
                subject, encoding = decode_header(msg["Subject"])[0]
                if isinstance(subject, bytes):
                    # if it's a bytes, decode to str
                    subject = subject.decode(encoding)
                # decode email sender
                From, encoding = decode_header(msg.get("From"))[0]
                if isinstance(From, bytes):
                    From = From.decode(encoding)

                print("Subject:", subject)
                print("From:", From)

                # if the email message is multipart
                if msg.is_multipart():
                    # iterate over email parts
                    for part in msg.walk():
                        # extract content type of email
                        content_type = part.get_content_type()
                        content_disposition = str(part.get("Content-Disposition"))
                        try:
                            # get the email body
                            body = part.get_payload(decode=True).decode()
                        except:
                            pass
                        if content_type == "text/plain" and "attachment" not in content_disposition:
                            # print text/plain emails and skip attachments
                            print(body)
                        elif "attachment" in content_disposition:
                            # download attachment
                            filename = part.get_filename()
                            if filename:
                                folder_name = clean(subject)
                                if not os.path.isdir(folder_name):
                                    # make a folder for this email (named after the subject)
                                    os.mkdir(folder_name)
                                filepath = os.path.join(folder_name, filename)
                                # download attachment and save it
                                open(filepath, "wb").write(part.get_payload(decode=True))
                else:
                    # extract content type of email
                    content_type = msg.get_content_type()
                    # get the email body
                    body = msg.get_payload(decode=True).decode()
                    if content_type == "text/plain":
                        # print only text email parts
                        print(body)

                if content_type == "text/html":
                    # if it's HTML, create a new HTML file and open it in browser
                    folder_name = clean(subject)
                    if not os.path.isdir(folder_name):
                        # make a folder for this email (named after the subject)
                        os.mkdir(folder_name)
                    filename = "index.html"
                    filepath = os.path.join(folder_name, filename)
                    # write the file
                    open(filepath, "w").write(body)
                    # open in the default browser
                    webbrowser.open(filepath)
                print("="*100)

    # close the connection and logout
    imap_conn.close()
    imap_conn.logout()

## RUN ##
if __name__ == '__main__':
    main()
