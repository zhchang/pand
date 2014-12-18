pand
====

Linux could be the best platform to develop Android APP, since it is compatible with most Android phones, you don't have to fight for drivers when debugging.

I myself is a heavy user of VIM, I feel Eclipse ADT and Android Studio did a lot of things right, but also slow me down in many ways.  I wonder is it possible to develop Android APP using VIM + CLI tools only, hence this project. If you are a heavy VIM user like me and you are developing Android APP, trust me, this tool will make your life much more easier.

DOES NOT WORK WITH MICROSOFT WINDOWS
====================================

a CLI tool for compile, build, debug, run, showing adb logs for Android Projects

Unique Features:

    1. Auto run android update project to setup CLI environment
    2. Auto generate compile ant target in custom_rules.xml
    3. Guided configuration steps included (when first run or when config files are missing)
    4. Support guided new project creation
    5. Support setup android environment from scratch

simply issue command:

    pand cmds

where cmds is comma or space separated values, env,new,compile,build,clean,adb,run,debug

Examples:

    pand env //guided android env setup
    pand new //create a new project with guided configurations
    pand // scan modification and incrementally compiles current project
    pand compile
    pand clean //cleans current project
    pand build //scan modification and incrementally builds apk
    pand run //run last built apk and show adb output for the android process
    pand debug //build,run and forward debug port to and connect to jdb
    pand adb //get log for last debuggable process
    pand clean,compile //do a fresh compile
    pand config //guided configuration
    pand clean compile build run adb //fresh build and run

first time running, there will be a guided setup.

Have Fun!

NOTE:

1. sdk path config is stored in ~/.pand (delete to reconfigure) 
2. project/source config is stored in PWD/.pand (delete to reconfigure)
