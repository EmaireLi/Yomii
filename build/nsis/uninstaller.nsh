; 自定义卸载脚本 - electron-builder 会包含此文件
; 注入到 NSIS 卸载段中

!macro customInstall
!macroend

!macro customUnInstall
  SetShellVarContext current
  RMDir /r /REBOOTOK "$LOCALAPPDATA\yomii-updater"
  RMDir /r /REBOOTOK "$LOCALAPPDATA\Yomii"
!macroend
