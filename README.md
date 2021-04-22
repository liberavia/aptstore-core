# aptstore-core
core component which takes care about installation and removal of packages according to used source. Action will be triggered with xdg-open and reports states into logs

# examples

**Installing** _Catan Universe_ via platform **proton**
```
aptstore-core proton install 544730 --login <your_login> --secret=<your_steam_password>
```
**Removing** _Catan Universe_ via platform **proton**
```
aptstore-core proton remove 544730 --login <your_login> --secret=<your_steam_password>
```
**Installing** _Shiny The Firefly_ via platform **steam**
```
aptstore-core steam install 277510 --login <your_login> --secret=<your_steam_password>
```
**Removing** _Shiny The Firefly_ via platform **steam**
```
aptstore-core steam remove 277510 --login <your_login> --secret=<your_steam_password>
```


