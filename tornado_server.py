from bokeh.embed import server_document
from bokeh.server.server import Server


def create_bokeh_server(io_loop, files, argvs, host, port):
    '''Start bokeh server with applications paths'''
    from bokeh.server.server import Server
    from bokeh.command.util import build_single_handler_applications

    # Turn file paths into bokeh apps
    apps = build_single_handler_applications(files, argvs)

    # kwargs lifted from bokeh serve call to Server, with created io_loop
    kwargs = {
        'io_loop':io_loop,
        'generate_session_ids':True,
        'redirect_root':True,
        'secret_key':None,
        'num_procs':1,
        'sign_sessions':False,
        'port':port,
        'use_index':True
    }
    server = Server(apps,**kwargs)

    return server


def run_single_app(files, port=5000, new='tab'):

    def start_bokeh(io_loop):
        '''Start the `io_loop`'''
        io_loop.start()
        return None

    def launch_app(host, app_name, new):
        '''Lauch app in browser

        Ideally this would `bokeh.util.browser.view()`, but it doesn't work
        '''
        import webbrowser

        # Map method strings to webbrowser method
        options = {'current':0, 'window':1, 'tab':2}

        # Concatenate url and open in browser, creating a session
        app_url = 'http://{}/{}'.format(host, app_name)
        print('Opening `{}` in browser'.format(app_url))
        webbrowser.open(app_url, new=options[new])

        return None

    def server_loop(server, io_loop):
        '''Check connections once session created and close on disconnect'''
        import time

        connected = [True,]
        session_loaded = False
        while any(connected):

            # Check if no session started on server
            sessions = server.get_sessions()
            if not session_loaded:
                if sessions:
                    session_loaded = True
            # Once 1+ sessions started, check for no connections
            else:
                # List of bools for each session
                connected = [True,]*len(sessions)
                # Set `connected` item false no connections on session
                for i in range(len(sessions)):
                    if sessions[i].connection_count == 0:
                        connected[i] = False
            # Keep the pace down
            time.sleep(2)

        # Stop server once opened session connections closed
        io_loop.stop()

        return None

    import os
    import threading
    import tornado.ioloop
    import tornado.autoreload
    import time

    # Initialize some values, sanatize the paths to the bokeh plots
    argvs = {}
    app_names = []
    for path in files:
        argvs[path] = None
        app_names.append(os.path.splitext(os.path.split(path)[1])[0])

    # Concate hostname/port for creating handlers, launching apps
    host = 'localhost:{}'.format(port)

    # Initialize the tornado server
    io_loop = tornado.ioloop.IOLoop.instance()
    tornado.autoreload.start(io_loop)

    # Add the io_loop to the bokeh server
    server = create_bokeh_server(io_loop, files, argvs, host, port)

    print('Starting the server on {}'.format(host))
    args = (io_loop,)
    th_startup = threading.Thread(target=start_bokeh, args=args)
    th_startup.start()

    # Launch each application in own tab or window
    th_launch = [None,]*len(app_names)
    for i in range(len(app_names)):
        args = (host, app_names[i], new)
        th_launch[i] = threading.Thread(target=launch_app, args=args)
        th_launch[i].start()
        # Delay to allow tabs to open in same browser window
        time.sleep(2)

    # Run session connection test, then stop `io_loop`
    args = (server, io_loop)
    th_shutdown = threading.Thread(target=server_loop, args=args)
    th_shutdown.start()

    return None


if __name__ == "__main__":
    # app.run()
    run_single_app(["islm.py"], port=5006)