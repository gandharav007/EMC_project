#!/usr/bin/env python
# coding: utf-8

# In[ ]:


from __future__ import print_function
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
import email
import base64
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer,ENGLISH_STOP_WORDS
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
import helpers
# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def fn2(df): #function to group the data using K-means algorithm ( unsupervised learning )
    
    vect = TfidfVectorizer(analyzer='word', stop_words='english')
    
    X=vect.fit_transform(df.email_body)
    
    clf=KMeans(n_clusters=3,max_iter=100,init='k-means++',n_init=1) # forming three different clusters( can be changed by the altering)
    
    labels = clf.fit_predict(X)
    
    pca=PCA(n_components=2).fit(X.todense())
    
    data2d =pca.transform(X.todense())
    
    centers2d = pca.transform(clf.cluster_centers_)
    
    plt.scatter(data2d[:,0], data2d[:,1],c=clf.labels_)
    
    plt.scatter(centers2d[:,0], centers2d[:,1], 
                marker='x', s=200, linewidths=3, c='r')
    plt.show() 
    
    helpers.plot_tfidf_classfeats_h(helpers.top_feats_per_cluster(X, labels, vect.get_feature_names(),0.1,25))
    
def fn(service_object,msg_ids,user_id):# function to extract the relevant emails with the Subject containing ("Thank You for applying") 
    d=[]
    for i in range(len(msg_ids)):
        
        res1=service_object.users().messages().get(userId='me',id=msg_ids[i],format='full').execute()
        
        for g in res1['payload']['headers']:
            
            if g['name']=='Subject':
                
                if "Thank You for applying" in g['value']: 
                    
                    res2=service_object.users().messages().get(userId='me',id=msg_ids[i],format='raw').execute()
                    
                    msg_r=base64.urlsafe_b64decode(res2['raw'].encode('ASCII'))
                    
                    msg_s=email.message_from_bytes(msg_r)
                    
                    content_types=msg_s.get_content_maintype()
                    
                    if content_types=='multipart':
                        
                        p= msg_s.get_payload()
                        
                        content1,content2=msg_s.get_payload()
                        
                        d.append(content1.get_payload())
                    else:
                        
                        d.append(msg_s.get_payload())
                        
    fn2(pd.DataFrame(d,columns=['email_body']))
                    
    
def main():
    
    
    creds = None
    
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
            
    # If there are no (valid) credentials available, let the user log in.
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
        # Save the credentials for the next run
        
        with open('token.pickle', 'wb') as token:
            
            pickle.dump(creds, token)

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    
    results = service.users().messages().list(userId='me',labelIds=['INBOX']).execute()
    
    labels = results.get('messages', [])
    
    ids=[msg['id'] for msg in labels] # extract the ids associated with all the emails in the INBOX.
    
    fn(service,ids,'me')

        


if __name__ == '__main__':
    main()

