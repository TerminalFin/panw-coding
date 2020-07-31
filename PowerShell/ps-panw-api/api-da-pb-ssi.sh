#!/bin/zsh
pwsh ps-panw-api.ps1 -DisplayAll $true -PauseBetweenFW $true -Command "show system info" -Batch ".\fw.txt"
