from nltk.corpus import wordnet
classes = ['UNDEFINED', 'LOG', 'FINGERPRINT', 'NETWORK', 'LOCATION', 'BATTERY', 'WIFI', 'CAMERA', 
    'ACCOUNT', 'CALENDAR', 'SCREEN', 'ACTIVITY_INFO', 'SYNC', 'DATABASE', 'CONTACT', 'MICROPHONE', 'PHONE_CALL', 
    'SENSOR', 'SMS','STORAGE', 'USER_HISTORY', 'HARDWARE', 'BLUETOOTH', 'MULTIMEDIA', 'SETTINGS', 'BUNDLE', 'SHARE_PREFERENCE', 
    'NOTIFICATION', 'FINANCIAL'
    ]

for word in classes:
    synonyms = []
    for syn in wordnet.synsets(word):
        for lm in syn.lemmas():
            synonyms.append(lm.name())
    print([word, set(synonyms)])
    

