#!/usr/bin/python
import os,argparse,sys
import xml.etree.ElementTree as ET
from subprocess import call,check_output
import random
import re
from sys import platform as _platform
import util

def get_package_and_activity(folder):
    package = None
    activity = None
    try:
        manifest_path = util.get_os_path(folder,['src','main','AndroidManifest.xml'])
        if os.path.isfile(manifest_path):
            tree = ET.parse(manifest_path)
            package = tree.getroot().attrib['package']
            app = tree.getroot().find('application')
            for act in app.iterfind('activity'):
                for intent in act.iterfind('intent-filter'):
                    for action in intent.iterfind('action'):
                        for key,value in action.attrib.iteritems():
                            if key.endswith('name') and value == 'android.intent.action.MAIN':
                                activity = act.attrib['{http://schemas.android.com/apk/res/android}name']
                                raise Exception('found activity %s'%activity)


    except Exception as e:
        print e
        pass
    return (package,activity)

def get_app_name(folder):
    if not os.path.isabs(folder): 
        folder = util.get_os_path(os.getcwd(),folder)
    if folder.endswith('.'):
        folder = folder[:folder.rfind('/')] 
    if folder.rfind('/') != -1:
        return folder[folder.rfind('/')+1:]
    else:
        return folder

def detect_changes(f,folder):
    if os.path.isfile(f) and os.path.isdir(folder):
        t0 = os.path.getmtime(f)
        for root,dirs,files in os.walk(folder):
            for thing in files:
                name,ext = os.path.splitext(thing)
                if ext.lower() in ['.xml','.java','.aidl']:
                    if os.path.getmtime(util.get_os_path(root,thing))>t0:
                        print 'changes detected: %s'%(thing)
                        return True
                    else:
                        pass
    else:
        return True
    return False

def do_build(project,source,sdk,**args):
    apk_file = util.get_os_path(project,['build','outputs','apk','%s-debug.apk'%(get_app_name(project))])
    build_prop = util.get_os_path(project,['build','build.prop'])
    skip = (not detect_changes(build_prop,source)) and  os.path.isfile(apk_file)
    path = os.getcwd()
    toraise = None
    try:
        os.chdir(project)
        if not skip:
            if os.path.isfile(apk_file):
                try:
                    os.remove(apk_file)
                except:
                    pass

            if 'env' in args:
                env = args['env']
                for key,value in env.iteritems():
                    os.environ[key] = value
            with open(os.devnull,'w') as f:
                call(['./gradlew','build','--info'],stdout=f)
        if os.path.isfile(apk_file):
            with open(build_prop,'w') as f:
                f.write('build ok')
            print 'build ok'
        else:
            raise Exception('failed to build apk : %s'%(apk_file))
    finally:
        os.chdir(path)

def get_adb(sdk):
    if sdk is not None:
        adb = util.get_os_path(sdk,['platform-tools','adb'])
    else:
        adb = 'adb'
    return adb

def get_android(sdk):
    if sdk is not None:
        android = util.get_os_path(sdk,['tools','android'])
    else:
        android = 'android'
    return android


def do_run(project,source,sdk,**args):
    apk_file = util.get_os_path(project,["build","outputs","apk","%s-debug.apk"%(get_app_name(project))])
    if not os.path.isfile(apk_file):
        do_build(project,source,**args)
    adb = get_adb(sdk)

    path = os.getcwd()
    try:
        os.chdir(project)
        print 'build ok, installing'
        call(['adb','install','-r',apk_file]) 
        package,activity = get_package_and_activity(project)
        print 'package[%s],activity[%s]'%(package,activity)
        if len(activity.split('.')) == 1:
            activity = '.' + activity
        if package is not None and activity is not None:
            call([adb,'shell','am','start','-n','%s/%s'%(package,activity)])
            grep = check_output([adb,'shell','set `ps|grep %s|grep -v :`;echo $2'%(package)]).strip()
            cmd = '%s logcat|grep %s'%(adb,grep)
            print cmd
            call([cmd],shell=True)
        else:
            print 'failed to determine package and activity'
    finally:
        os.chdir(path)

