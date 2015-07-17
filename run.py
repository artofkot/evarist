#!/usr/local/bin/python
from evarist import app
from flask_debugtoolbar import DebugToolbarExtension

app.config['DEBUG_TB_ENABLED']=True

toolbar = DebugToolbarExtension(app)
app.config['DEBUG_TB_PANELS'] = (
    'flask.ext.debugtoolbar.panels.versions.VersionDebugPanel',
    'flask.ext.debugtoolbar.panels.timer.TimerDebugPanel',
    'flask.ext.debugtoolbar.panels.headers.HeaderDebugPanel',
    'flask.ext.debugtoolbar.panels.request_vars.RequestVarsDebugPanel',
    'flask.ext.debugtoolbar.panels.template.TemplateDebugPanel',
    'flask.ext.debugtoolbar.panels.logger.LoggingPanel',
    'flask_debugtoolbar.panels.route_list.RouteListDebugPanel'
)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
app.run(debug=True)