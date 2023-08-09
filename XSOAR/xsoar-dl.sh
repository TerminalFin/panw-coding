#!/bin/bash
# Cortex XSOAR Downloader Script
# By Josh Levine, Palo Alto Networks Federal Solutions Architect
# Necessary tools: wget
                
clear
options=("Default Installer" "Signed Installer" "Signed Installer Public Key File" "FIPS Default Installer" "FIPS Signed Installer" "FIPS Installer Public Key File"
"Elastic Migration Tool" "Offline Docker Tarball" "Exit Script")

base_url="https://download.demisto.com/download-params?token="

echo "Palo Alto Network Cortex XSOAR Installer Download Script"
echo "\nDownload link will be provided either after purchase or in the Community Edition request"
echo "\nDownload link format is: https://download.demisto.works/download-params?token=<TOKEN>&email=<REGISTERED_EMAIL_ADDRESS>"
echo -e "------\\n\\n"
read -p "Enter download token: " token
read -p "Enter email address associated with token: " email

url=$base_url$token\&email="$email"\&eula=accept

while true; do
    url=$base_url$token\&email="$email"\&eula=accept
    clear

    select opt in "${options[@]}"; do   
        case $opt in
            "Default Installer")
                echo "Donwloading latest unsigned Cortex XSOAR installer to current working directory"
                echo "Remote url: $url"
                wget --show-progress --content-disposition $url
                read -n 1 -s -r -p "Press any key to continue"
                break ;;
            "Signed Installer")                                      
                echo "Donwloading latest signed Cortex XSOAR installer to current working directory"
                url+=\&downloadName=signed
                echo "Remote url: $url"
                wget --show-progress --content-disposition $url
                read -n 1 -s -r -p "Press any key to continue"
                break ;;
            "Signed Installer Public Key File")
                echo "Donwloading latest signed Cortex XSOAR installer public key file to current working directory"
                url+=\&downloadName=signed_public_key
                echo "Remote url: $url"
                wget --show-progress --content-disposition $url
                read -n 1 -s -r -p "Press any key to continue"
                break ;;
            "FIPS Default Installer")
                echo "Donwloading latest unsigned FIPS Cortex XSOAR installer to current working directory"
                url+=\&downloadName=fips
                echo "Remote url: $url"
                wget --show-progress --content-disposition $url
                read -n 1 -s -r -p "Press any key to continue"
                break ;;
            "FIPS Signed Installer")
                echo "Donwloading latest signed FIPS Cortex XSOAR installer to current working directory"
                url+=\&downloadName=fips_signed
                echo "Remote url: $url"
                wget --show-progress --content-disposition $url
                read -n 1 -s -r -p "Press any key to continue"
                break ;;
            "FIPS Installer Public Key File")
                echo "Donwloading latest signed FIPS Cortex XSOAR installer public key to current working directory"
                url+=\&downloadName=fips_signed_public_key
                echo "Remote url: $url"
                wget --show-progress --content-disposition $url
                read -n 1 -s -r -p "Press any key to continue"
                break ;;
            "Elastic Migration Tool")        
                echo "Donwloading latest Cortex XSOAR Elastic Migration Tool to current working directory"
                url+=\&downloadName=elasticsearch_migration_tool
                echo "Remote url: $url"
                wget --show-progress --content-disposition $url
                read -n 1 -s -r -p "Press any key to continue"
                break ;;
            "Offline Docker Tarball")
                echo "Donwloading latest XSOAR Docker Image Offline Tarball to current working directory"
                url+=\&downloadName=dockerimages
                echo "Remote url: $url"
                wget --show-progress --content-disposition $url
                read -n 1 -s -r -p "Press any key to continue"
                break ;;
            "Exit Script")
                echo "done..."
                exit
                ;;
            * )
            echo "Invalid option"
        esac
    done
done

