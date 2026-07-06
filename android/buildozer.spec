[app]
title = CGPSC Mains Tracker
package.name = cgpscmainstracker
package.domain = com.manish.cgpsc
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,db,toml
version = 1.0.0
requirements = python3,kivy,android,pyjnius,pandas,numpy,plotly,streamlit,tornado,watchdog,click,blinker,protobuf,pyarrow
orientation = portrait
fullscreen = 0
android.permissions = INTERNET,WRITE_EXTERNAL_STORAGE,READ_EXTERNAL_STORAGE
android.api = 31
android.minapi = 24
android.ndk = 25b
android.accept_sdk_license = True
android.archs = arm64-v8a, armeabi-v7a
android.enable_androidx = True
android.gradle_dependencies = androidx.webkit:webkit:1.4.0
p4a.branch = develop
p4a.extra_args = --private ${source.dir}/.. --package ${package.domain}.${package.name} --name "${title}" --version ${version} --bootstrap=sdl2 --requirements=${requirements}

[buildozer]
log_level = 2
warn_on_root = 1