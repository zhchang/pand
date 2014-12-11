pand
====

a CLI tool for compile, build, debug, run, showing adb logs for Android Projects

simply issue command:

    pand cmds

where cmds is comma separated values, compile,build,clean,adb,run,debug

Examples:

    pand // scan modification and incrementally compiles current project
    pand compile
    pand clean //cleans current project
    pand build //scan modification and incrementally builds apk
    pand run //run last built apk
    pand debug //build,run and forward debug port to and connect to jdb
    pand adb //get log for last debuggable process
    pand clean,compile //do a fresh compile
    pand config //guided configuration

first time running, there will be a guided setup.

Have Fun!

NOTE:

1. sdk path config is stored in ~/.pand (delete to reconfigure) 
2. project/source config is stored in PWD/.pand (delete to reconfigure)
