# -*- coding: utf-8 -*-
### required - do no delete
#
# 
# sudo easy_install --upgrade google-api-python-client
# sudo  easy_install rfc3339



def user(): return dict(form=auth())
def download(): return response.download(request,db)
def call():
    session.forget()
    return service()
### end requires
def index():
    form = SQLFORM.factory(
        Field('Nombre', requires=IS_NOT_EMPTY(),),
        Field('Email',),
        Field('Tlf',),
        Field('Inicio','datetime'),
        Field('Fin','datetime'),
        
        )
    if form.process().accepted:
        response.flash = 'Cita agregada %s ' % form.vars.Nombre        
        session.your_name = form.vars.your_name
        session.your_image = form.vars.your_image
        insert_ajx(form.vars.Nombre,form.vars.Email,form.vars.Tlf,form.vars.Inicio,form.vars.Fin)
    elif form.errors:
        response.flash = 'form has errors'
    script=''

    return dict(form=form,script=script)


def insert_ajx(nombre,email,tlf,inicio,fin):
    rest="POST https://www.googleapis.com/calendar/v3/calendars/%s/events" % settings.google_calid
    from rfc3339 import rfc3339
    inicio=rfc3339(inicio)
    fin=rfc3339(fin)
    event = {
        'summary': nombre,
        'location': 'Caracas',
        'start': {
            'dateTime': inicio,
            'timeZone':"America/Caracas",
            },
        'end': {
            'dateTime': fin,
            'timeZone':"America/Caracas"
            },
        'attendees': [
            {
            'email': email,
            # Other attendee's data...
             },        
        ],
    }
    from oauth2client import gce
    import os
    import httplib2
    from apiclient.discovery import build    
    from oauth2client.client import flow_from_clientsecrets
    from oauth2client.file import Storage
    from oauth2client.tools import run

    jsonfile=os.path.join(request.folder,'static','client_secrets.json')
    storage = Storage('credentials.dat')
    credentials = storage.get()
    
    redirecturl='urn:ietf:wg:oauth:2.0:oob'
    flow = flow_from_clientsecrets(jsonfile,
                               scope='https://www.googleapis.com/auth/calendar',
                               redirect_uri=redirecturl)

    if credentials is None or credentials.invalid:
        credentials = run(flow, storage)
    http = httplib2.Http()
    http = credentials.authorize(http)
    
    service = build('calendar', 'v3',http=http)

    created_event = service.events().insert(calendarId=settings.google_calid, body=event).execute()
    #response.flash = created_event['id']
    script=''
    return dict(script=script)

def delete_ajx():
    id=request.vars.id
    id=id.replace('@google.com','')
    from oauth2client import gce
    import os
    import httplib2
    from apiclient.discovery import build    
    from oauth2client.client import flow_from_clientsecrets
    from oauth2client.file import Storage
    from oauth2client.tools import run

    jsonfile=os.path.join(request.folder,'static','client_secrets.json')
    storage = Storage('credentials.dat')
    credentials = storage.get()
    
    redirecturl='urn:ietf:wg:oauth:2.0:oob'
    flow = flow_from_clientsecrets(jsonfile,
                               scope='https://www.googleapis.com/auth/calendar',
                               redirect_uri=redirecturl)

    if credentials is None or credentials.invalid:
        credentials = run(flow, storage)
    http = httplib2.Http()
    http = credentials.authorize(http)
    
    service = build('calendar', 'v3',http=http)
    
    created_event = service.events().delete(calendarId=settings.google_calid, eventId=id).execute()
    script="window.location.href = '%s'; " % URL('default','index')
    return dict(script=script)


def error():
    return dict()

@auth.requires_login()
def mymap():
    rows=db(db.t_appointment.created_by==auth.user.id)(db.t_appointment.f_start_time>=request.now).select()
    return dict(rows=rows)

@auth.requires_login()
def mycal():
    rows=db(db.t_appointment.created_by==auth.user.id).select()
    return dict(rows=rows)

@auth.requires_login()
def appointment_create():
    form=crud.create(db.t_appointment,
                     onvalidation=geocode2,
                     next='appointment_read/[id]')
    return dict(form=form)

@auth.requires_login()
def appointment_read():
    record = db.t_appointment(request.args(0)) or redirect(URL('error'))
    form=crud.read(db.t_appointment,record)
    return dict(form=form)

@auth.requires_login()
def appointment_update():
    record = db.t_appointment(request.args(0),active=True) or redirect(URL('error'))
    form=crud.update(db.t_appointment,record,next='appointment_read/[id]',
                     onvalidation=geocode2,
                     ondelete=lambda form: redirect(URL('appointment_select')),
                     onaccept=crud.archive)
    return dict(form=form)

@auth.requires_login()
def appointment_select():
    f,v=request.args(0),request.args(1)
    query=f and db.t_appointment[f]==v or db.t_appointment
    rows=db(query)(db.t_appointment.active==True).select()
    return dict(rows=rows)

@auth.requires_login()
def appointment_search():
    form, rows=crud.search(db.t_appointment,query=db.t_appointment.active==True)
    return dict(form=form, rows=rows)
