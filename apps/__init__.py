__version__ = '0.1.0'


from apps.application import create_application


app = create_application()


@app.get('/ping', tags=['healz'])
def ping():
    return 'pong'
