# aptstore-core
core component which takes care about installation and removal of packages according to used source. Action will be triggered with xdg-open and reports states into logs

```
usage: aptstore-core [-h] [-i IDENT] [-l LOGIN] [-s SECRET] [-g] platform action

Install/Remove apps from different sources.

positional arguments:
  platform              Allowed values are "debian", "steam", "proton".
  action                Allowed values are "install", "remove", "activate".

optional arguments:
  -h, --help            show this help message and exit
  -i IDENT, --ident IDENT
                        Identifier for an related app-identification depending on platform.
  -l LOGIN, --login LOGIN
                        Optional login (depends on platform)
  -s SECRET, --secret SECRET
                        Optional password (depends on platform)
  -g, --gui             Optional flag that indicates GUI-Mode
```

# Requirements

Needed system packages:
- python3-pip 
- python3-tk

Needed pip packages:
- setuptools~=45.2.0
- requests~=2.22.0
- pexpect~=4.8

# examples

**Install** debian package _gnome-clocks_
```
sudo aptstore-core debian install --ident=gnome-clocks
```

**Remove** debian package _gnome-clocks_
```
sudo aptstore-core debian install --ident=gnome-clocks
```

**Activate** platform _steam_ (Mandatory before use steam platform)
```
sudo aptstore-core steam activate
```

**Install** _Catan Universe_ via platform **proton**
```
aptstore-core proton install --ident=544730 --login <your_login> --secret=<your_steam_password>
```

**Remove** _Catan Universe_ via platform **proton**
```
aptstore-core proton remove --ident=544730 --login <your_login> --secret=<your_steam_password>
```

**Install** _Shiny The Firefly_ via platform **steam**
```
aptstore-core steam install --ident=277510 --login <your_login> --secret=<your_steam_password>
```

**Remove** _Shiny The Firefly_ via platform **steam**
```
aptstore-core steam remove --ident=277510 --login <your_login> --secret=<your_steam_password>
```
