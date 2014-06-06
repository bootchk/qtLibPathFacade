'''
Copyright 2014 Lloyd Konneker

Released under GPLv3
'''

import sys, syslog

from PyQt5.QtCore import QCoreApplication, QDir



def logAlert(message):
  # OSX only logs above ALERT
  # After OSX 10.8, stderr and stdout are to /dev/null ?
  syslog.syslog(syslog.LOG_ALERT, message)


class QtLibPathFacade(object):
  '''
  Hides Qt dynamic library path.
  
  This addresses these Qt design issues :
  - default Qt library search path won't find platform plugins when app is sandboxed
  - qt.conf is not read before platform plugin is needed
  - chicken and egg issue setting up library path to find platform abstraction plugin:
    you can't create your QApplication before the platform plugin is loaded,
    but you can't use QCoreApplication.applicationDirPath() before you have an instance knowing sys.argv
    
  It logs to syslog:
  - the result is crucial
  - syslog works on OSX
  But if you build Python static, uncomment syslogmodule.c in Module/Setup.
  
  A class not to be instantiated.
  
  Typically used only once as in this example:
  
  def main(args):
      QtLibPathFacade.addBundledPluginPath()
      app = QApplication(args)
      ...
      
  Note Qt uses the same path to search for plugins and other dynamically loaded libraries explicitly loaded by an app.
  At the time when this class is needed, the Qt frameworks (dynamic libraries) have already been loaded by OS machinery.
  So this does not add any dirs except .app/Contents/PlugIns, e.g. not /Frameworks.
  And just after this, Qt reads qt.conf and further adjusts the library path?
  '''
  
  @classmethod
  def addBundledPluginsPath(cls):
    '''
    Set library path so bundled plugins are found on OSX.
    You should call this before instantiating QApplication if the platform abstraction plugin is not statically linked
    and the app is sandboxed (plugins in the bundle.)
    
    You can call this on any platform.
    On OSX, when the platform plugin libqcocoa.dylib is in the PlugIns dir  of the app bundle (.app) , 
    this prepends to Qt's library path.
    On other platforms, it usually has no effect on Qt's library path.
    '''
    aAppDirPath = cls._appDirPath()
    # assert not exist an instance of QApplication, else the following addLibraryPath() is specific to that instance?
    
    pluginDirPath = cls._appBundlePluginsPath(aAppDirPath)
    logAlert('pluginDirPath: {}'.format(pluginDirPath))
    
    if pluginDirPath is not None:
      logAlert("On MacOS, prepending plugin path: {}".format(pluginDirPath))
      QCoreApplication.addLibraryPath(pluginDirPath)
      
      # assert QApplication.libraryPath() contains pluginDirPath

  
  @classmethod
  def _appDirPath(cls):
    '''
    string path to app's dir.
    
    This wraps Qt method of same name, but succeeds even if not exist a QApplication instance.
    
    Credit K.Knowles see http://qt-project.org/forums/viewthread/20672
    '''
    # temp instance because applicationDirPath requires it and sys.argv
    _ = QCoreApplication(sys.argv)
    result = QCoreApplication.applicationDirPath()
    logAlert('appDirPath: {}'.format(result))
    # !!! temp instance of QCA will now be garbage collected.
    # We don't want it to hang around, so QApplication.instance() won't find it.
    return result
    
    
  @classmethod
  def _appBundlePluginsPath(cls, appDirPath):
    '''
    path to plugin directory of OSX app's bundle 
    (especially when sandboxed, i.e. in a cls-contained bundle w/o shared libraries)
    If not (platform is OSX and app has PlugIns dir in the bundle), returns None.
    
    On other platforms (or when OSX app is not sandboxed)
    plugins are not usually bundled, but in the shared install directory of the Qt package.
    
    Implementation: use Qt since it understands colons (e.g. ':/') for resource paths.
    (Instead of Python os.path, which is problematic.)
    Convert string to QDir, move it around, convert back to string of abs path without colons.
    '''
    # appDirPath typically "/Users/<user>/Library/<appName>.app/Contents/MacOS" on OSX.
    appDir = QDir(appDirPath)
    if not appDir.cdUp():
      logAlert("Could not cdUp from appDir")
    # assert like ..../Contents
    if appDir.cd("PlugIns"):  # !!! Capital I
      result = appDir.absolutePath()
      # assert like ..../Contents/PlugIns
    else:
      logAlert("Could not cd to PlugIns")
      result = None
    assert result is None or isinstance(result, str)
    return result
  
  
  @classmethod
  def dump(cls):
    '''
    For debugging fail to load plugins, mainly OSX.
    '''
    logAlert("Qt Library/plugin search paths:")
    for path in QCoreApplication.libraryPaths():
      logAlert("  Path: {}".format(path))



