#!/bin/bash
# Environment setup for Insider Test Automation
# Bu dosya ansible-playbook alias'i icin gerekli

# Insider projesi icin ozel ayarlar
export INSIDER_PROJECT=true
export PROJECT_ROOT="/mnt/c/Users/dtorun/Desktop/insider"

# Ansible icin Python yorumlayici
export ANSIBLE_PYTHON_INTERPRETER=/usr/bin/python3

# Bu dosya sirket projelerinizdeki environment.sh'den farkli
# Sadece bu proje icin gerekli ayarlari icerir