def do_adb(project,source,sdk,**args):
    adb = get_adb(sdk)
    package,activity = get_package_and_activity(project)
    print 'package[%s],activity[%s]'%(package,activity)
    if package is not None and activity is not None:
        call([adb,'shell','set `ps|grep %s|grep -v :`;echo $2'%(package)])
        grep = check_output([adb,'shell','set `ps|grep %s|grep -v :`;echo $2'%(package)]).strip()
        cmd = '%s logcat|grep %s'%(adb,grep)
        print cmd
        call([cmd],shell=True)
    else:
        print 'failed to determine package and activity'


def do_debug(project,source,sdk,**args):
    adb = get_adb(sdk)
    apk_file = util.get_os_path(project,["build","outputs","apk","%s-debug.apk"%(get_app_name(project))])
    if not os.path.isfile(apk_file):
        do_build(project,source,**args)

    path = os.getcwd()
    try:
        os.chdir(project)
           
        print 'build ok, installing'
        call([adb,'install','-r',apk_file]) 
        package,activity = get_package_and_activity(project)
        print 'package[%s],activity[%s]'%(package,activity)
        if package is not None and activity is not None:
            call([adb,'shell','am','start','-n','%s/%s'%(package,activity)])
            pid = check_output([adb,'shell','set `ps|grep %s|grep -v :`;echo $2'%(package)]).strip()
            print 'forwarding debugg port %s'%(pid)
            print check_output([adb,'forward','tcp:19438','jdwp:%s'%(pid)])
            print 'connecting jdb'
            call(['jdb -attach localhost:19438'],shell=True)

            print 'failed to determine package and activity'
    finally:
        os.chdir(path)

def do_clean(project,source,sdk,**args):
    path = os.getcwd()
    try:
        os.chdir(project)
        if 'env' in args:
            env = args['env']
            for key,value in env.iteritems():
                os.environ[key] = value
        call(['./gradlew','clean'])
    finally:
        os.chdir(path)

def do_remove(project,source,sdk,**args):
    adb = get_adb(sdk)
    try:
        package,activity = get_package_and_activity(project)
        if package is not None:
            print 'alright, let me try uninstall it.'
            call([adb,'uninstall',package])

    except:
        pass

def do_compile(project,source,sdk,**args):
    compile_prop = util.get_os_path(project,['build','compile.prop'])
    skip = not detect_changes(compile_prop,source)
    if skip:
        print 'no changes detected, compile skipped'
        return
    path = os.getcwd()
    try:
        os.chdir(project)
        if 'env' in args:
            env = args['env']
            for key,value in env.iteritems():
                os.environ[key] = value
        with open(os.devnull,'w') as f:
            cs = call(['./gradlew','compileDebugJava','--info'],stdout=f)
            if cs == 0:
                with open(compile_prop,'w') as prop:
                    prop.write('compile succeed')
    finally:
        os.chdir(path)


def check_project(p):
    if not os.path.isabs(p): 
        p = util.get_os_path(os.getcwd(),p)
    if not os.path.isdir(p) or  not os.path.isfile(util.get_os_path(p,['src','main','AndroidManifest.xml'])):
        raise argparse.ArgumentTypeError('invalid project folder')
    return p 

def check_source(p):
    if not os.path.isabs(p): 
        p = util.get_os_path(os.getcwd(),p)
    if not os.path.isdir(p):
        raise argparse.ArgumentTypeError('invalid source folder')
    return p 

def check_sdk(p):
    if not os.path.isabs(p):
        p = util.get_os_path(os.getcwd(),p)
    if not os.path.isdir(p):
        raise Exception('oh man, this is not even a folder...,tell me again:')
    pt = util.get_os_path(p,'platform-tools')
    if not os.path.isdir(pt):
        raise Exception('dude, there is no platform-tools folder in the given path')
    if not os.path.isfile(util.get_os_path(pt,'adb')):
        raise Exception('dude, I need adb to work, did you deleted it?')
    ts = util.get_os_path(p,'tools')
    if not os.path.isdir(ts):
        raise Exception('dude, your sdk seems incomplete. where is the tools folder?')
    if not os.path.isfile(util.get_os_path(ts,'android')):
        raise Exception('dude, seriously, stop deleting sdk files at will.')
    return p
    


def do_idle(project,source,sdk):
    pass

