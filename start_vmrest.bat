@echo off
title remove_ip_bat_script
%1 mshta vbscript:CreateObject("Shell.Application").ShellExecute("cmd.exe","/c %~s0 ::","","runas",1)(window.close)&&exit
chcp 65001 > nul

start "" "C:\Program Files (x86)\VMware\VMware Workstation\vmrest.exe"