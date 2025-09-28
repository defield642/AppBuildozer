[app]

# App details
title = TiM@$k
package.name = timmyalarmpro
package.domain = com.timmy.alarm
source.dir = .
source.include_exts = py,png,jpg,kv,atlas,wav,mp3,json,java
version = 2.0
services = Timmytimetable:service.py

# Dependencies
# Using local patched pyjnius recipe
requirements = python3==3.10.12, kivy, kivymd==1.1.1, plyer, pyjnius, cython==0.29.36

# Orientation / fullscreen
orientation = portrait
fullscreen = 0

# Permissions
android.permissions = android.permission.INTERNET,android.permission.WAKE_LOCK,android.permission.VIBRATE,android.permission.RECEIVE_BOOT_COMPLETED,android.permission.FOREGROUND_SERVICE,android.permission.POST_NOTIFICATIONS,android.permission.SCHEDULE_EXACT_ALARM,android.permission.USE_EXACT_ALARM,android.permission.READ_EXTERNAL_STORAGE,android.permission.WRITE_EXTERNAL_STORAGE

# Java sources directory
android.add_src = android/src

# Extra manifest xml
android.extra_manifest_application_arguments = %(source.dir)s/android/extra_manifest_application_arguments.xml

# Icon and splash
icon.filename = %(source.dir)s/icon.png
presplash.filename = %(source.dir)s/presplash.png
android.adaptive_icon.foreground = %(source.dir)s/adaptive_icon_fg.png
android.adaptive_icon.background = %(source.dir)s/adaptive_icon_bg.png

# Android API / min / ndk
android.api = 33
android.minapi = 21
android.ndk = 25b
android.ndk_api = 21


# CPU architectures
android.archs = arm64-v8a, armeabi-v7a

# Gradle dependencies
android.gradle_dependencies = \
    androidx.core:core:1.9.0, \
    androidx.work:work-runtime:2.8.1, \
    androidx.appcompat:appcompat:1.6.1
android.enable_androidx = True

# Other settings
android.allow_backup = False
android.presplash_color = #FFFFFF
android.window_style = normal

[buildozer]
log_level = 2
warn_on_root = 1
build_dir = .buildozer
bin_dir = bin
android.accept_sdk_license = True

[p4a]
# Point to local patched pyjnius recipe
local_recipes = ./p4a_recipes
p4a.bootstrap = sdl2
p4a.branch = develop
python_version = 3.10