def config_sdk():
    sdk = read_sdk_config()
    if sdk is None:
        print 'so where did you install Android SDK?'
        while True:
            sdk= sys.stdin.readline().strip()
            try:
                sdk= check_sdk(sdk)
                break
            except Exception as e:
                print e
                pass
    home = os.path.expanduser('~')
    with open(util.get_os_path(home,'.pand'),'w') as f:
        f.write('sdk=%s\n'%(sdk))

def do_config(project,source,sdk):
    
    print 'What is your project path?'
    while True:
        project = sys.stdin.readline().strip()
        try:
            project = check_project(project)
            break
        except:
            print 'Dude, this path looks not like a project folder to me. I will give you one more chance to make it right:'
            pass
    print 'Where do you want me to scan for changes?'
    while True:
        source = sys.stdin.readline().strip()
        try:
            source = check_source(source)
            break
        except:
            print 'Man, we need a folder. Tell me again now:'
            pass
    with open('.pand','w') as f:
        f.write('project=%s\n'%(project))
        f.write('source=%s\n'%(source))

def read_sdk_config():
    sdk = None
    home_config = util.get_os_path(os.path.expanduser('~'),'.pand')
    if os.path.isfile(home_config):
        with open(home_config,'r') as f:
            lines = f.readlines()
            for line in lines:
                try:
                    key,value = line.split('=',2)
                    key = key.strip()
                    value = value.strip()
                    if key == 'sdk':
                        sdk = check_sdk(value)
                except:
                    pass
    return sdk


def read_config(config_file):
    p = '.'
    s = '.'
    if os.path.isfile(config_file):
        with open(config_file,'r') as f:
            lines = f.readlines()
            for line in lines:
                try:
                    key,value = line.split('=',2)
                    key = key.strip()
                    value = value.strip()
                    if key == 'project':
                        p = check_project(value)
                    elif key == 'source':
                        s = check_source(value)
                except:
                    pass
    return p,s

def get_input(hint,error,checker):
    print hint
    while True:
        choice = sys.stdin.readline().strip()
        if checker(choice):
            return choice
        else:
            print error


def get_target_input():
    android = get_android(sdk)
    output = check_output([android,'list','target'])
    ids = []
    for line in output.split('\n'):
        line = line.strip()
        if line.startswith("id: "):
            ids.append( line.split('or')[0].strip().split(' ')[1])
            print line
    def checker(choice):
        return choice in ids
    return get_input('come on now, which sdk you wanna use?','Dude, do not make things up! tell me again',checker)




def do_new(sdk):
    path = os.getcwd()
    if len(os.listdir(path)) > 0:
        print 'Darn, this is not an empty folder, are you sure you wanna do it here?[Y/N]'
        if not get_yn_choice():
            print 'Alright, call me again when you are ready.'
            exit(0)
    android = get_android(sdk)
    target = get_target_input()
    print 'target %s'%(target)
    def check_name(name):
        return re.match('^[A-Za-z]*[A-Za-z0-9-_]*$',name) != None

    def check_package(package):
        names = package.split(".")
        for name in names:
            if not check_name(name):
                return False
        return True
    name = get_input('what do you wanna call your project?','shit man, bad name.',check_name)
    activity = get_input('what do you wanna call your activity?','shit man, bad name.',check_name)
    package = get_input('what java package for your source code?','shit man, bad package.',check_package)
    
    call([android,'create','project','--target',target,'--name',name,'--path','.','--activity',activity,'--package',package,'-g','-v','1.0+'])
    exit(0)

def get_yn_choice():
    while True:
        choice = sys.stdin.readline().strip()
        if choice.lower() in ['y','yes','yep','yeah']:
            return True
        elif choice.lower() in ['n','no','nuh','nope']:
            return False
        else:
            print 'Speak English![Y/N]'


def download_file(url):
    error = 'I cannot seem to download %s. You might want to try again later.'%(url)
    path = url[url.rfind('/')+1:]
    if call(['curl',url,'-o',path]) != 0:
        try:
            os.remove(path)
        except:
            pass
        raise Exception(error)



def get_os_keyword():
    keyword = ''
    if _platform == "linux" or _platform == "linux2":
        keyword = 'linux'
    elif _platform == "darwin":
        keyword = 'macosx'
    return keyword



def do_env():
    def checker(path):
        return os.path.isdir(path) 
    dest = get_input('So where should I install sdks?','dude, this is not a good place. Choose somewhere else.',checker)
    if not os.path.isabs(dest): 
        dest = util.get_os_path(os.getcwd(),dest)
    path = os.getcwd()
    try:
        if not os.path.isfile('android-sdk.tgz'):
            has_curl = False
            try:
                check_output(['which','curl'])
                has_curl = True
            except:
                pass
            if not has_curl:
                print 'we need curl to proceed, let me know when you have it.'
                exit(0)

            os.chdir(dest)
            try:
                os.remove('index.html')
            except:
                pass
            download_file('http://developer.android.com/sdk/index.html')
            sdk_url= ''
            keyword = get_os_keyword()
            with open('index.html','r') as f:
                c = f.read()
                result = c.find('"http://dl.google.com/android',0)
                while result != -1:
                    start = result + 1
                    result = c.find('"',start)
                    thing = c[start:result]
                    if thing.find(keyword)!=-1:
                        sdk_url= thing
                        break
                    result = c.find('"http://dl.google.com/android',start)
            print sdk_url
            sdk_zip = sdk_url[sdk_url.rfind('/'):]

            download = util.get_os_path(dest,sdk_zip)
            try:
                os.remove(download)
            except:
                pass
            download_file(sdk_url)
        os.rename(download,'android-sdk.tgz')
        if call(['tar','zxf','android-sdk.tgz'])!=0:
            raise Exception('The file downloaded seems to be corrupted. You might wanna try again later.')
        try:
            os.remove('android-sdk.tgz')
        except:
            pass
        sdk = util.get_os_path(dest,'android-sdk-linux')
        android =get_android(sdk)
        print android
        while not os.path.isdir(util.get_os_path(sdk,'platform-tools')) or len(os.listdir(util.get_os_path(sdk,'platforms'))) == 0:
            print 'it appears I need to download more package, shall I proceed?[Y/N]'
            if get_yn_choice():
                call([android,'update','sdk','-u'])
            else:
                raise Exception('Bye then.')
        home = os.path.expanduser('~')
        with open(util.get_os_path(home,'.pand'),'w') as f:
            f.write('sdk=%s\n'%(sdk))
        try:
            os.remove(download)
        except:
            pass
    except Exception as e:
        print e
    finally:
        os.chdir(path)
    exit(0)
    


if __name__ == '__main__':
    if len(get_os_keyword())==0:
        print 'I support only linux or OSX'
    cmds = []
    if len(sys.argv) == 1:
            cmds = ['compile']
    else:
        cmds = []
        for arg in sys.argv[1:]:
            cmds += arg.lower().split(',')

    if 'help' in cmds:
        util.print_help(globals())
        exit(0)

    if 'env' in cmds:
        cmds.remove('env')
        do_env()


    sdk = read_sdk_config()
    if sdk is not None:
        config_sdk()

    if 'new' in cmds:
        cmds.remove('new')
        do_new(sdk)
    should_config = False
    if 'config' in cmds:
        cmds.remove('config')
        should_config = True


    config_file = util.get_os_path(os.getcwd(),'.pand')
    if not should_config and not os.path.isfile(config_file):
        print 'Howdy Dude, tell me something before we can start,ready?'
        print '[Y/N]'
        if get_yn_choice():
            should_config= True

    if should_config:
        do_config(None,None,None)

    try:
        project,source = read_config(config_file) 

        project = check_project(project)
        source = check_source(source)

        for cmd in cmds:
            if 'do_%s'%(cmd) not in globals():
                trash_talks = ['what the heck is %s?','Man! I know not what %s is','Seriously, what do you mean by %s?']
                random.seed()
                raise Exception(trash_talks[random.randrange(len(trash_talks))]%(cmd))
        
        for cmd in cmds:
            globals()['do_%s'%(cmd)](project,source,sdk)
    except Exception as e:
        if not os.path.isfile(config_file):
            print e
            print 'We better config before proceed. Bye~ Take Care!'
        else:
            print e
            exit(1)    
    
